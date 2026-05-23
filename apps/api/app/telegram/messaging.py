import logging
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


def api_url(method: str) -> str:
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
        response = await client.post(api_url("sendMessage"), json=payload)
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
        await client.post(api_url("answerCallbackQuery"), json=payload)


def own_phone_keyboard() -> dict[str, Any]:
    return {
        "keyboard": [[{"text": "📱 Поделиться номером", "request_contact": True}]],
        "resize_keyboard": True,
        "one_time_keyboard": True,
    }


def webapp_inline_keyboard() -> dict[str, Any]:
    url = settings.telegram_webapp_url or "https://planam.ru"
    return {
        "inline_keyboard": [
            [{"text": "🚀 Открыть ПланАм", "web_app": {"url": url}}],
        ],
    }


def remove_keyboard() -> dict[str, Any]:
    return {"remove_keyboard": True}
