"""User-facing recipe step helpers (response normalization only; no DB writes)."""

from __future__ import annotations

import re
from typing import Any


GENERIC_FISH_STEP_FIX_IDS = frozenset({235, 239, 242, 245, 246})
FISH_ALIASES = ("рыб", "лосос", "треск", "тунец", "кревет", "морепродукт")

STEP_OVERRIDES_BY_ID: dict[int, dict[int, str]] = {
    235: {
        0: "Подготовьте филе индейки, гречку и морковь: индейку нарежьте порционными кусками, гречку промойте.",
    },
    239: {
        0: "Подготовьте куриное бедро, булгур, лук и паприку: курицу нарежьте порционными кусками, булгур промойте.",
    },
    242: {
        0: "Подготовьте говядину и брокколи: мясо нарежьте тонкими полосками, брокколи разделите на соцветия.",
    },
    245: {
        0: "Подготовьте филе индейки и овощи: индейку нарежьте порционными кусками, овощи нарежьте удобными ломтиками.",
    },
    246: {
        0: "Подготовьте куриное филе и овощи: курицу нарежьте тонкими полосками, овощи нарежьте для быстрой обжарки.",
    },
}

GENERIC_ABSENT_FISH_RE = re.compile(
    r"мясо,\s*рыбу\s+или\s+овощи\s+нарежьте\s+порционными\s+кусками",
    re.I,
)


def _contains_any(text: str, words: tuple[str, ...]) -> bool:
    lowered = text.lower()
    return any(word in lowered for word in words)


def _ingredient_blob(ingredients: list[Any]) -> str:
    names: list[str] = []
    for item in ingredients:
        if isinstance(item, dict):
            names.append(str(item.get("name") or item.get("display_name") or ""))
        else:
            names.append(str(item or ""))
    return " ".join(names).lower()


def public_recipe_steps(
    recipe_id: int | None,
    steps: list[str],
    ingredients: list[Any] | None = None,
) -> list[str]:
    """Return clean user-facing steps without mutating stored data."""
    ingredients = ingredients or []
    fish_present = _contains_any(_ingredient_blob(ingredients), FISH_ALIASES)
    overrides = STEP_OVERRIDES_BY_ID.get(int(recipe_id)) if recipe_id is not None else None
    cleaned: list[str] = []
    for index, step in enumerate(steps):
        text = str(step or "").strip()
        if overrides and index in overrides:
            cleaned.append(overrides[index])
            continue
        if not fish_present and GENERIC_ABSENT_FISH_RE.search(text):
            text = GENERIC_ABSENT_FISH_RE.sub(
                "основные ингредиенты нарежьте порционными кусками",
                text,
            )
        cleaned.append(text)
    return cleaned


def step_has_absent_fish_reference(step: str, ingredients: list[Any], title: str = "") -> bool:
    """True when a user-facing step mentions fish but the dish is not fish/seafood."""
    text = str(step or "").lower()
    if "рыб" not in text:
        return False
    dish_blob = f"{_ingredient_blob(ingredients)} {title}".lower()
    return not _contains_any(dish_blob, FISH_ALIASES)
