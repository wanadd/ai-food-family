"""Build Telegram Bot API URLs (direct or via relay)."""

from __future__ import annotations

from app.config import settings

DEFAULT_TELEGRAM_API_BASE_URL = "https://api.telegram.org"


def telegram_api_base_url() -> str:
    """Normalized API base without trailing slash."""
    base = (settings.telegram_api_base_url or DEFAULT_TELEGRAM_API_BASE_URL).strip()
    return base.rstrip("/") or DEFAULT_TELEGRAM_API_BASE_URL


def telegram_bot_api_url(method: str, *, token: str | None = None) -> str:
    """URL for Bot API methods, e.g. sendMessage, getWebhookInfo."""
    bot_token = token or settings.telegram_bot_token
    method_name = method.strip().lstrip("/")
    return f"{telegram_api_base_url()}/bot{bot_token}/{method_name}"


def telegram_file_url(file_path: str, *, token: str | None = None) -> str:
    """URL for downloading a file returned by getFile."""
    bot_token = token or settings.telegram_bot_token
    path = str(file_path or "").lstrip("/")
    return f"{telegram_api_base_url()}/file/bot{bot_token}/{path}"
