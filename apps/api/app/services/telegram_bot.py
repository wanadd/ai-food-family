import logging
from typing import Any

import httpx
from sqlalchemy.orm import Session

from app.config import settings
from app.models.family import FamilyRole
from app.models.user import User
from app.schemas.family import FamilyInviteByPhoneRequest
from app.services import family as family_service
from app.services.users import (
    get_user_by_telegram_id,
    upsert_user_from_bot,
    user_has_verified_phone,
)
from fastapi import HTTPException

logger = logging.getLogger(__name__)

BOT_COMMANDS_HELP = """ПланАм — команды бота:

/help — эта справка
/invite +79001234567 — пригласить в семью по номеру (только админ семьи)

Откройте приложение кнопкой ниже."""

PHONE_REQUIRED_TEXT = (
    "Для работы ПланАм нужен номер телефона.\n\n"
    "Нажмите «Поделиться номером» — после этого откроется Mini App "
    "и станут доступны команды бота."
)


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
        logger.warning("sendMessage failed: %s", data)


def _contact_keyboard() -> dict[str, Any]:
    return {
        "keyboard": [[{"text": "Поделиться номером", "request_contact": True}]],
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


def _remove_keyboard() -> dict[str, Any]:
    return {"remove_keyboard": True}


async def send_phone_required(chat_id: int) -> None:
    await send_telegram_message(
        chat_id,
        PHONE_REQUIRED_TEXT,
        reply_markup=_contact_keyboard(),
    )


async def send_verified_welcome(chat_id: int, *, returning: bool = False) -> None:
    intro = (
        "С возвращением в ПланАм!"
        if returning
        else "Готово! Номер подтверждён."
    )
    await send_telegram_message(
        chat_id,
        f"{intro}\n\n{BOT_COMMANDS_HELP}",
        reply_markup=_remove_keyboard(),
    )
    await send_telegram_message(
        chat_id,
        "Откройте приложение:",
        reply_markup=_webapp_inline_keyboard(),
    )


async def handle_start(db: Session, chat_id: int, from_user: dict[str, Any]) -> None:
    user, _ = upsert_user_from_bot(
        db,
        telegram_id=from_user["id"],
        username=from_user.get("username"),
        first_name=from_user.get("first_name"),
        last_name=from_user.get("last_name"),
        language_code=from_user.get("language_code"),
    )

    if user_has_verified_phone(user):
        await send_verified_welcome(chat_id, returning=True)
        return

    await send_phone_required(chat_id)


async def handle_contact(
    db: Session, chat_id: int, from_user: dict[str, Any], contact: dict[str, Any]
) -> None:
    if contact.get("user_id") != from_user.get("id"):
        await send_telegram_message(
            chat_id,
            "Пожалуйста, отправьте свой номер через кнопку «Поделиться номером».",
            reply_markup=_contact_keyboard(),
        )
        return

    phone = contact.get("phone_number")
    if not phone:
        await send_telegram_message(
            chat_id,
            "Не удалось прочитать номер. Попробуйте ещё раз.",
            reply_markup=_contact_keyboard(),
        )
        return

    upsert_user_from_bot(
        db,
        telegram_id=from_user["id"],
        username=from_user.get("username"),
        first_name=from_user.get("first_name"),
        last_name=from_user.get("last_name"),
        language_code=from_user.get("language_code"),
        phone_number=phone,
    )

    await send_verified_welcome(chat_id, returning=False)


async def handle_help(chat_id: int) -> None:
    user_text = BOT_COMMANDS_HELP
    await send_telegram_message(chat_id, user_text)
    await send_telegram_message(
        chat_id,
        "Открыть приложение:",
        reply_markup=_webapp_inline_keyboard(),
    )


async def handle_invite(
    db: Session, chat_id: int, from_user: dict[str, Any], text: str
) -> None:
    parts = text.split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip():
        await send_telegram_message(
            chat_id,
            "Формат: /invite +79001234567\n\nУкажите номер в международном формате.",
        )
        return

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
        await send_telegram_message(
            chat_id,
            "Приглашать по номеру может только администратор семьи.",
        )
        return

    family_name = membership.family.name if membership.family else "семья"

    try:
        member = family_service.invite_member_by_phone(
            db,
            user,  # type: ignore[arg-type]
            membership.family_id,
            FamilyInviteByPhoneRequest(phone_number=parts[1].strip()),
        )
    except HTTPException as exc:
        detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
        await send_telegram_message(chat_id, detail)
        return

    if member.user_id:
        invited_user = db.get(User, member.user_id)
        if invited_user:
            await send_telegram_message(
                invited_user.telegram_id,
                f"Вас пригласили в семью «{family_name}» в ПланАм. "
                "Откройте приложение, чтобы увидеть общее меню и покупки.",
                reply_markup=_webapp_inline_keyboard(),
            )

    await send_telegram_message(
        chat_id,
        f"Участник {member.display_name} добавлен в семью «{family_name}».",
    )


async def process_telegram_update(db: Session, update: dict[str, Any]) -> None:
    message = update.get("message")
    if not message:
        return

    chat = message.get("chat") or {}
    chat_id = chat.get("id")
    from_user = message.get("from")
    if not chat_id or not from_user:
        return

    contact = message.get("contact")
    if contact:
        await handle_contact(db, chat_id, from_user, contact)
        return

    text = (message.get("text") or "").strip()
    command = text.split()[0].split("@")[0].lower() if text else ""

    if command in ("/start", "/start@planam_bot"):
        await handle_start(db, chat_id, from_user)
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

    if command in ("/help", "/help@planam_bot"):
        await handle_help(chat_id)
        return

    if command in ("/invite", "/invite@planam_bot"):
        await handle_invite(db, chat_id, from_user, text)
        return

    await send_telegram_message(
        chat_id,
        "Неизвестная команда. Доступны: /help, /invite +номер\n\n"
        "Или откройте приложение:",
        reply_markup=_webapp_inline_keyboard(),
    )
