import logging

import httpx

from app.config import settings
from app.telegram.api_urls import telegram_bot_api_url, telegram_file_url

logger = logging.getLogger(__name__)


async def download_telegram_file(file_id: str) -> bytes | None:
    if not settings.telegram_bot_token or not file_id:
        return None

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            meta_resp = await client.get(
                telegram_bot_api_url("getFile"),
                params={"file_id": file_id},
            )
            meta = meta_resp.json()
            if not meta.get("ok"):
                logger.warning("getFile failed: %s", meta)
                return None
            file_path = meta["result"]["file_path"]
            file_resp = await client.get(telegram_file_url(file_path))
            file_resp.raise_for_status()
            return file_resp.content
    except Exception:
        logger.exception("Failed to download Telegram file %s", file_id)
        return None
