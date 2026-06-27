"""Distributed lock for notification scheduler (Redis or PG advisory)."""

from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import settings

logger = logging.getLogger(__name__)

_LOCK_KEY = "planam:notification_scheduler"
_LOCK_TTL = 25  # seconds, < poll interval
_PG_LOCK_ID = 918_001


@contextmanager
def notification_scheduler_lock(db: Session | None = None) -> Generator[bool, None, None]:
    """Yield True if this process holds the scheduler lock."""
    acquired = False
    try:
        import redis

        client = redis.from_url(settings.redis_url, socket_connect_timeout=1)
        acquired = bool(client.set(_LOCK_KEY, "1", nx=True, ex=_LOCK_TTL))
        if acquired:
            yield True
            return
    except Exception:
        logger.debug("Redis scheduler lock unavailable, trying PG advisory lock")

    if db is not None:
        try:
            row = db.execute(
                text("SELECT pg_try_advisory_lock(:id)"),
                {"id": _PG_LOCK_ID},
            ).scalar()
            acquired = bool(row)
            try:
                yield acquired
            finally:
                if acquired:
                    db.execute(text("SELECT pg_advisory_unlock(:id)"), {"id": _PG_LOCK_ID})
            return
        except Exception:
            logger.warning("PG advisory lock failed")

    yield True
