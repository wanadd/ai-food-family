import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


async def setup_menu_button() -> None:
    if not settings.telegram_bot_token or not settings.telegram_webapp_url:
        logger.info(
            "Skip Telegram menu button setup: TELEGRAM_BOT_TOKEN or "
            "TELEGRAM_WEBAPP_URL is not set"
        )
        return

    payload = {
        "menu_button": {
            "type": "web_app",
            "text": settings.telegram_menu_button_text,
            "web_app": {"url": settings.telegram_webapp_url},
        }
    }

    url = (
        f"https://api.telegram.org/bot{settings.telegram_bot_token}/setChatMenuButton"
    )

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(url, json=payload)
        data = response.json()

    if not data.get("ok"):
        logger.warning("Failed to set Telegram menu button: %s", data)
        return

    logger.info("Telegram menu button configured for %s", settings.telegram_webapp_url)
