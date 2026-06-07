#!/usr/bin/env python3
"""Canonical products + unit/quantity normalization rules for PLANAM V1.

Source of truth for the normalization stage. Pure data + pure functions — no DB
access here, so it is trivially testable and reusable by the dry-run/commit
normalizer.

Design notes:
* The current catalog has 0 spelling/word-order variant groups, so canonical
  names are the existing names (identity). Renaming is therefore NOT done here;
  a canonical product = existing name + assigned shopping category + flags.
* Ambiguous head nouns (e.g. "перец") are resolved by listing each product in
  its correct category (перец чёрный -> специи_соусы, перец болгарский ->
  овощи_зелень), which is exactly what canonical products should do.
* Generic names (овощи, специи, ...) get a shopping category but are flagged
  ``generic`` and ``nutrition_ready=False``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

DEFAULT_CATEGORY = "другое"

# Canonical shopping categories (mirror categories_v1.SYSTEM_CATEGORIES_V1).
CANONICAL_CATEGORIES = frozenset(
    {
        "овощи_зелень",
        "фрукты_ягоды",
        "мясо_птица",
        "рыба_морепродукты",
        "молочные",
        "яйца",
        "хлеб_выпечка",
        "крупы_макароны",
        "бакалея",
        "специи_соусы",
        "напитки",
        "быт_уборка",
        "детские_товары",
        "для_питомцев",
        "другое",
    }
)

# Names that are too generic for a single product / nutrition profile, but can
# still carry a shopping category.
GENERIC_NAMES = frozenset(
    {
        "овощи",
        "зелень",
        "специи",
        "приправа",
        "приправы",
        "мясо",
        "рыба",
        "сыр",
        "грибы",
        "соус",
        "бульон",
        "ягода",
        "ягоды",
        "орехи",
        "сухофрукты",
        "ассорти овощное",
        "фрукты",
    }
)

# category -> canonical product names (lowercase, ё normalized to е on match)
CATEGORY_PRODUCTS: dict[str, tuple[str, ...]] = {
    "овощи_зелень": (
        "лук репчатый", "картофель", "чеснок", "морковь", "перец болгарский",
        "помидор", "петрушка", "зелень", "огурец", "укроп", "грибы", "шампиньоны",
        "листья салата", "горошек зеленый", "лук красный", "помидоры черри",
        "базилик", "баклажан", "свекла", "капуста белокочанная", "кукуруза",
        "лук зеленый", "капуста пекинская", "авокадо", "лук-порей",
        "сельдерей черешковый", "кабачок", "лук белый", "руккола", "репа",
        "редька", "пастернак", "сельдерей корневой", "капуста цветная",
        "капуста кольраби", "капуста брюссельская", "шпинат", "мята", "овощи",
        "ассорти овощное", "тыква", "кинза", "опята", "вешенки", "брокколи",
        "перец сладкий", "перец сладкий красный", "перец сладкий желтый",
        "перец чили", "перец красный жгучий", "фасоль стручковая",
        "огурец соленый",
    ),
    "фрукты_ягоды": (
        "яблоко", "лимон", "ананас", "банан", "виноград", "апельсин",
        "клубника", "абрикос", "малина", "киви", "груша", "гранат", "ягода",
    ),
    "мясо_птица": (
        "филе куриное", "курица", "фарш мясной", "грудка куриная", "свинина",
        "ветчина", "бедро куриное", "бекон", "печень куриная", "окорочок куриный",
        "говядина", "сало", "фарш куриный", "голень куриная", "шпиг", "баранина",
        "сосиска", "печень говяжья", "колбаса", "сердечки куриные",
        "крылья куриные", "ребра свиные", "фрикадельки", "балык", "мясо",
    ),
    "рыба_морепродукты": (
        "сельдь", "филе рыбное", "рыба", "горбуша", "креветки", "кальмар",
        "зубатка", "килька", "тунец", "шпроты", "семга", "треска", "кожа рыбная",
        "угорь", "кета", "лосось", "анчоусы", "крабовые палочки", "капуста морская",
    ),
    "молочные": (
        "сыр твердый", "сметана", "молоко", "творог", "сыр плавленый", "сливки",
        "пармезан", "йогурт", "сыр творожный", "сыр голландский", "сыр колбасный",
        "сыр полутвердый", "сыр мягкий", "сыр сулугуни", "масло сливочное",
        "напиток кисломолочный", "сыр", "романо",
    ),
    "яйца": (
        "яйцо куриное", "желток яичный", "яйцо перепелиное", "белок яичный",
    ),
    "хлеб_выпечка": (
        "сухари панировочные", "хлеб", "хлебцы", "корж", "блин", "булочка", "маца",
    ),
    "крупы_макароны": (
        "рис", "крупа гречневая", "макаронные изделия", "крупа перловая",
        "вермишель", "крупа манная", "спагетти", "мука гречневая", "пшено",
        "хлопья овсяные", "хлопья гречневые", "лапша", "кус-кус", "маш", "нут",
        "отруби",
    ),
    "бакалея": (
        "масло растительное", "масло оливковое", "масло подсолнечное", "сахар",
        "мука пшеничная", "мед", "уксус", "томатная паста", "сахар коричневый",
        "крахмал кукурузный", "крахмал картофельный", "какао-порошок", "изюм",
        "чернослив", "орехи грецкие", "кунжут", "дрожжи", "сода", "ванилин",
        "ванильный сахар", "маслины", "оливки зеленые", "мак", "халва", "финик",
        "сухофрукты", "арахис", "орехи", "томаты в собственном соку",
        "томаты пассерованные", "молоко кокосовое", "масло кунжутное", "тофу",
        "пюре картофельное", "фасоль",
    ),
    "специи_соусы": (
        "соль", "перец черный", "соевый соус", "приправа", "специи",
        "сок лимонный", "горчица", "лист лавровый", "кориандр", "перец душистый",
        "куркума", "смесь перцев", "хмели-сунели", "паприка сладкая", "кумин",
        "шафран", "корица", "тимьян", "майоран", "шалфей", "зира", "карри",
        "кардамон", "орегано", "эстрагон", "тмин", "пажитник", "уцхо-сунели",
        "табаско", "ткемали", "кетчуп", "соус", "хрен", "перец белый",
        "перец кайен", "цедра лимона", "орех мускатный", "майонез", "бальзамик",
        "бульон",
    ),
    "напитки": (
        "вода", "сок", "сок апельсиновый", "сок томатный",
    ),
    "детские_товары": (
        "детское питание", "пюре фруктовое",
    ),
}

# Optional synonym aliases (raw -> canonical). Currently identity-only; kept for
# future spelling synonyms without code changes.
ALIASES: dict[str, str] = {}

# ---------------------------------------------------------------------------
# Units
# ---------------------------------------------------------------------------

CANONICAL_UNITS = frozenset(
    {"г", "кг", "мл", "л", "шт", "ст.л.", "ч.л.", "стакан", "зубчик", "щепотка", "упаковка"}
)

UNIT_ALIASES: dict[str, str] = {
    "гр": "г", "гр.": "г", "г.": "г", "грамм": "г", "граммов": "г", "грамма": "г",
    "килограмм": "кг", "кг.": "кг",
    "мл.": "мл", "л.": "л", "литр": "л", "литра": "л",
    "ст.л": "ст.л.", "ст. л.": "ст.л.", "стл": "ст.л.", "ст.ложка": "ст.л.",
    "столовая ложка": "ст.л.", "столовых ложек": "ст.л.", "ложка": "ст.л.",
    "ложки": "ст.л.",
    "ч.л": "ч.л.", "ч. л.": "ч.л.", "чайная ложка": "ч.л.", "чл": "ч.л.",
    "шт.": "шт", "штук": "шт", "штука": "шт", "штуки": "шт",
    "зуб.": "зубчик", "зубчика": "зубчик", "зубчиков": "зубчик",
    "пакетик": "упаковка", "пакет": "упаковка", "пач.": "упаковка",
    "пачка": "упаковка", "банка": "упаковка",
    "стак.": "стакан",
    "щепотку": "щепотка",
}

NON_NUMERIC_QUANTITY = frozenset(
    {
        "", "0", "по вкусу", "немного", "щепотка", "щепотку", "пара",
        "несколько", "горсть", "на глаз", "чуть", "капля", "по желанию",
    }
)

_QUANTITY_RE = re.compile(r"^\d+([.,]\d+)?([/-]\d+([.,]\d+)?)?$")
_UNIT_IN_TEXT_RE = re.compile(
    r"(ст\.?\s*л\.?|ч\.?\s*л\.?|кг|мл|г|л|шт|стакан|зубчик|щепотк\w*|упаковк\w*)",
    re.IGNORECASE,
)


def _norm(value: str) -> str:
    return (value or "").strip().lower().replace("ё", "е")


@dataclass
class CanonicalProduct:
    canonical_name: str
    category: str
    generic: bool
    nutrition_ready: bool


def build_lookup() -> dict[str, str]:
    """name(normalized) -> category."""
    lookup: dict[str, str] = {}
    for category, names in CATEGORY_PRODUCTS.items():
        for name in names:
            lookup[_norm(name)] = category
    return lookup


_LOOKUP = build_lookup()


def resolve_product(name: str) -> CanonicalProduct:
    """Resolve a raw ingredient name to a canonical product (no renaming)."""
    raw = (name or "").strip()
    key = _norm(raw)
    key = _norm(ALIASES.get(key, key))
    category = _LOOKUP.get(key, DEFAULT_CATEGORY)
    generic = key in GENERIC_NAMES
    nutrition_ready = bool(raw) and not generic
    return CanonicalProduct(
        canonical_name=raw,
        category=category,
        generic=generic,
        nutrition_ready=nutrition_ready,
    )


def is_valid_quantity(quantity: str) -> bool:
    value = _norm(quantity)
    if value in NON_NUMERIC_QUANTITY:
        return False
    return bool(_QUANTITY_RE.match(value))


def normalize_quantity(quantity: str) -> tuple[str, bool]:
    """Return (normalized_quantity, to_taste).

    "по вкусу"/"немного"/empty/0 -> ("", to_taste=True): never invent numbers.
    Valid numeric -> (cleaned, False). Other -> (original_trimmed, False).
    """
    value = (quantity or "").strip()
    low = _norm(value)
    if low in NON_NUMERIC_QUANTITY:
        return "", True
    if _QUANTITY_RE.match(low):
        return value.replace(",", "."), False
    return value, False


def normalize_unit(unit: str, quantity: str = "") -> tuple[str, bool]:
    """Return (canonical_unit, changed).

    Handles dirty spellings and junk like "...4 ст.л." (quantity bled into unit)
    by extracting a known unit token. Empty unit defaults to "шт".
    """
    raw = (unit or "").strip()
    low = _norm(raw)
    if not low:
        return "шт", raw != "шт"
    if low in CANONICAL_UNITS:
        return low, low != raw
    if low in UNIT_ALIASES:
        return UNIT_ALIASES[low], True
    match = _UNIT_IN_TEXT_RE.search(low)
    if match:
        token = match.group(1).replace(" ", "")
        token = token.replace("ст.л", "ст.л.").replace("ч.л", "ч.л.")
        token = re.sub(r"\.\.+", ".", token)
        if token.startswith("щепотк"):
            token = "щепотка"
        if token.startswith("упаковк"):
            token = "упаковка"
        canonical = UNIT_ALIASES.get(token, token)
        if canonical in CANONICAL_UNITS:
            return canonical, True
    return raw, False
