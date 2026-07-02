"""User-facing recipe description helpers (response fallback only; no DB writes)."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from app.services.recipe_storage import get_structured_ingredients, get_tags

if TYPE_CHECKING:
    from app.models.recipe import Recipe

FORBIDDEN_FALLBACK_MARKERS = (
    "source_url",
    "original_url",
    "povarenok",
    "поваренок",
    "gold_v3",
    "recipe_schema_v3",
    "upgraded_from_legacy",
    "status:gold",
    "no_pork",
    "no pork",
)
ENGLISH_PREFIX_RE = re.compile(
    r"^\s*(high protein|pro weight loss|pre-workout|post-workout|meal prep)\s*:",
    re.I,
)
MEAL_TYPE_PHRASE = {
    "breakfast": "завтрак",
    "lunch": "обед",
    "dinner": "ужин",
    "snack": "перекус",
    "dessert": "десерт",
}


UPGRADED_GOLD_V3_RECIPE_IDS = frozenset(
    {
        2,
        227,
        228,
        229,
        230,
        231,
        232,
        233,
        234,
        235,
        236,
        237,
        238,
        239,
        240,
        241,
        242,
        243,
        244,
        245,
        246,
        247,
        248,
        249,
        250,
        251,
        252,
        253,
        254,
        255,
    }
)


def is_gold_v3_for_display(recipe: Recipe) -> bool:
    if recipe.id is not None and int(recipe.id) in UPGRADED_GOLD_V3_RECIPE_IDS:
        return True
    tags = get_tags(recipe)
    if "upgraded_from_legacy" in tags:
        return True
    return (
        "gold_v3" in tags
        or "recipe_schema_v3" in tags
        or (
            str(getattr(recipe, "source_type", "") or "") == "seed"
            and recipe.id is not None
            and 256 <= int(recipe.id) <= 265
        )
    )


def _ingredient_names(recipe: Recipe, limit: int = 3) -> list[str]:
    names: list[str] = []
    for item in get_structured_ingredients(recipe):
        name = str(item.get("name") or "").strip()
        if not name:
            continue
        lowered = name[0].lower() + name[1:] if name else name
        if lowered not in names:
            names.append(lowered)
        if len(names) >= limit:
            break
    return names


def _ingredient_phrase(names: list[str]) -> str:
    if not names:
        return ""
    if len(names) == 1:
        return f"с {names[0]}"
    if len(names) == 2:
        return f"с {names[0]} и {names[1]}"
    return f"с {names[0]}, {names[1]} и {names[2]}"


def build_description_fallback(recipe: Recipe) -> str:
    """Deterministic Russian fallback for empty Gold V3 descriptions."""
    names = _ingredient_names(recipe)
    phrase = _ingredient_phrase(names)
    meal = MEAL_TYPE_PHRASE.get(str(getattr(recipe, "meal_type", "") or "").strip(), "")
    if phrase and meal:
        return f"Домашнее блюдо для {meal} {phrase} — удобный вариант для семейного меню."
    if phrase:
        return f"Сбалансированное блюдо {phrase} для понятного домашнего меню."
    title = (
        getattr(recipe, "display_title", None) or getattr(recipe, "title", "") or ""
    ).strip()
    if title:
        return f"Домашнее блюдо «{title}» для понятного семейного меню."
    return "Домашнее блюдо для понятного семейного меню."


def public_description(recipe: Recipe) -> str:
    stored = (recipe.description or "").strip()
    if stored:
        return stored
    if not is_gold_v3_for_display(recipe):
        return ""
    fallback = build_description_fallback(recipe).strip()
    lowered = fallback.lower()
    if any(marker in lowered for marker in FORBIDDEN_FALLBACK_MARKERS):
        return "Домашнее блюдо для понятного семейного меню."
    if ENGLISH_PREFIX_RE.search(fallback):
        return "Домашнее блюдо для понятного семейного меню."
    return fallback
