from __future__ import annotations

import secrets
import time
import uuid

_TIMESTAMP_BITS = 48
_RAND_A_BITS = 12
_RAND_B_BITS = 62
_VERSION_7 = 0x7
_RFC_4122_VARIANT = 0b10


def new_uuid7(now_ns: int | None = None) -> uuid.UUID:
    """Generate an RFC 9562 UUIDv7 value from Unix epoch milliseconds."""
    timestamp_ms = (time.time_ns() if now_ns is None else now_ns) // 1_000_000
    timestamp_ms &= (1 << _TIMESTAMP_BITS) - 1
    rand_a = secrets.randbits(_RAND_A_BITS)
    rand_b = secrets.randbits(_RAND_B_BITS)

    value = (
        (timestamp_ms << 80)
        | (_VERSION_7 << 76)
        | (rand_a << 64)
        | (_RFC_4122_VARIANT << 62)
        | rand_b
    )
    return uuid.UUID(int=value)


def uuid7_str(now_ns: int | None = None) -> str:
    return str(new_uuid7(now_ns=now_ns))


def is_uuid7(value: uuid.UUID | str) -> bool:
    parsed = value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))
    return parsed.version == 7 and parsed.variant == uuid.RFC_4122
