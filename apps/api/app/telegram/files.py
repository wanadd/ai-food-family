import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


async def download_telegram_file(file_id: str) -> bytes | None:
    if not settings.telegram_bot_token or not file_id:
        return None

    base = f"https://api.telegram.org/bot{settings.telegram_bot_token}"

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            meta_resp = await client.get(
                f"{base}/getFile",
                params={"file_id": file_id},
            )
            meta = meta_resp.json()
            if not meta.get("ok"):
                logger.warning("getFile failed: %s", meta)
                return None
            file_path = meta["result"]["file_path"]
            file_resp = await client.get(
                f"https://api.telegram.org/file/bot{settings.telegram_bot_token}/{file_path}",
            )
            file_resp.raise_for_status()
            return file_resp.content
    except Exception:
        logger.exception("Failed to download Telegram file %s", file_id)
        return None
