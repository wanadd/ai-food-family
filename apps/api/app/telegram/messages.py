import logging

import httpx

from app.config import settings
from app.telegram.api_urls import telegram_bot_api_url

logger = logging.getLogger(__name__)


async def send_telegram_message(
    telegram_id: int,
    text: str,
    *,
    web_app_path: str = "/",
    button_text: str = "Открыть приложение",
) -> bool:
    if not settings.telegram_outbound_allowed:
        logger.info("Skip Telegram message: outbound disabled")
        return False
    if not settings.telegram_bot_token:
        logger.info("Skip Telegram message: TELEGRAM_BOT_TOKEN is not set")
        return False

    base_url = settings.telegram_webapp_url.rstrip("/")
    web_app_url = f"{base_url}{web_app_path}"

    payload: dict = {
        "chat_id": telegram_id,
        "text": text,
        "parse_mode": "HTML",
    }

    if settings.telegram_webapp_url:
        payload["reply_markup"] = {
            "inline_keyboard": [
                [
                    {
                        "text": button_text,
                        "web_app": {"url": web_app_url},
                    }
                ]
            ]
        }

    url = telegram_bot_api_url("sendMessage")

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(url, json=payload)
        data = response.json()

    if not data.get("ok"):
        logger.warning(
            "Failed to send Telegram message to %s: %s", telegram_id, data
        )
        return False

    return True
