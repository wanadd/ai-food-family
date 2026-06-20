"""Subscription / admin override validation — PLANAM V1.

New, centralized validators for plan codes and subscription statuses. Pure
functions, no DB access. Used by the project health audit and available to the
subscription/admin write-paths.

Plan codes mirror ``subscription_catalog.PLAN_SEEDS``. We deliberately keep a
local copy of the known codes (instead of importing the catalog) so this module
stays dependency-free and importable in isolation; ``is_valid_plan_code`` is the
source of truth for "is this a recognized plan".
"""

from __future__ import annotations

# Mirrors subscription_catalog.PLAN_SEEDS codes (+ historic "free").
KNOWN_PLAN_CODES: frozenset[str] = frozenset(
    {"trial", "free", "personal", "shared", "family", "pro"}
)

# Aliases seen in legacy data → canonical code.
_PLAN_ALIASES: dict[str, str] = {
    "basic": "personal",
    "premium": "pro",
    "пробный": "trial",
    "личный": "personal",
    "совместный": "shared",
    "семейный": "family",
}

KNOWN_STATUSES: frozenset[str] = frozenset(
    {"active", "trial", "trialing", "expired", "cancelled", "canceled", "past_due"}
)

_STATUS_ALIASES: dict[str, str] = {
    "trialing": "trial",
    "canceled": "cancelled",
}


def normalize_plan_code(code: str | None) -> str:
    """Trim/lowercase a plan code and map known aliases. Default: ``free``."""
    raw = (code or "").strip().lower()
    if not raw:
        return "free"
    raw = _PLAN_ALIASES.get(raw, raw)
    return raw


def is_valid_plan_code(code: str | None) -> bool:
    return normalize_plan_code(code) in KNOWN_PLAN_CODES


def normalize_status(status: str | None) -> str:
    """Trim/lowercase a status and map known aliases. Default: ``active``."""
    raw = (status or "").strip().lower()
    if not raw:
        return "active"
    return _STATUS_ALIASES.get(raw, raw)


def is_valid_status(status: str | None) -> bool:
    return normalize_status(status) in KNOWN_STATUSES


__all__ = [
    "KNOWN_PLAN_CODES",
    "KNOWN_STATUSES",
    "normalize_plan_code",
    "is_valid_plan_code",
    "normalize_status",
    "is_valid_status",
]
