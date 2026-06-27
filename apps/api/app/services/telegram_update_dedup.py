"""Idempotent Telegram webhook update handling via Redis."""

from __future__ import annotations

import logging
from typing import Any

from app.config import settings

logger = logging.getLogger(__name__)

_DEDUP_TTL_SECONDS = 86400  # 24h


def _redis_client():
    try:
        import redis

        return redis.from_url(settings.redis_url, socket_connect_timeout=1)
    except Exception:
        logger.warning("Redis unavailable for Telegram dedup")
        return None


def _claim_key(client, key: str) -> bool:
    """Return True if this is the first time we see key (should process)."""
    try:
        return bool(client.set(key, "1", nx=True, ex=_DEDUP_TTL_SECONDS))
    except Exception:
        logger.warning("Redis dedup claim failed for %s", key)
        return True


def should_process_telegram_update(update: dict[str, Any]) -> bool:
    """False if update was already processed (duplicate webhook delivery)."""
    client = _redis_client()
    if client is None:
        return True

    update_id = update.get("update_id")
    if update_id is not None:
        if not _claim_key(client, f"telegram_update:{update_id}"):
            logger.info("Skip duplicate Telegram update_id=%s", update_id)
            return False

    callback = update.get("callback_query") or {}
    callback_id = callback.get("id")
    if callback_id:
        if not _claim_key(client, f"telegram_callback:{callback_id}"):
            logger.info("Skip duplicate Telegram callback_id=%s", callback_id)
            return False

    return True
