"""Safe postprocess normalization for Gold V3 generated recipes (Stage F.1)."""

from __future__ import annotations

import copy
import re
from typing import Any

from app.nutrition.restrictions_catalog import get_restriction_definition
from app.recipes.recipe_gold_v3_schema import ALLOWED_INGREDIENT_CATEGORIES, ALLOWED_UNITS

# Preferred units for AI generation (subset of ALLOWED_UNITS).
PROMPT_ALLOWED_UNITS: tuple[str, ...] = ("г", "мл", "шт", "ч.л.", "ст.л.", "по вкусу")

MEAT_MARKERS = (
    "мясо",
    "куриц",
    "курин",
    "говядин",
    "свинин",
    "баранин",
    "индейк",
    "бекон",
    "ветчин",
    "фарш",
    "рыб",
    "лосос",
    "тунец",
    "треск",
    "семг",
    "кревет",
)
DAIRY_EGG_MARKERS = ("молок", "сливк", "сыр", "творог", "йогурт", "сметан", "яйц", "желток")
PORK_MARKERS = ("свинин", "свин", "бекон", "ветчин", "сало", "карбонат")
ALCOHOL_MARKERS = (
    "алкогол",
    "вино",
    "пиво",
    "водк",
    "коньяк",
    "ром",
    "ликер",
    "ликёр",
    "настойк",
)

_UNIT_ALIASES: dict[str, str] = {
    "шт.": "шт",
    "штук": "шт",
    "штука": "шт",
    "штуки": "шт",
    "ст. л.": "ст.л.",
    "ст.л": "ст.л.",
    "ст. ложка": "ст.л.",
    "ст. ложки": "ст.л.",
    "ст ложка": "ст.л.",
    "ст ложки": "ст.л.",
    "столовая ложка": "ст.л.",
    "столовые ложки": "ст.л.",
    "ч. л.": "ч.л.",
    "ч.л": "ч.л.",
    "ч. ложка": "ч.л.",
    "ч. ложки": "ч.л.",
    "ч ложка": "ч.л.",
    "ч ложки": "ч.л.",
    "чайная ложка": "ч.л.",
    "чайные ложки": "ч.л.",
    "гр": "г",
    "гр.": "г",
    "грамм": "г",
    "граммы": "г",
    "мл.": "мл",
    "литр": "л",
    "л.": "л",
    "кг.": "кг",
    "ложка": "ч.л.",
    "ложки": "ч.л.",
    "стакан": "мл",
    "стакана": "мл",
    "стаканы": "мл",
    "зубчик": "шт",
    "зубчика": "шт",
    "зубчики": "шт",
    "пучок": "шт",
    "пучка": "шт",
    "щепотка": "ч.л.",
    "щепотки": "ч.л.",
}

_CATEGORY_ALIASES: dict[str, str] = {
    "жиры": "масла/соусы",
    "масла": "масла/соусы",
    "масло": "масла/соусы",
    "соусы": "масла/соусы",
    "мясо птицы": "мясо_птица",
    "птица": "мясо_птица",
    "приправы": "специи",
    "специя": "специи",
    "жидкость": "напитки",
    "вода": "напитки",
    "другие": "прочее",
    "другое": "прочее",
    "овощи и зелень": "овощи",
    "зелень": "овощи",
    "молочные": "молочные продукты",
    "молочное": "молочные продукты",
    "макароны": "паста",
    "макароны": "паста",
    "фрукты": "фрукты/ягоды",
    "ягоды": "фрукты/ягоды",
    "крупа": "крупы",
    "крупы/злаки": "крупы",
    "выпечка": "выпечка/тесто",
    "тесто": "выпечка/тесто",
    "морепродукт": "морепродукты",
    "орех": "орехи",
    "бобовые/бобовые": "бобовые",
}


def _normalize_unit(unit: str) -> str:
    raw = unit.strip()
    key = raw.lower().replace("  ", " ")
    return _UNIT_ALIASES.get(key, raw)


def _normalize_category(category: str) -> str:
    raw = category.strip()
    key = raw.lower().replace("  ", " ")
    mapped = _CATEGORY_ALIASES.get(key, raw)
    if mapped in ALLOWED_INGREDIENT_CATEGORIES:
        return mapped
    # fuzzy: replace spaces with underscore for groups like "мясо_птица"
    underscored = key.replace(" ", "_")
    if underscored in ALLOWED_INGREDIENT_CATEGORIES:
        return underscored
    return mapped


def _ingredient_blob(recipe: dict[str, Any]) -> str:
    parts: list[str] = []
    for ing in recipe.get("ingredients") or []:
        if isinstance(ing, dict):
            parts.append(str(ing.get("name", "")))
            parts.append(str(ing.get("shopping_name", "")))
    return " ".join(parts).lower()


def _text_has_any(text: str, markers: tuple[str, ...]) -> bool:
    lower = text.lower()
    return any(m in lower for m in markers)


def _default_shopping_name(name: str) -> str:
    cleaned = re.sub(r"\s+", " ", name.strip())
    # Drop leading quantity words
    cleaned = re.sub(
        r"^(свеж(ий|ая|ие|их)|молот(ый|ая|ые)|рублен(ый|ая|ые)|"
        r"нарезанн(ый|ая|ые)|крупн(ый|ая|ые)|мелк(ий|ая|ие))\s+",
        "",
        cleaned,
        flags=re.I,
    )
    return cleaned.strip() or name.strip()


def _format_display_amount(amount: Any, unit: str) -> str:
    try:
        val = float(amount)
        if val == int(val):
            num = str(int(val))
        else:
            num = str(round(val, 1)).replace(".", ",")
    except (TypeError, ValueError):
        num = str(amount)
    if unit == "по вкусу":
        return "по вкусу"
    return f"{num} {unit}"


def _estimate_nutrition_defaults(recipe: dict[str, Any]) -> tuple[float, float, float]:
    category = str(recipe.get("category") or "main")
    if category in {"dessert", "snack"}:
        return 3.0, 1.0, 12.0
    if category in {"salad", "soup"}:
        return 5.0, 1.2, 4.0
    if category == "side":
        return 4.0, 1.0, 3.0
    return 4.0, 1.4, 5.0


def _cleanup_restriction_keys(recipe: dict[str, Any]) -> list[str]:
    blob = _ingredient_blob(recipe)
    keys = [k for k in (recipe.get("restriction_keys") or []) if get_restriction_definition(k)]
    diet_tags = [str(t).lower() for t in (recipe.get("diet_tags") or [])]
    remove: set[str] = set()

    has_meat = _text_has_any(blob, MEAT_MARKERS)
    has_dairy_egg = _text_has_any(blob, DAIRY_EGG_MARKERS)
    has_pork = _text_has_any(blob, PORK_MARKERS)
    has_alcohol = _text_has_any(blob, ALCOHOL_MARKERS)

    if has_meat:
        remove.update({"vegan", "vegetarian", "pescatarian"})
    if has_dairy_egg:
        remove.update({"vegan", "lactose_free", "no_milk"})
    if _text_has_any(blob, ("яйц", "желток")):
        remove.update({"vegan", "no_eggs"})
    if has_pork:
        remove.update({"no_pork", "halal", "kosher"})
    if has_alcohol:
        remove.add("no_alcohol")
    if "vegan" in diet_tags and has_meat:
        remove.add("vegan")
    if "vegetarian" in diet_tags and has_meat:
        remove.add("vegetarian")

    cleaned = [k for k in keys if k not in remove]
    # Also drop vegan/vegetarian from diet_tags if contradicted
    if has_meat and isinstance(recipe.get("diet_tags"), list):
        recipe["diet_tags"] = [
            t for t in recipe["diet_tags"] if str(t).lower() not in {"vegan", "vegetarian"}
        ]
    return cleaned


def postprocess_generated_recipe(recipe: dict[str, Any]) -> dict[str, Any]:
    """Fix safe formal issues before validation (does not change recipe meaning)."""
    out = copy.deepcopy(recipe)

    for ing in out.get("ingredients") or []:
        if not isinstance(ing, dict):
            continue
        unit = _normalize_unit(str(ing.get("unit") or "г"))
        if unit not in ALLOWED_UNITS:
            # last resort: map unknown to г or шт
            unit = "шт" if "шт" in unit.lower() or unit in {"зубчик", "пучок"} else "г"
        ing["unit"] = unit

        cat = _normalize_category(str(ing.get("category") or "прочее"))
        if cat not in ALLOWED_INGREDIENT_CATEGORIES:
            cat = "прочее"
        ing["category"] = cat

        name = str(ing.get("name") or "").strip()
        shopping = str(ing.get("shopping_name") or "").strip()
        if not shopping and name:
            ing["shopping_name"] = _default_shopping_name(name)

        amount = ing.get("amount")
        display = str(ing.get("display_amount") or "").strip()
        if not display and amount is not None:
            ing["display_amount"] = _format_display_amount(amount, unit)

        if ing.get("optional") is None:
            ing["optional"] = False

    nutrition = dict(out.get("nutrition_per_serving") or {})
    fiber_d, salt_d, sugar_d = _estimate_nutrition_defaults(out)
    if nutrition.get("fiber_g") is None:
        nutrition["fiber_g"] = fiber_d
    if nutrition.get("salt_g") is None:
        nutrition["salt_g"] = salt_d
    if nutrition.get("sugar_g") is None:
        nutrition["sugar_g"] = sugar_d
    out["nutrition_per_serving"] = nutrition

    prep = int(out.get("prep_time_min") or 0)
    cook = int(out.get("cook_time_min") or 0)
    total = int(out.get("total_time_min") or 0)
    if total < prep + cook:
        out["total_time_min"] = prep + cook

    out["restriction_keys"] = _cleanup_restriction_keys(out)

    shopping = dict(out.get("shopping") or {})
    shopping.setdefault("aggregation_safe", True)
    shopping.setdefault("has_fractional_amounts", False)
    shopping.setdefault("rounding_notes", "")
    out["shopping"] = shopping

    image = dict(out.get("image_prompt_data") or {})
    image.setdefault("serving_style", "единый сервиз PLANAM")
    avoid = image.get("avoid_visuals") or ["текст", "логотипы", "руки", "грязный фон"]
    image["avoid_visuals"] = avoid
    out["image_prompt_data"] = image

    return out
