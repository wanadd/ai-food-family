"""Notification / care settings validation — PLANAM V1.

New, centralized validators for reminder times, quiet hours and timezones.
Pure functions, no DB access. Used by the notifications/care write-paths and by
the project health audit to flag invalid settings.
"""

from __future__ import annotations

import re

_TIME_RE = re.compile(r"^([01]?\d|2[0-3]):[0-5]\d$")

# A small, safe allow-list. Unknown timezones are not rejected (the app stores
# IANA names), but a blank/None timezone falls back to the project default.
DEFAULT_TIMEZONE = "Europe/Moscow"
KNOWN_CARE_LEVELS: frozenset[str] = frozenset({"light", "standard", "intense"})


def is_valid_time(value: str | None) -> bool:
    """True if ``value`` is a well-formed ``HH:MM`` 24h time."""
    if not value:
        return False
    return bool(_TIME_RE.match(value.strip()))


def normalize_time(value: str | None, fallback: str) -> str:
    """Return a zero-padded ``HH:MM`` time or ``fallback`` when invalid."""
    raw = (value or "").strip()
    if not _TIME_RE.match(raw):
        return fallback
    hh, mm = raw.split(":")
    return f"{int(hh):02d}:{mm}"


def normalize_quiet_hours(
    start: str | None, end: str | None
) -> tuple[str | None, str | None]:
    """Validate a quiet-hours window.

    Both ends must be valid ``HH:MM`` for the window to be kept; otherwise both
    are cleared (a half-defined window is meaningless). Windows that wrap past
    midnight (start > end) are allowed — they represent overnight quiet hours.
    """
    if not is_valid_time(start) or not is_valid_time(end):
        return None, None
    norm_start = normalize_time(start, "00:00")
    norm_end = normalize_time(end, "00:00")
    if norm_start == norm_end:
        # Zero-length window — treat as "no quiet hours".
        return None, None
    return norm_start, norm_end


def normalize_care_level(value: str | None) -> str:
    """Map a care level to a known value, defaulting to ``standard``."""
    level = (value or "").strip().lower()
    return level if level in KNOWN_CARE_LEVELS else "standard"


def normalize_timezone(value: str | None) -> str:
    """Return a non-empty timezone string, defaulting to the project default."""
    tz = (value or "").strip()
    return tz or DEFAULT_TIMEZONE


def normalize_notification_settings(data: dict) -> dict:
    """Normalize a notification-settings-shaped dict (returns a new dict).

    Recognized ``*_time`` fields are coerced to valid ``HH:MM`` (keeping the
    model defaults as fallbacks); ``timezone`` is defaulted. Unknown keys pass
    through untouched.
    """
    cleaned = dict(data)
    time_fallbacks = {
        "buy_reminder_time": "09:00",
        "cook_reminder_time": "17:30",
        "cook_breakfast_time": "08:00",
        "cook_lunch_time": "13:00",
        "cook_dinner_time": "18:00",
    }
    for field, fallback in time_fallbacks.items():
        if field in cleaned and cleaned.get(field) is not None:
            cleaned[field] = normalize_time(cleaned.get(field), fallback)
    if "timezone" in cleaned and cleaned.get("timezone") is not None:
        cleaned["timezone"] = normalize_timezone(cleaned.get("timezone"))
    return cleaned


__all__ = [
    "DEFAULT_TIMEZONE",
    "KNOWN_CARE_LEVELS",
    "is_valid_time",
    "normalize_time",
    "normalize_quiet_hours",
    "normalize_care_level",
    "normalize_timezone",
    "normalize_notification_settings",
]
