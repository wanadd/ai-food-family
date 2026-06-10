import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


def resolve_webhook_url() -> str | None:
    """Public URL where Telegram sends updates (must be reachable from internet)."""
    if settings.telegram_webhook_url.strip():
        return settings.telegram_webhook_url.strip().rstrip("/")

    if settings.telegram_webapp_url.strip():
        base = settings.telegram_webapp_url.strip().rstrip("/")
        return f"{base}/api/telegram/webhook"

    return None


async def _telegram_api(method: str, payload: dict | None = None) -> dict:
    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/{method}"
    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.post(url, json=payload or {})
        return response.json()


async def setup_menu_button() -> None:
    if not settings.telegram_bot_token or not settings.telegram_webapp_url:
        logger.info(
            "Skip Telegram menu button: TELEGRAM_BOT_TOKEN or TELEGRAM_WEBAPP_URL missing"
        )
        return

    payload = {
        "menu_button": {
            "type": "web_app",
            "text": settings.telegram_menu_button_text,
            "web_app": {"url": settings.telegram_webapp_url},
        }
    }

    data = await _telegram_api("setChatMenuButton", payload)
    if not data.get("ok"):
        logger.warning("setChatMenuButton failed: %s", data)
        return

    logger.info("Telegram menu button → %s", settings.telegram_webapp_url)


async def setup_bot_commands() -> None:
    """Register bot command menu so the chat always has visible entry points."""
    if not settings.telegram_bot_token:
        logger.info("Skip Telegram bot commands: TELEGRAM_BOT_TOKEN missing")
        return

    payload = {
        "commands": [
            {"command": "start", "description": "Запустить PLANAM"},
            {"command": "help", "description": "Помощь и кнопки"},
            {"command": "invite", "description": "Пригласить в семью"},
        ]
    }
    data = await _telegram_api("setMyCommands", payload)
    if not data.get("ok"):
        logger.warning("setMyCommands failed: %s", data)
        return
    logger.info("Telegram bot commands registered")


async def setup_webhook() -> None:
    if not settings.telegram_auto_setup_webhook:
        logger.info("Telegram auto webhook setup disabled (TELEGRAM_AUTO_SETUP_WEBHOOK=false)")
        return

    webhook_url = resolve_webhook_url()
    if not settings.telegram_bot_token:
        logger.warning("Skip Telegram webhook: TELEGRAM_BOT_TOKEN is not set")
        return

    if not webhook_url:
        logger.warning(
            "Skip Telegram webhook: set TELEGRAM_WEBHOOK_URL or TELEGRAM_WEBAPP_URL "
            "(expected https://<domain>/api/telegram/webhook behind nginx)"
        )
        return

    data = await _telegram_api("setWebhook", {"url": webhook_url})
    if not data.get("ok"):
        logger.error("setWebhook failed for %s: %s", webhook_url, data)
        return

    logger.info("Telegram webhook registered → %s", webhook_url)

    info = await _telegram_api("getWebhookInfo", {})
    if info.get("ok"):
        result = info.get("result") or {}
        logger.info(
            "Webhook info: url=%s pending=%s last_error=%s",
            result.get("url"),
            result.get("pending_update_count"),
            result.get("last_error_message"),
        )


async def get_webhook_info() -> dict:
    if not settings.telegram_bot_token:
        return {"ok": False, "error": "TELEGRAM_BOT_TOKEN not set"}
    data = await _telegram_api("getWebhookInfo", {})
    return {
        "ok": data.get("ok", False),
        "configured_url": resolve_webhook_url(),
        "telegram": data.get("result"),
    }
