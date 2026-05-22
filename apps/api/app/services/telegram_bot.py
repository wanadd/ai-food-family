import logging
from typing import Any

import httpx
from sqlalchemy.orm import Session

from app.config import settings
from app.services.users import upsert_user_from_bot

logger = logging.getLogger(__name__)


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


async def send_open_planam_button(chat_id: int, text: str) -> None:
    await send_telegram_message(
        chat_id,
        text,
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

    if user.phone_number:
        await send_open_planam_button(
            chat_id,
            "С возвращением в ПланАм! Откройте приложение, чтобы посмотреть меню и список покупок.",
        )
        return

    await send_telegram_message(
        chat_id,
        "Добро пожаловать в ПланАм! Чтобы персонализировать меню и покупки, подтвердите номер телефона.",
        reply_markup=_contact_keyboard(),
    )


async def handle_contact(
    db: Session, chat_id: int, from_user: dict[str, Any], contact: dict[str, Any]
) -> None:
    if contact.get("user_id") != from_user.get("id"):
        await send_telegram_message(
            chat_id,
            "Пожалуйста, отправьте свой номер через кнопку «Поделиться номером».",
        )
        return

    phone = contact.get("phone_number")
    if not phone:
        await send_telegram_message(chat_id, "Не удалось прочитать номер. Попробуйте ещё раз.")
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

    await send_telegram_message(
        chat_id,
        "Готово! Теперь можно открыть ПланАм.",
        reply_markup=_remove_keyboard(),
    )
    await send_open_planam_button(chat_id, "Нажмите кнопку ниже:")


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
    if text.startswith("/start"):
        await handle_start(db, chat_id, from_user)
