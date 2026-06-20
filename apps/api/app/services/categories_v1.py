"""PlanAm V1 shopping categories — backend source of truth (mirrors web categories-v1.ts)."""

from __future__ import annotations

FORBIDDEN_CATEGORY_SLUG = "продукты"
DEFAULT_CATEGORY_SLUG = "другое"

# (slug, label, icon, is_food)
SYSTEM_CATEGORIES_V1: tuple[tuple[str, str, str, bool], ...] = (
    ("овощи_зелень", "Овощи и зелень", "🥬", True),
    ("фрукты_ягоды", "Фрукты и ягоды", "🍓", True),
    ("мясо_птица", "Мясо и птица", "🥩", True),
    ("рыба_морепродукты", "Рыба и морепродукты", "🐟", True),
    ("молочные", "Молочные продукты", "🥛", True),
    ("яйца", "Яйца", "🥚", True),
    ("хлеб_выпечка", "Хлеб и выпечка", "🍞", True),
    ("крупы_макароны", "Крупы и макароны", "🌾", True),
    ("бакалея", "Бакалея", "🫙", True),
    ("специи_соусы", "Специи и соусы", "🧂", True),
    ("напитки", "Напитки", "🥤", True),
    ("быт_уборка", "Быт и уборка", "🧴", False),
    ("детские_товары", "Детские товары", "🧸", False),
    ("для_питомцев", "Для питомцев", "🐾", False),
    ("другое", "Другое", "📦", True),
)

CANONICAL_SLUGS: frozenset[str] = frozenset(row[0] for row in SYSTEM_CATEGORIES_V1)

CATEGORY_ORDER: list[str] = [row[0] for row in SYSTEM_CATEGORIES_V1]

# Data migration + runtime normalization for legacy slugs.
LEGACY_SLUG_MAP: dict[str, str] = {
    FORBIDDEN_CATEGORY_SLUG: DEFAULT_CATEGORY_SLUG,
    "овощи": "овощи_зелень",
    "зелень": "овощи_зелень",
    "фрукты": "фрукты_ягоды",
    "ягоды": "фрукты_ягоды",
    "мясо": "мясо_птица",
    "птица": "мясо_птица",
    "рыба": "рыба_морепродукты",
    "морепродукты": "рыба_морепродукты",
    "молочное": "молочные",
    "молочные_продукты": "молочные",
    "крупы": "крупы_макароны",
    "макароны": "крупы_макароны",
    "специи": "специи_соусы",
    "соусы": "специи_соусы",
    "масла": "специи_соусы",
    "хлеб": "хлеб_выпечка",
    "выпечка": "хлеб_выпечка",
    "заморозка": "бакалея",
    "сладости": "бакалея",
    "дом_и_химия": "быт_уборка",
    "бытовые": "быт_уборка",
    "хозтовары": "быт_уборка",
    "животные": "для_питомцев",
    "питомцы": "для_питомцев",
    "детское": "детские_товары",
    "детские": "детские_товары",
    "ребенку": "детские_товары",
    "ребёнку": "детские_товары",
    "аптека": DEFAULT_CATEGORY_SLUG,
    "ремонт": DEFAULT_CATEGORY_SLUG,
    "подарки": DEFAULT_CATEGORY_SLUG,
    "алкоголь": DEFAULT_CATEGORY_SLUG,
    "бобовые": "бакалея",
    "другое_продуктовое": DEFAULT_CATEGORY_SLUG,
    "прочее": DEFAULT_CATEGORY_SLUG,
    "products": DEFAULT_CATEGORY_SLUG,
    "vegetables": "овощи_зелень",
    "fruit": "фрукты_ягоды",
    "fruits": "фрукты_ягоды",
    "meat": "мясо_птица",
    "fish": "рыба_морепродукты",
    "seafood": "рыба_морепродукты",
    "dairy": "молочные",
    "eggs": "яйца",
    "grains": "крупы_макароны",
    "grocery": "бакалея",
    "spices": "специи_соусы",
    "sauces": "специи_соусы",
    "herbs": "овощи_зелень",
    "legumes": "бакалея",
    "drinks": "напитки",
    "alcohol": DEFAULT_CATEGORY_SLUG,
    "bread": "хлеб_выпечка",
    "frozen": "бакалея",
    "other": DEFAULT_CATEGORY_SLUG,
    "other_food": DEFAULT_CATEGORY_SLUG,
    "дом и химия": "быт_уборка",
    "одежда и обувь": DEFAULT_CATEGORY_SLUG,
    "одежда_и_обувь": DEFAULT_CATEGORY_SLUG,
}

# Slugs that must not exist in DB after migration (non-V1 system categories).
DEPRECATED_SYSTEM_SLUGS: frozenset[str] = frozenset(
    {
        FORBIDDEN_CATEGORY_SLUG,
        "заморозка",
        "сладости",
    }
)


def map_legacy_slug(slug: str | None) -> str | None:
    if not slug:
        return None
    key = slug.strip().lower().replace(" ", "_")
    if not key:
        return None
    if key in CANONICAL_SLUGS:
        return key
    if key in LEGACY_SLUG_MAP:
        return LEGACY_SLUG_MAP[key]
    return None


def normalize_category_slug(slug: str | None) -> str:
    mapped = map_legacy_slug(slug)
    if mapped:
        return mapped
    return DEFAULT_CATEGORY_SLUG
