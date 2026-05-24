"""Telegram bot flow for hidden /admin access."""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.orm import Session

from app.services import admin_auth
from app.services import bot_session as bot_session_service
from app.services.admin_auth import STATE_AWAITING_ADMIN_PIN
from app.services.users import get_user_by_telegram_id, upsert_user_from_bot

logger = logging.getLogger(__name__)

_MSG_UNKNOWN = "Откройте ПланАм через меню"
_MSG_PIN_PROMPT = "Введите PIN администратора"
_MSG_PIN_OK = "Доступ подтверждён"
_MSG_PIN_BAD = "Неверный PIN"
_MSG_LOCKED = "Слишком много попыток. Повторите через 15 минут."


def _admin_panel_button(session_token: str) -> dict[str, Any]:
    return {
        "inline_keyboard": [
            [
                {
                    "text": "📊 Открыть админ-панель",
                    "web_app": {"url": admin_auth.admin_webapp_url(session_token)},
                }
            ],
        ],
    }


async def handle_admin_command(
    db: Session, chat_id: int, from_user: dict[str, Any]
) -> None:
    from app.services.telegram_bot import send_telegram_message

    telegram_id = int(from_user["id"])
    if not admin_auth.panel_enabled():
        await send_telegram_message(chat_id, _MSG_UNKNOWN)
        return
    if not admin_auth.is_admin_telegram_id(telegram_id):
        await send_telegram_message(chat_id, _MSG_UNKNOWN)
        return
    if admin_auth.is_pin_locked(db, telegram_id):
        await send_telegram_message(chat_id, _MSG_LOCKED)
        return
    bot_session_service.set_session_state(
        db, telegram_id, STATE_AWAITING_ADMIN_PIN
    )
    await send_telegram_message(chat_id, _MSG_PIN_PROMPT)


async def handle_admin_pin_message(
    db: Session, chat_id: int, from_user: dict[str, Any], pin_text: str
) -> bool:
    """Returns True if message was consumed by admin PIN flow."""
    from app.services.telegram_bot import send_telegram_message

    telegram_id = int(from_user["id"])
    session = bot_session_service.get_session(db, telegram_id)
    if not session or session.state != STATE_AWAITING_ADMIN_PIN:
        return False
    if not admin_auth.is_admin_telegram_id(telegram_id):
        bot_session_service.clear_session_state(db, telegram_id)
        return False
    if admin_auth.is_pin_locked(db, telegram_id):
        await send_telegram_message(chat_id, _MSG_LOCKED)
        bot_session_service.clear_session_state(db, telegram_id)
        return True

    pin = pin_text.strip()
    if not pin or pin.startswith("/"):
        await send_telegram_message(chat_id, _MSG_PIN_PROMPT)
        return True

    if not admin_auth.verify_pin(pin):
        admin_auth.record_pin_attempt(db, telegram_id, success=False)
        await send_telegram_message(chat_id, _MSG_PIN_BAD)
        if admin_auth.is_pin_locked(db, telegram_id):
            await send_telegram_message(chat_id, _MSG_LOCKED)
            bot_session_service.clear_session_state(db, telegram_id)
        return True

    admin_auth.record_pin_attempt(db, telegram_id, success=True)
    user = get_user_by_telegram_id(db, telegram_id)
    if user is None:
        user, _ = upsert_user_from_bot(
            db,
            telegram_id=telegram_id,
            username=from_user.get("username"),
            first_name=from_user.get("first_name"),
            last_name=from_user.get("last_name"),
            language_code=from_user.get("language_code"),
        )

    admin_session = admin_auth.create_admin_session(db, user)
    bot_session_service.clear_session_state(db, telegram_id)
    await send_telegram_message(
        chat_id,
        _MSG_PIN_OK,
        reply_markup=_admin_panel_button(admin_session.session_token),
    )
    return True
