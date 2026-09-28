"""Shared operational stop for legacy provider calls during OD-18 cutover."""

from functools import lru_cache

import redis

from app.config import settings

FROZEN_KEY = "planam:legacy-cutover:outbound-frozen"


class OutboundFrozen(RuntimeError):
    pass


@lru_cache(maxsize=1)
def redis_client() -> redis.Redis:
    return redis.from_url(settings.redis_url, socket_connect_timeout=1, socket_timeout=1)


def outbound_status() -> bool:
    """Read the shared flag; an unreadable flag is never interpreted as OFF."""
    value = redis_client().get(FROZEN_KEY)
    if value not in (None, b"1"):
        raise OutboundFrozen("LEGACY_OUTBOUND_STATE_INVALID")
    return value == b"1"


def assert_outbound_available() -> None:
    if not settings.legacy_outbound_guard_enabled:
        return
    try:
        frozen = outbound_status()
    except redis.RedisError as exc:
        raise OutboundFrozen("LEGACY_OUTBOUND_STATE_UNAVAILABLE") from exc
    if frozen:
        raise OutboundFrozen("LEGACY_OUTBOUND_FROZEN")


def outbound_allowed() -> bool:
    try:
        assert_outbound_available()
    except OutboundFrozen:
        return False
    return True
