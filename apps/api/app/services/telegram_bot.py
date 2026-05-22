import logging
from typing import Any

import httpx
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.models.family import FamilyRole
from app.models.family_invite import FamilyInvite
from app.models.user import User
from app.services import bot_session as bot_session_service
from app.services import family as family_service
from app.services import family_invites as invite_service
from app.services.family_invites import (
    bind_link_invite_to_user,
    build_invite_deep_link,
    build_share_url,
    inviter_display_name,
    is_link_invite,
)
from app.services.users import (
    get_user_by_telegram_id,
    mask_phone,
    normalize_phone,
    upsert_user_from_bot,
    user_has_verified_phone,
)

logger = logging.getLogger(__name__)

BOT_COMMANDS_HELP = """ПланАм — команды:

/help — справка
/invite +79001234567 — пригласить по номеру (админ семьи)
Пригласить в семью — ссылка-приглашение

Откройте приложение кнопкой ниже."""

PHONE_REQUIRED_TEXT = (
    "Для работы ПланАм нужен номер телефона.\n\n"
    "Нажмите «Поделиться моим номером» — после этого откроется Mini App "
    "и станут доступны команды бота."
)

INVITE_FAMILY_TEXT = (
    "Telegram не позволяет боту открыть список ваших контактов. "
    "Отправьте ссылку приглашения человеку, которого хотите добавить.\n\n"
    "Или введите номер: /invite +79001234567"
)

OTHER_PERSON_CONTACT_TEXT = (
    "Для приглашения другого человека используйте ссылку-приглашение "
    "или введите номер вручную: /invite +79001234567"
)

CREATE_INVITE_LINK_CALLBACK = "create_family_invite_link"


def _api_url(method: str) -> str:
    return f"https://api.telegram.org/bot{settings.telegram_bot_token}/{method}"


async def send_telegram_message(
    chat_id: int,
    text: str,
    *,
    reply_markup: dict[str, Any] | None = None,
) -> None:
    if not settings.telegram_bot_token:
        logger.warning("TELEGRAM_BOT_TOKEN not set, skip sendMessage")
        return

    payload: dict[str, Any] = {"chat_id": chat_id, "text": text}
    if reply_markup:
        payload["reply_markup"] = reply_markup

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(_api_url("sendMessage"), json=payload)
        data = response.json()
    if not data.get("ok"):
        logger.warning("sendMessage failed chat_id=%s: %s", chat_id, data)


async def answer_callback_query(callback_query_id: str, text: str = "") -> None:
    if not settings.telegram_bot_token:
        return
    payload: dict[str, Any] = {"callback_query_id": callback_query_id}
    if text:
        payload["text"] = text
    async with httpx.AsyncClient(timeout=15.0) as client:
        await client.post(_api_url("answerCallbackQuery"), json=payload)


def _own_phone_keyboard() -> dict[str, Any]:
    return {
        "keyboard": [[{"text": "Поделиться моим номером", "request_contact": True}]],
        "resize_keyboard": True,
        "one_time_keyboard": True,
    }


def _webapp_inline_keyboard() -> dict[str, Any]:
    url = settings.telegram_webapp_url or "https://planam.ru"
    return {
        "inline_keyboard": [
            [{"text": "Открыть ПланАм", "web_app": {"url": url}}],
        ],
    }


def _invite_family_inline_keyboard() -> dict[str, Any]:
    return {
        "inline_keyboard": [
            [
                {
                    "text": "Создать ссылку-приглашение",
                    "callback_data": CREATE_INVITE_LINK_CALLBACK,
                },
            ],
            [{"text": "Открыть ПланАм", "web_app": {"url": settings.telegram_webapp_url or "https://planam.ru"}}],
        ],
    }


def _invite_action_keyboard(invite_id: int) -> dict[str, Any]:
    return {
        "inline_keyboard": [
            [
                {
                    "text": "Принять",
                    "callback_data": f"accept_family_invite:{invite_id}",
                },
                {
                    "text": "Отклонить",
                    "callback_data": f"decline_family_invite:{invite_id}",
                },
            ],
        ],
    }


def _telegram_share_keyboard(invite_token: str) -> dict[str, Any]:
    return {
        "inline_keyboard": [
            [
                {
                    "text": "Отправить приглашение в Telegram",
                    "url": build_share_url(invite_token),
                },
            ],
        ],
    }


def _remove_keyboard() -> dict[str, Any]:
    return {"remove_keyboard": True}


def _parse_start_payload(text: str) -> str | None:
    parts = text.strip().split(maxsplit=1)
    if len(parts) < 2:
        return None
    payload = parts[1].strip()
    if payload.startswith("invite_"):
        return payload[7:]
    return None


def _is_invite_flow_start(text: str) -> bool:
    parts = text.strip().split(maxsplit=1)
    if len(parts) < 2:
        return False
    return parts[1].strip() == "invite"


def _is_own_contact(from_user: dict[str, Any], contact: dict[str, Any]) -> bool:
    contact_user_id = contact.get("user_id")
    if contact_user_id is None:
        return False
    return contact_user_id == from_user.get("id")


async def send_phone_required(chat_id: int, *, invite_token: str | None = None) -> None:
    await send_telegram_message(
        chat_id,
        PHONE_REQUIRED_TEXT,
        reply_markup=_own_phone_keyboard(),
    )


async def notify_invitee_about_invite(
    db: Session, invite_id: int, chat_id: int | None = None
) -> bool:
    invite = invite_service.get_invite_by_id(db, invite_id)
    if invite is None or not invite.invited_user_id:
        return False
    invited = db.get(User, invite.invited_user_id)
    if not invited or not invited.telegram_id:
        return False
    target = chat_id or invited.telegram_id
    inviter_name = inviter_display_name(invite.invited_by)
    family_name = invite.family.name if invite.family else "семья"
    await send_telegram_message(
        target,
        f"{inviter_name} приглашает вас в семью «{family_name}» в ПланАм.",
        reply_markup=_invite_action_keyboard(invite.id),
    )
    return True


async def send_pending_invites_to_user(db: Session, user: User, chat_id: int) -> None:
    invites = invite_service.link_pending_invites_to_user(db, user)
    for invite in invites:
        if is_link_invite(invite):
            continue
        family_name = invite.family.name if invite.family else "семья"
        inviter_name = inviter_display_name(invite.invited_by)
        await send_telegram_message(
            chat_id,
            f"{inviter_name} приглашает вас в семью «{family_name}» в ПланАм.",
            reply_markup=_invite_action_keyboard(invite.id),
        )


async def show_invite_mismatch(chat_id: int) -> None:
    await send_telegram_message(
        chat_id,
        "Этот номер не совпадает с номером приглашения. "
        "Попросите отправить приглашение на ваш номер.",
    )


async def _show_invite_prompt(
    db: Session, user: User, chat_id: int, invite: FamilyInvite
) -> None:
    family_name = invite.family.name if invite.family else "семья"
    inviter_name = inviter_display_name(invite.invited_by)
    await send_telegram_message(
        chat_id,
        f"Вас пригласили в семью «{family_name}» ({inviter_name}).",
        reply_markup=_invite_action_keyboard(invite.id),
    )


async def process_deep_link_invite(
    db: Session, user: User, chat_id: int, invite_token: str
) -> None:
    invite = invite_service.get_invite_by_token(db, invite_token)
    if invite is None or invite.status != "pending":
        await send_telegram_message(chat_id, "Приглашение не найдено или уже обработано.")
        return

    if not user_has_verified_phone(user):
        bot_session_service.set_session_state(
            db, user.telegram_id, "", invite_token=invite_token
        )
        await send_phone_required(chat_id)
        return

    if is_link_invite(invite):
        try:
            invite = bind_link_invite_to_user(db, invite, user)
        except HTTPException as exc:
            detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
            await send_telegram_message(chat_id, detail)
            return
        await _show_invite_prompt(db, user, chat_id, invite)
        return

    if not invite_service.user_matches_invite(user, invite):
        await show_invite_mismatch(chat_id)
        return

    await _show_invite_prompt(db, user, chat_id, invite)


async def send_verified_welcome(
    db: Session, user: User, chat_id: int, *, returning: bool = False
) -> None:
    intro = "С возвращением в ПланАм!" if returning else "Готово! Номер подтверждён."
    await send_telegram_message(
        chat_id,
        f"{intro}\n\n{BOT_COMMANDS_HELP}",
        reply_markup=_remove_keyboard(),
    )
    await send_pending_invites_to_user(db, user, chat_id)

    session = bot_session_service.get_session(db, user.telegram_id)
    if session and session.invite_token:
        await process_deep_link_invite(db, user, chat_id, session.invite_token)
        bot_session_service.clear_session_state(db, user.telegram_id)
        return

    await send_telegram_message(
        chat_id,
        "Откройте приложение:",
        reply_markup=_webapp_inline_keyboard(),
    )


async def handle_start(
    db: Session, chat_id: int, from_user: dict[str, Any], text: str
) -> None:
    logger.info("/start user_id=%s", from_user.get("id"))
    user, _ = upsert_user_from_bot(
        db,
        telegram_id=from_user["id"],
        username=from_user.get("username"),
        first_name=from_user.get("first_name"),
        last_name=from_user.get("last_name"),
        language_code=from_user.get("language_code"),
    )

    if _is_invite_flow_start(text):
        await handle_invite_family_button(db, chat_id, from_user)
        return

    invite_token = _parse_start_payload(text)
    if invite_token:
        logger.info("Deep-link invite token=%s…", invite_token[:8])
        bot_session_service.set_session_state(
            db, user.telegram_id, "", invite_token=invite_token
        )
        if user_has_verified_phone(user):
            await process_deep_link_invite(db, user, chat_id, invite_token)
            bot_session_service.clear_invite_token(db, user.telegram_id)
            return
        await send_phone_required(chat_id)
        return

    if user_has_verified_phone(user):
        await send_verified_welcome(db, user, chat_id, returning=True)
        return

    await send_phone_required(chat_id)


async def handle_own_contact(
    db: Session, chat_id: int, from_user: dict[str, Any], contact: dict[str, Any]
) -> None:
    phone = contact.get("phone_number")
    if not phone:
        await send_telegram_message(
            chat_id,
            "Не удалось прочитать номер. Попробуйте ещё раз.",
            reply_markup=_own_phone_keyboard(),
        )
        return

    logger.info("Phone verified telegram_id=%s phone=%s", from_user.get("id"), mask_phone(phone))
    user, _ = upsert_user_from_bot(
        db,
        telegram_id=from_user["id"],
        username=from_user.get("username"),
        first_name=from_user.get("first_name"),
        last_name=from_user.get("last_name"),
        language_code=from_user.get("language_code"),
        phone_number=phone,
    )

    session = bot_session_service.get_session(db, user.telegram_id)
    pending_token = session.invite_token if session else None

    if pending_token:
        invite = invite_service.get_invite_by_token(db, pending_token)
        if invite and invite.status == "pending":
            if is_link_invite(invite):
                try:
                    bind_link_invite_to_user(db, invite, user)
                except HTTPException as exc:
                    detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
                    bot_session_service.clear_session_state(db, user.telegram_id)
                    await send_telegram_message(chat_id, detail)
                    return
            elif normalize_phone(phone) != invite.invited_phone_normalized:
                bot_session_service.clear_session_state(db, user.telegram_id)
                await show_invite_mismatch(chat_id)
                return

    await send_verified_welcome(db, user, chat_id, returning=False)
    bot_session_service.clear_session_state(db, user.telegram_id)


async def handle_contact(
    db: Session, chat_id: int, from_user: dict[str, Any], contact: dict[str, Any]
) -> None:
    if not _is_own_contact(from_user, contact):
        await send_telegram_message(
            chat_id,
            OTHER_PERSON_CONTACT_TEXT,
            reply_markup=_invite_family_inline_keyboard(),
        )
        return
    await handle_own_contact(db, chat_id, from_user, contact)


async def handle_create_invite_link(
    db: Session, chat_id: int, from_user: dict[str, Any]
) -> None:
    user = get_user_by_telegram_id(db, from_user["id"])
    if not user_has_verified_phone(user):
        await send_phone_required(chat_id)
        return

    membership = family_service.get_user_membership(db, user)  # type: ignore[arg-type]
    if membership is None:
        await send_telegram_message(
            chat_id,
            "Сначала создайте семью в приложении (раздел «Семья»).",
        )
        return

    if membership.role != FamilyRole.ADMIN.value:
        await send_telegram_message(chat_id, "Приглашать может только администратор семьи.")
        return

    try:
        result = invite_service.create_link_invite(
            db,
            user,  # type: ignore[arg-type]
            membership.family_id,
        )
    except HTTPException as exc:
        detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
        await send_telegram_message(chat_id, detail)
        return

    invite = result.invite
    await send_telegram_message(
        chat_id,
        f"Ссылка-приглашение в семью «{result.family_name}» готова.\n\n"
        f"{build_invite_deep_link(invite.invite_token)}",
        reply_markup=_telegram_share_keyboard(invite.invite_token),
    )


async def handle_invite_family_button(db: Session, chat_id: int, from_user: dict[str, Any]) -> None:
    user = get_user_by_telegram_id(db, from_user["id"])
    if not user_has_verified_phone(user):
        await send_phone_required(chat_id)
        return

    membership = family_service.get_user_membership(db, user)  # type: ignore[arg-type]
    if membership is None:
        await send_telegram_message(
            chat_id,
            "Сначала создайте семью в приложении (раздел «Семья»).",
        )
        return

    if membership.role != FamilyRole.ADMIN.value:
        await send_telegram_message(chat_id, "Приглашать может только администратор семьи.")
        return

    await send_telegram_message(
        chat_id,
        INVITE_FAMILY_TEXT,
        reply_markup=_invite_family_inline_keyboard(),
    )


async def handle_invite_command(
    db: Session, chat_id: int, from_user: dict[str, Any], text: str
) -> None:
    parts = text.split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip():
        await send_telegram_message(
            chat_id,
            "Формат: /invite +79001234567",
        )
        return

    user = get_user_by_telegram_id(db, from_user["id"])
    if not user_has_verified_phone(user):
        await send_phone_required(chat_id)
        return

    membership = family_service.get_user_membership(db, user)  # type: ignore[arg-type]
    if membership is None:
        await send_telegram_message(chat_id, "Сначала создайте семью в приложении.")
        return

    if membership.role != FamilyRole.ADMIN.value:
        await send_telegram_message(chat_id, "Приглашать может только администратор семьи.")
        return

    try:
        result = invite_service.create_invite(
            db,
            user,  # type: ignore[arg-type]
            membership.family_id,
            parts[1].strip(),
        )
    except HTTPException as exc:
        detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
        await send_telegram_message(chat_id, detail)
        return

    invite = result.invite
    if result.invitee_notified:
        await notify_invitee_about_invite(db, invite.id)
        await send_telegram_message(
            chat_id,
            f"Приглашение отправлено ({mask_phone(parts[1])}).",
        )
    else:
        await send_telegram_message(
            chat_id,
            "Приглашение создано. Отправьте ссылку человеку, который ещё не запускал бота:",
            reply_markup=_telegram_share_keyboard(invite.invite_token),
        )


async def handle_callback(db: Session, callback: dict[str, Any]) -> None:
    callback_id = callback.get("id")
    data = callback.get("data") or ""
    from_user = callback.get("from") or {}
    telegram_id = from_user.get("id")
    message = callback.get("message") or {}
    chat_id = (message.get("chat") or {}).get("id") or from_user.get("id")

    if not telegram_id or not chat_id:
        return

    if data == CREATE_INVITE_LINK_CALLBACK:
        await handle_create_invite_link(db, chat_id, from_user)
        if callback_id:
            await answer_callback_query(callback_id, "Ссылка создана")
        return

    user = get_user_by_telegram_id(db, telegram_id)
    if not user_has_verified_phone(user):
        if callback_id:
            await answer_callback_query(callback_id, "Сначала подтвердите номер: /start")
        return

    if data.startswith("accept_family_invite:"):
        invite_id = int(data.split(":", 1)[1])
        logger.info("Accept invite id=%s user_id=%s", invite_id, user.id)
        try:
            invite = invite_service.get_invite_by_id(db, invite_id)
            if invite and is_link_invite(invite) and user_has_verified_phone(user):
                invite = bind_link_invite_to_user(db, invite, user)  # type: ignore[arg-type]
            member = invite_service.accept_invite(db, user, invite_id)  # type: ignore[arg-type]
            invite = invite_service.get_invite_by_id(db, invite_id)
            if invite and invite.invited_by and invite.invited_by.telegram_id:
                name = member.display_name
                await send_telegram_message(
                    invite.invited_by.telegram_id,
                    f"{name} присоединился к семье.",
                )
            await send_telegram_message(chat_id, "Вы присоединились к семье.")
            if callback_id:
                await answer_callback_query(callback_id, "Принято")
        except HTTPException as exc:
            detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
            await send_telegram_message(chat_id, detail)
            if callback_id:
                await answer_callback_query(callback_id, detail[:200])
        return

    if data.startswith("decline_family_invite:"):
        invite_id = int(data.split(":", 1)[1])
        logger.info("Decline invite id=%s user_id=%s", invite_id, user.id)
        try:
            invite_service.decline_invite(db, user, invite_id)  # type: ignore[arg-type]
            await send_telegram_message(chat_id, "Приглашение отклонено.")
            if callback_id:
                await answer_callback_query(callback_id, "Отклонено")
        except HTTPException as exc:
            detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
            await send_telegram_message(chat_id, detail)
            if callback_id:
                await answer_callback_query(callback_id, detail[:200])


async def process_telegram_update(db: Session, update: dict[str, Any]) -> None:
    logger.info("Telegram update keys=%s", list(update.keys()))

    callback = update.get("callback_query")
    if callback:
        await handle_callback(db, callback)
        return

    message = update.get("message")
    if not message:
        return

    chat = message.get("chat") or {}
    chat_id = chat.get("id")
    from_user = message.get("from")
    if not chat_id or not from_user:
        return

    if message.get("contact"):
        await handle_contact(db, chat_id, from_user, message["contact"])
        return

    text = (message.get("text") or "").strip()

    if text == "Пригласить в семью":
        await handle_invite_family_button(db, chat_id, from_user)
        return

    if text.startswith("/start"):
        await handle_start(db, chat_id, from_user, text)
        return

    user = get_user_by_telegram_id(db, from_user["id"])
    if user is None:
        upsert_user_from_bot(
            db,
            telegram_id=from_user["id"],
            username=from_user.get("username"),
            first_name=from_user.get("first_name"),
            last_name=from_user.get("last_name"),
            language_code=from_user.get("language_code"),
        )
        user = get_user_by_telegram_id(db, from_user["id"])

    if not user_has_verified_phone(user):
        await send_phone_required(chat_id)
        return

    command = text.split()[0].split("@")[0].lower() if text else ""

    if command in ("/help",):
        await send_telegram_message(chat_id, BOT_COMMANDS_HELP)
        await send_telegram_message(
            chat_id,
            "Откройте приложение:",
            reply_markup=_webapp_inline_keyboard(),
        )
        return

    if command in ("/invite",):
        await handle_invite_command(db, chat_id, from_user, text)
        return

    await send_telegram_message(
        chat_id,
        "Команды: /help, /invite +номер, «Пригласить в семью»",
        reply_markup=_webapp_inline_keyboard(),
    )
