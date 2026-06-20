"""Shopping list category taxonomy — PlanAm V1."""

from __future__ import annotations

from app.services.categories_v1 import (
    CANONICAL_SLUGS,
    CATEGORY_ORDER,
    DEFAULT_CATEGORY_SLUG,
    LEGACY_SLUG_MAP,
    normalize_category_slug,
)

FOOD_CATEGORIES: tuple[str, ...] = tuple(
    slug for slug in CATEGORY_ORDER if slug not in {"быт_уборка", "детские_товары", "для_питомцев"}
)

NON_FOOD_CATEGORIES: frozenset[str] = frozenset(
    {"быт_уборка", "детские_товары", "для_питомцев"}
)

CATEGORY_ALIASES: dict[str, str] = dict(LEGACY_SLUG_MAP)
for slug in CANONICAL_SLUGS:
    CATEGORY_ALIASES[slug] = slug

# Order matters: eggs and sauces/spices before vegetables.
CATEGORY_KEYWORDS: list[tuple[str, list[str]]] = [
    ("яйца", ["яйц"]),
    (
        "специи_соусы",
        [
            "соус",
            "паста томат",
            "томатн паст",
            "томатная паст",
            "майонез",
            "кетчуп",
            "аджик",
            "паприк",
            "куркум",
            "кориандр",
            "лавров",
            "приправ",
            "специ",
            "ванил",
            "сунел",
            "шафран",
            "хмели",
            "корица",
            "гвоздик",
            "мускат",
            "базилик суш",
            "орегано",
            "тимьян",
            "черн перец",
            "чёрн перец",
            "молот перец",
        ],
    ),
    (
        "овощи_зелень",
        [
            "морков",
            "лук",
            "картоф",
            "помидор",
            "огур",
            "капуст",
            "перец болг",
            "перец слад",
            "перец",
            "чеснок",
            "свекл",
            "кабач",
            "баклажан",
            "брокколи",
            "цукини",
            "овощ",
            "укроп",
            "петрушк",
            "кинз",
            "салат лист",
            "зелень",
        ],
    ),
    (
        "фрукты_ягоды",
        ["яблок", "банан", "ягод", "малин", "груш", "апельсин", "лимон", "фрукт", "виноград"],
    ),
    (
        "мясо_птица",
        [
            "курин",
            "куриц",
            "говядин",
            "свинин",
            "фарш",
            "индейк",
            "мяс",
            "котлет",
            "бедр",
            "грудк",
            "филе",
            "колбас",
            "сосиск",
        ],
    ),
    (
        "рыба_морепродукты",
        ["рыб", "лосос", "тунец", "минтай", "треск", "кревет", "морепродукт"],
    ),
    (
        "молочные",
        [
            "молок",
            "сыр",
            "творог",
            "йогурт",
            "кефир",
            "сливк",
            "сметан",
            "масло слив",
        ],
    ),
    (
        "крупы_макароны",
        [
            "рис",
            "греч",
            "овсян",
            "макарон",
            "спагет",
            "пенне",
            "киноа",
            "булгур",
            "кускус",
            "перлов",
            "пшено",
            "крупа",
        ],
    ),
    ("бакалея", ["мук", "сахар", "соль", "уксус", "масло раст", "масло подсол", "бульон", "орех"]),
    ("хлеб_выпечка", ["хлеб", "батон", "булк", "лаваш", "булочк", "выпеч"]),
    ("напитки", ["сок", "вода", "чай", "кофе", "напит", "вино", "пиво", "водк", "шампан"]),
    ("быт_уборка", ["салфет", "мыло", "порошок", "шампун", "средство", "губк", "уборк"]),
    ("детские_товары", ["подгуз", "соск", "детск"]),
    ("для_питомцев", ["корм", "наполнител", "для кот", "для соб", "питомц"]),
]


def normalize_category(raw: str | None) -> str:
    if not raw:
        return DEFAULT_CATEGORY_SLUG
    key = raw.strip().lower().replace(" ", "_")
    if key in CATEGORY_ALIASES:
        return CATEGORY_ALIASES[key]
    if key in CANONICAL_SLUGS:
        return key
    if key in NON_FOOD_CATEGORIES:
        return key
    return normalize_category_slug(key)


def infer_category(name: str, hint: str | None) -> str:
    if hint:
        category = normalize_category(hint)
        if category in NON_FOOD_CATEGORIES:
            return category
        if category != DEFAULT_CATEGORY_SLUG:
            return category
    lowered = name.lower()
    for cat, keywords in CATEGORY_KEYWORDS:
        if any(word in lowered for word in keywords):
            return cat
    return DEFAULT_CATEGORY_SLUG


def is_food_category(category: str) -> bool:
    return normalize_category(category) not in NON_FOOD_CATEGORIES
