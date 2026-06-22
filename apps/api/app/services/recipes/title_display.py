"""User-facing recipe title helpers (response normalization only; no DB writes)."""

from __future__ import annotations

import re

from app.models.recipe import Recipe
from app.services.recipes.description_display import (
    UPGRADED_GOLD_V3_RECIPE_IDS,
    is_gold_v3_for_display,
)

ENGLISH_TITLE_PREFIX_RE = re.compile(
    r"^\s*(high protein|pro weight loss|pre-workout|post-workout|meal prep)\s*:?\s*",
    re.I,
)

CATEGORY_PREFIX_RE = re.compile(
    r"^\s*(?:"
    r"лёгкий|легкий|семейный|детский|"
    r"для похудения|для спортсменов"
    r")\s+(?:завтрак|обед|ужин|перекус)\s*:\s*",
    re.I,
)

MARKETING_PREFIX_RE = re.compile(
    r"^\s*(?:быстрый|лёгкий|легкий|энергетический|вегетарианская|вегетарианский)\s+",
    re.I,
)

RELIGIOUS_TITLE_TERMS = (
    "халяль",
    "кошер",
    "постный",
    "православ",
    "мусульман",
)

ENGLISH_TITLE_TERMS = (
    "смузи",
    "боул",
    "стир-фрай",
    "стир фрай",
    "тост",
    "high protein",
    "pre-workout",
    "post-workout",
    "meal prep",
    "pro weight",
)

RELIGIOUS_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"халяль[-\s]*", re.I), ""),
    (re.compile(r"кошер[-\s]*", re.I), ""),
    (re.compile(r"постный\s+", re.I), ""),
    (re.compile(r"православн\w*\s+", re.I), ""),
    (re.compile(r"мусульман\w*\s+", re.I), ""),
)

PHRASE_REPLACEMENTS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"творожная\s+боул", re.I), "творог"),
    (re.compile(r"смузи[-\s]*боул", re.I), "банановый завтрак"),
    (re.compile(r"\bтост\b", re.I), "хлеб"),
    (re.compile(r"стир[-\s]*фрай\s+с\s+курицей", re.I), "курица с овощами на сковороде"),
    (re.compile(r"вегетарианская\s+паста", re.I), "паста"),
    (re.compile(r"энергетический\s+перекус", re.I), "перекус"),
    (re.compile(r"\s+для\s+детей\b", re.I), ""),
)

EXACT_TITLE_OVERRIDES: dict[str, str] = {
    "халяль-курица с булгуром": "Курица с булгуром",
    "постный гороховый суп": "Гороховый суп с овощами",
    "смузи-боул с бананом и орехами": "Банановый завтрак с орехами",
    "творожная боул с фруктами": "Творог с фруктами",
    "тост с авокадо и яйцом": "Хлеб с авокадо и яйцом",
    "быстрый стир-фрай с курицей": "Курица с овощами на сковороде",
    "лёгкий ужин: салат с тунцом": "Салат с тунцом и овощами",
    "легкий ужин: салат с тунцом": "Салат с тунцом и овощами",
    "семейный ужин: тефтели в томатном соусе": "Тефтели в томатном соусе",
    "детский перекус: кефир с печеньем": "Кефир с печеньем",
    "лёгкий овощной суп": "Овощной суп",
    "легкий овощной суп": "Овощной суп",
    "вегетарианская паста с грибами": "Паста с грибами",
    "энергетический перекус с орехами": "Орехи с курагой и мёдом",
    "рисовая каша на молоке для детей": "Рисовая каша на молоке",
}


def _normalize_key(title: str) -> str:
    return re.sub(r"\s+", " ", str(title or "").strip().lower())


def _collapse_whitespace(title: str) -> str:
    text = re.sub(r"\s+", " ", str(title or "")).strip()
    text = re.sub(r"^[\s\-—:]+", "", text)
    text = re.sub(r"[\s\-—:]+$", "", text)
    return text.strip()


def public_recipe_title(title: str, recipe_id: int | None = None) -> str:
    """Return a clean Russian user-facing title without mutating stored data."""
    del recipe_id  # reserved for future per-id overrides
    raw = _collapse_whitespace(title)
    if not raw:
        return "Домашнее блюдо"

    override = EXACT_TITLE_OVERRIDES.get(_normalize_key(raw))
    if override:
        return override

    cleaned = CATEGORY_PREFIX_RE.sub("", raw)
    cleaned = ENGLISH_TITLE_PREFIX_RE.sub("", cleaned)
    cleaned = MARKETING_PREFIX_RE.sub("", cleaned)
    for pattern, replacement in RELIGIOUS_PATTERNS:
        cleaned = pattern.sub(replacement, cleaned)
    for pattern, replacement in PHRASE_REPLACEMENTS:
        cleaned = pattern.sub(replacement, cleaned)
    cleaned = _collapse_whitespace(cleaned)

    override = EXACT_TITLE_OVERRIDES.get(_normalize_key(cleaned))
    if override:
        return override

    if not cleaned:
        return "Домашнее блюдо"
    return cleaned[0].upper() + cleaned[1:] if len(cleaned) > 1 else cleaned.upper()


def public_recipe_title_for_recipe(recipe: Recipe) -> str:
    raw = (recipe.display_title or recipe.title or "").strip()
    if not raw:
        return "Домашнее блюдо"
    if not should_clean_recipe_title(recipe):
        return raw
    return public_recipe_title(raw, recipe_id=int(recipe.id) if recipe.id is not None else None)


def should_clean_recipe_title(recipe: Recipe) -> bool:
    if recipe.id is not None and int(recipe.id) in UPGRADED_GOLD_V3_RECIPE_IDS:
        return True
    return is_gold_v3_for_display(recipe)


def _contains_term(text: str, term: str) -> bool:
    if " " in term.strip():
        return term.lower() in text.lower()
    return re.search(rf"(?<![\w-]){re.escape(term)}(?![\w-])", text, re.I) is not None


def title_has_category_prefix(title: str) -> bool:
    return bool(CATEGORY_PREFIX_RE.search(str(title or "")))


def analyze_title_cleanliness(title: str) -> dict[str, list[str]]:
    value = str(title or "")
    lowered = value.lower()
    return {
        "religious": [term for term in RELIGIOUS_TITLE_TERMS if _contains_term(lowered, term)],
        "english": [term for term in ENGLISH_TITLE_TERMS if _contains_term(lowered, term)],
        "category_prefix": ["category_prefix"] if title_has_category_prefix(value) else [],
    }


def count_bad_title_terms(title: str) -> dict[str, int]:
    issues = analyze_title_cleanliness(title)
    religious = len(issues["religious"])
    english = len(issues["english"])
    category_prefix = len(issues["category_prefix"])
    return {
        "bad_title_term_count": religious + english + category_prefix,
        "religious_title_marker_count": religious,
        "english_title_marker_count": english,
        "category_prefix_title_count": category_prefix,
    }


def title_cleanliness_blockers(title: str) -> list[str]:
    counts = count_bad_title_terms(title)
    blockers: list[str] = []
    if counts["religious_title_marker_count"]:
        blockers.append("religious_title_marker")
    if counts["english_title_marker_count"]:
        blockers.append("english_title_marker")
    if counts["category_prefix_title_count"]:
        blockers.append("category_prefix_title")
    if ENGLISH_TITLE_PREFIX_RE.search(title or ""):
        blockers.append("english_title_prefix")
    return blockers
