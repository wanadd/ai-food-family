"""PLANAM Recipe V2 product taxonomy (English slugs).

Backend canonical map for shopping/pantry categories. UI may use Russian slugs
via ``legacy_shopping_slug()`` until full V2 migration.
"""

from __future__ import annotations

import re
from typing import Final

SHOPPING_CATEGORIES_V2: Final[tuple[str, ...]] = (
    "vegetables_greens",
    "fruits_berries",
    "mushrooms",
    "meat_poultry",
    "fish_seafood",
    "dairy",
    "eggs",
    "grains_pasta",
    "grocery",
    "sauces_spices",
    "drinks",
    "frozen",
    "other",
)

SHOPPING_CATEGORY_LABELS_RU: Final[dict[str, str]] = {
    "vegetables_greens": "Овощи и зелень",
    "fruits_berries": "Фрукты и ягоды",
    "mushrooms": "Грибы",
    "meat_poultry": "Мясо и птица",
    "fish_seafood": "Рыба и морепродукты",
    "dairy": "Молочные продукты",
    "eggs": "Яйца",
    "grains_pasta": "Крупы и макароны",
    "grocery": "Бакалея",
    "sauces_spices": "Соусы и специи",
    "drinks": "Напитки",
    "frozen": "Заморозка",
    "other": "Другое",
}

# V2 slug → legacy Russian slug used by shopping_categories / UI today.
V2_TO_LEGACY_SHOPPING: Final[dict[str, str]] = {
    "vegetables_greens": "овощи_зелень",
    "fruits_berries": "фрукты_ягоды",
    "mushrooms": "овощи_зелень",
    "meat_poultry": "мясо_птица",
    "fish_seafood": "рыба_морепродукты",
    "dairy": "молочные",
    "eggs": "яйца",
    "grains_pasta": "крупы_макароны",
    "grocery": "бакалея",
    "sauces_spices": "специи_соусы",
    "drinks": "напитки",
    "frozen": "заморозка",
    "other": "другое",
}

# Ordered keyword rules: first match wins.
_CATEGORY_RULES: Final[tuple[tuple[str, tuple[str, ...]], ...]] = (
    ("mushrooms", ("гриб", "шампиньон", "вешенк", "портобелло", "лисичк", "опят", "сыроежк")),
    ("eggs", ("яйц",)),
    ("fish_seafood", ("лосос", "треск", "тунец", "рыб", "кревет", "кальмар", "мидии", "икра", "форел")),
    ("meat_poultry", ("куриц", "курин", "индейк", "утк", "филе птиц", "говядин", "телят", "баран", "свинин", "фарш", "бекон", "колбас")),
    ("dairy", ("молок", "творог", "сыр", "йогурт", "кефир", "сметан", "сливк", "ряженк", "брынз")),
    ("grains_pasta", ("гречк", "рис", "овсян", "перлов", "булгур", "киноа", "макарон", "паста", "спагетти", "лапш", "пшено", "манк")),
    ("fruits_berries", ("яблок", "груш", "банан", "апельсин", "лимон", "ягод", "клубник", "малин", "черник", "виноград", "персик", "слив")),
    ("vegetables_greens", ("картоф", "морков", "лук", "чеснок", "капуст", "огур", "помидор", "томат", "перец болгар", "кабач", "баклаж", "укроп", "петруш", "кинз", "салат", "шпинат", "зелень", "сельдер", "свекл", "тыкв", "редис", "редьк")),
    ("sauces_spices", ("соус", "кетчуп", "горчиц", "уксус", "паприк", "перец черн", "перец бел", "корианд", "куркум", "базилик", "орегано", "тимьян", "лавров", "корица", "ванил", "имбир", "чили", "аджик", "томатная паст")),
    ("grocery", ("мёд", "мед ", " мед", "оливковое масло", "масло растительное", "масло подсолнеч", "мука", "сахар", "соль", "дрожж", "крахмал", "масло сливоч", "масло кунжут", "крупа", "чечев", "фасол", "нут", "горох", "орех", "семеч", "изюм", "сухофрукт")),
    ("drinks", ("вода", "сок", "чай", "кофе", "компот", "морс", "какао")),
    ("frozen", ("заморож", "frozen")),
)

_WORD_RE = re.compile(r"[a-zа-яё0-9]+", re.IGNORECASE)


def _normalize_name(name: str) -> str:
    return " ".join(_WORD_RE.findall(name.lower().strip()))


def infer_shopping_category_v2(name: str, hint: str | None = None) -> str:
    """Map ingredient display/canonical name to V2 shopping category slug."""
    if hint and hint in SHOPPING_CATEGORIES_V2:
        return hint

    normalized = _normalize_name(name)
    if not normalized:
        return "other"

    for slug, keywords in _CATEGORY_RULES:
        if any(keyword in normalized for keyword in keywords):
            return slug

    return "other"


def legacy_shopping_slug(v2_slug: str) -> str:
    """Convert V2 English slug to legacy Russian slug for existing pipelines."""
    if v2_slug not in SHOPPING_CATEGORIES_V2:
        return V2_TO_LEGACY_SHOPPING["other"]
    return V2_TO_LEGACY_SHOPPING[v2_slug]


def pantry_category_slug(shopping_slug: str) -> str:
    """Pantry uses the same V2 taxonomy for Stage 1."""
    if shopping_slug in SHOPPING_CATEGORIES_V2:
        return shopping_slug
    return "other"
