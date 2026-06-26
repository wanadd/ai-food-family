"""Canonical subscription plan codes and legacy aliases."""

from __future__ import annotations

START_PLAN_CODE = "start"
START_DAYS = 7

CANONICAL_ACTIVE_PLANS = frozenset(
    {"start", "personal", "shared", "family", "pro"}
)

LEGACY_START_ALIASES = frozenset({"trial", "free", "demo"})

DEPRECATED_PLAN_CODES = LEGACY_START_ALIASES

PUBLIC_PLAN_LABELS: dict[str, str] = {
    "start": "Старт",
    "personal": "Личный",
    "shared": "Совместный",
    "family": "Семейный",
    "pro": "ПланАм PRO",
}


def resolve_storage_plan_code(code: str | None) -> str:
    """Map legacy DB codes to canonical plan code for lookups."""
    if not code:
        return START_PLAN_CODE
    normalized = code.strip().lower()
    if normalized in LEGACY_START_ALIASES:
        return START_PLAN_CODE
    return normalized


def public_plan_code(code: str | None) -> str:
    """Code exposed to clients (never free/demo/trial)."""
    return resolve_storage_plan_code(code)


def public_plan_name(code: str | None, fallback_name: str | None = None) -> str:
    pub = public_plan_code(code)
    if pub in PUBLIC_PLAN_LABELS:
        return PUBLIC_PLAN_LABELS[pub]
    if fallback_name:
        return fallback_name
    return pub


def is_start_access_plan(code: str | None) -> bool:
    return resolve_storage_plan_code(code) == START_PLAN_CODE


def is_deprecated_plan(code: str | None) -> bool:
    if not code:
        return False
    return code.strip().lower() in DEPRECATED_PLAN_CODES
