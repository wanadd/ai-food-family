"""Recipe title normalization for search and duplicate detection."""

from __future__ import annotations

import re

ALLOWED_CATALOG_MEAL_TYPES = frozenset({"breakfast", "lunch", "dinner", "snack"})
EXTENDED_MEAL_TYPES = frozenset(
    {
        "breakfast",
        "lunch",
        "dinner",
        "snack",
        "dessert",
        "drink",
        "cocktail",
        "smoothie",
        "protein_shake",
        "tea",
        "coffee",
    }
)

MEAL_TYPE_TO_CATALOG: dict[str, str] = {
    "breakfast": "breakfast",
    "lunch": "lunch",
    "dinner": "dinner",
    "snack": "snack",
    "dessert": "snack",
    "drink": "snack",
    "cocktail": "snack",
    "smoothie": "snack",
    "protein_shake": "snack",
    "tea": "snack",
    "coffee": "snack",
}


def normalize_title(value: str) -> str:
    """Lowercase collapsed whitespace title for dedup/search."""
    return re.sub(r"\s+", " ", value.strip().lower())


def catalog_meal_type(meal_type: str | None) -> str:
    raw = (meal_type or "lunch").strip().lower()
    return MEAL_TYPE_TO_CATALOG.get(raw, "lunch")


def display_title_from(title: str) -> str | None:
    """Light cleanup for catalog display; returns None when same as title."""
    cleaned = re.sub(r"\s+", " ", title.strip())
    unquoted = re.sub(r'^["«»]+|["«»]+$', "", cleaned).strip()
    if not unquoted or unquoted == cleaned:
        return None
    return unquoted
