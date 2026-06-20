"""Subscription capability gates — foundation only (Phase 4C)."""

from __future__ import annotations

from typing import Literal

TariffSlug = Literal[
    "start_trial",
    "personal_plus",
    "pair",
    "family",
    "family_pro",
]

CapabilityKey = Literal[
    "ai_inventory_menu",
    "ai_leftovers_suggestions",
    "health_extended",
    "health_sport_mode",
    "strict_diet_mode",
    "external_food_ai_parse",
    "voice_food_log",
    "photo_food_log",
    "ocr_receipts",
    "family_profiles_limit",
    "monthly_menu_depth",
]

TARIFF_CAPABILITIES: dict[TariffSlug, dict[str, object]] = {
    "start_trial": {
        "family_profiles_limit": 1,
        "monthly_menu_depth": 7,
        "ai_inventory_menu": False,
        "ai_leftovers_suggestions": False,
        "health_extended": False,
        "health_sport_mode": False,
        "strict_diet_mode": False,
        "external_food_ai_parse": False,
        "voice_food_log": False,
        "photo_food_log": False,
        "ocr_receipts": False,
    },
    "personal_plus": {
        "family_profiles_limit": 1,
        "monthly_menu_depth": 30,
        "ai_inventory_menu": True,
        "ai_leftovers_suggestions": True,
        "health_extended": True,
        "health_sport_mode": False,
        "strict_diet_mode": False,
        "external_food_ai_parse": True,
        "voice_food_log": True,
        "photo_food_log": True,
        "ocr_receipts": True,
    },
    "pair": {
        "family_profiles_limit": 3,
        "monthly_menu_depth": 30,
        "ai_inventory_menu": True,
        "ai_leftovers_suggestions": True,
        "health_extended": True,
        "health_sport_mode": False,
        "strict_diet_mode": False,
        "external_food_ai_parse": True,
        "voice_food_log": True,
        "photo_food_log": True,
        "ocr_receipts": True,
    },
    "family": {
        "family_profiles_limit": 5,
        "monthly_menu_depth": 30,
        "ai_inventory_menu": True,
        "ai_leftovers_suggestions": True,
        "health_extended": True,
        "health_sport_mode": False,
        "strict_diet_mode": False,
        "external_food_ai_parse": True,
        "voice_food_log": True,
        "photo_food_log": True,
        "ocr_receipts": True,
    },
    "family_pro": {
        "family_profiles_limit": 7,
        "monthly_menu_depth": 30,
        "ai_inventory_menu": True,
        "ai_leftovers_suggestions": True,
        "health_extended": True,
        "health_sport_mode": True,
        "strict_diet_mode": True,
        "external_food_ai_parse": True,
        "voice_food_log": True,
        "photo_food_log": True,
        "ocr_receipts": True,
    },
}


def get_tariff_capabilities(tariff: TariffSlug) -> dict[str, object]:
    return dict(TARIFF_CAPABILITIES.get(tariff, TARIFF_CAPABILITIES["start_trial"]))


def has_capability(tariff: TariffSlug, capability: CapabilityKey) -> bool:
    caps = get_tariff_capabilities(tariff)
    value = caps.get(capability)
    if isinstance(value, bool):
        return value
    return False


def profile_limit_for_tariff(tariff: TariffSlug) -> int:
    caps = get_tariff_capabilities(tariff)
    return int(caps.get("family_profiles_limit", 1))
