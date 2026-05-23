"""Telegram bot onboarding: legal consents and phone."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.config import settings
from app.legal.documents import DOCUMENTS, LEGAL_DOCUMENTS_VERSION
from app.models.user import User
from app.services import bot_session as bot_session_service
from app.services.legal_consent import (
    accept_legal,
    user_can_access_app,
    user_has_legal_consent,
)
from app.schemas.legal import LegalAcceptRequest
from app.telegram.messaging import (
    own_phone_keyboard,
    remove_keyboard,
    send_telegram_message,
    webapp_inline_keyboard,
)

LEGAL_PREFIX = "legal:"
PHONE_SKIP_CALLBACK = "phone:skip"


def _legal_flags(payload: dict) -> dict[str, bool]:
    legal = payload.get("legal") or {}
    if not isinstance(legal, dict):
        legal = {}
    return {
        "terms": bool(legal.get("terms")),
        "privacy": bool(legal.get("privacy")),
        "personal": bool(legal.get("personal")),
    }


def _legal_text(flags: dict[str, bool]) -> str:
    def mark(on: bool) -> str:
        return "☑" if on else "☐"

    return (
        "Добро пожаловать в **ПланАм**\n\n"
        "Ваш AI-помощник по:\n"
        "• меню\n"
        "• покупкам\n"
        "• запасам\n"
        "• семейному питанию\n"
        "• спортивным целям\n\n"
        "Перед началом ознакомьтесь с документами.\n\n"
        f"{mark(flags['terms'])} Пользовательское соглашение\n"
        f"{mark(flags['privacy'])} Политика конфиденциальности\n"
        f"{mark(flags['personal'])} Согласие на обработку персональных данных\n\n"
        "Отметьте все пункты, затем нажмите «Продолжить»."
    )


def _legal_keyboard(flags: dict[str, bool]) -> dict[str, Any]:
    all_on = flags["terms"] and flags["privacy"] and flags["personal"]
    rows = [
        [
            {
                "text": f"{'☑' if flags['terms'] else '☐'} Соглашение",
                "callback_data": f"{LEGAL_PREFIX}toggle:terms",
            },
            {
                "text": "Открыть",
                "url": DOCUMENTS["terms"]["url"],
            },
        ],
        [
            {
                "text": f"{'☑' if flags['privacy'] else '☐'} Конфиденциальность",
                "callback_data": f"{LEGAL_PREFIX}toggle:privacy",
            },
            {
                "text": "Открыть",
                "url": DOCUMENTS["privacy"]["url"],
            },
        ],
        [
            {
                "text": f"{'☑' if flags['personal'] else '☐'} Персональные данные",
                "callback_data": f"{LEGAL_PREFIX}toggle:personal",
            },
            {
                "text": "Открыть",
                "url": DOCUMENTS["personal_data"]["url"],
            },
        ],
        [
            {
                "text": "Продолжить →",
                "callback_data": f"{LEGAL_PREFIX}continue",
            }
            if all_on
            else {
                "text": "Продолжить (отметьте всё)",
                "callback_data": f"{LEGAL_PREFIX}continue",
            },
        ],
    ]
    return {"inline_keyboard": rows}


async def send_welcome_legal(db: Session, user: User, chat_id: int) -> None:
    payload = bot_session_service.get_payload(
        bot_session_service.get_session(db, user.telegram_id)
    )
    flags = _legal_flags(payload)
    bot_session_service.set_session_state(
        db, user.telegram_id, bot_session_service.STATE_AWAITING_LEGAL, payload=payload
    )
    text = _legal_text(flags).replace("**", "")
    await send_telegram_message(
        chat_id,
        text,
        reply_markup=_legal_keyboard(flags),
    )


async def handle_legal_callback(
    db: Session, user: User, chat_id: int, data: str
) -> bool:
    if not data.startswith(LEGAL_PREFIX):
        return False

    action = data[len(LEGAL_PREFIX) :]
    session = bot_session_service.get_or_create_session(db, user.telegram_id)
    payload = bot_session_service.get_payload(session)
    legal = payload.get("legal") or {}
    if not isinstance(legal, dict):
        legal = {}

    if action.startswith("toggle:"):
        key = action.split(":", 1)[1]
        legal[key] = not bool(legal.get(key))
        payload["legal"] = legal
        bot_session_service.set_payload(db, user.telegram_id, payload)
        flags = _legal_flags(payload)
        await send_telegram_message(
            chat_id,
            _legal_text(flags).replace("**", ""),
            reply_markup=_legal_keyboard(flags),
        )
        return True

    if action == "continue":
        flags = _legal_flags(payload)
        if not (flags["terms"] and flags["privacy"] and flags["personal"]):
            await send_telegram_message(
                chat_id,
                "Нужно отметить все три документа, чтобы продолжить.",
                reply_markup=_legal_keyboard(flags),
            )
            return True
        accept_legal(
            db,
            user,
            LegalAcceptRequest(
                accepted_terms=True,
                accepted_privacy=True,
                accepted_personal_data=True,
            ),
        )
        await send_phone_request(db, user, chat_id)
        return True

    return False


async def send_phone_request(db: Session, user: User, chat_id: int) -> None:
    bot_session_service.set_session_state(
        db, user.telegram_id, bot_session_service.STATE_AWAITING_PHONE
    )
    skip_kb = {
        "inline_keyboard": [
            [{"text": "Пропустить", "callback_data": PHONE_SKIP_CALLBACK}],
        ],
    }
    await send_telegram_message(
        chat_id,
        "Поделитесь номером телефона — он нужен для восстановления доступа, "
        "уведомлений и подписки.\n\n"
        "Нажмите кнопку ниже:",
        reply_markup=own_phone_keyboard(),
    )
    await send_telegram_message(
        chat_id,
        "Или пропустите этот шаг (некоторые функции могут быть недоступны):",
        reply_markup=skip_kb,
    )


async def handle_phone_skip(db: Session, user: User, chat_id: int) -> None:
    from app.services.legal_consent import mark_phone_skipped

    mark_phone_skipped(db, user)
    await send_registration_complete(db, user, chat_id)


async def send_registration_complete(db: Session, user: User, chat_id: int) -> None:
    from app.services.bot_menu import send_main_menu

    bot_session_service.clear_session_state(db, user.telegram_id)
    await send_telegram_message(
        chat_id,
        "🚀 Регистрация завершена!\n\nОткройте ПланАм:",
        reply_markup=webapp_inline_keyboard(),
    )
    await send_main_menu(chat_id)


async def route_after_start(db: Session, user: User, chat_id: int) -> None:
    if not user_has_legal_consent(user):
        await send_welcome_legal(db, user, chat_id)
        return
    if not user_can_access_app(user):
        await send_phone_request(db, user, chat_id)
        return
    from app.services.bot_menu import send_main_menu

    await send_telegram_message(
        chat_id,
        "С возвращением в ПланАм!",
        reply_markup=remove_keyboard(),
    )
    await send_main_menu(chat_id)
    await send_telegram_message(
        chat_id,
        "Открыть приложение:",
        reply_markup=webapp_inline_keyboard(),
    )
