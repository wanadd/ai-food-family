"""PLANAM Recipe V2 validation (no DB writes)."""

from __future__ import annotations

import re
from typing import Any

from app.recipes.product_taxonomy import (
    SHOPPING_CATEGORIES_V2,
    infer_shopping_category_v2,
    pantry_category_slug,
)

ALLOWED_UNITS: frozenset[str] = frozenset(
    {
        "г",
        "кг",
        "мл",
        "л",
        "шт",
        "ст.л.",
        "ч.л.",
        "по вкусу",
        "щепотка",
        "зубчик",
        "пучок",
    }
)

ALLOWED_MEAL_TYPES: frozenset[str] = frozenset(
    {
        "breakfast",
        "lunch",
        "dinner",
        "snack",
        "drink",
    }
)

ALLOWED_DIFFICULTIES: frozenset[str] = frozenset({"easy", "medium", "hard"})

ALLOWED_NUTRITION_CONFIDENCE: frozenset[str] = frozenset(
    {"verified", "estimated", "unavailable"}
)

# Products that should not use ``шт`` without explicit piece semantics.
WEIGHT_VOLUME_PRODUCTS: frozenset[str] = frozenset(
    {
        "мука",
        "сахар",
        "соль",
        "гречка",
        "рис",
        "овсянка",
        "крупа",
        "молоко",
        "вода",
        "масло",
        "мёд",
        "мед",
        "мясо",
        "филе",
        "говядина",
        "курица",
        "свинина",
        "рыба",
        "творог",
        "сыр",
    }
)

# Explicit whitelist: these may legitimately be counted in pieces.
PIECE_WHITELIST: frozenset[str] = frozenset(
    {
        "яйцо",
        "яйца",
        "лимон",
        "яблоко",
        "банан",
        "картофель",
        "лук",
        "морковь",
        "огурец",
        "помидор",
        "перец",
        "булочка",
        "батон",
        "лаваш",
        "авокадо",
    }
)

ALCOHOL_KEYWORDS = re.compile(
    r"\b(водк|виски|коньяк|ром|джин|лик[её]р|настойк|вино|шампан|пиво|алкогол)\b",
    re.IGNORECASE,
)
PORK_KEYWORDS = re.compile(r"\b(свинин|бекон|ветчин|сало|колбас)\b", re.IGNORECASE)
QUANTITY_IN_NAME = re.compile(
    r"\b\d+([.,]\d+)?\s*(г|кг|мл|л|шт|ст\.?\s*л\.?|ч\.?\s*л\.?)\b",
    re.IGNORECASE,
)
SLUG_RE = re.compile(r"^[a-z][a-z0-9_]{1,63}$")


def _slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-zа-яё0-9\s_-]", "", text)
    translit = {
        "а": "a",
        "б": "b",
        "в": "v",
        "г": "g",
        "д": "d",
        "е": "e",
        "ё": "e",
        "ж": "zh",
        "з": "z",
        "и": "i",
        "й": "y",
        "к": "k",
        "л": "l",
        "м": "m",
        "н": "n",
        "о": "o",
        "п": "p",
        "р": "r",
        "с": "s",
        "т": "t",
        "у": "u",
        "ф": "f",
        "х": "h",
        "ц": "ts",
        "ч": "ch",
        "ш": "sh",
        "щ": "sch",
        "ы": "y",
        "э": "e",
        "ю": "yu",
        "я": "ya",
    }
    out: list[str] = []
    for ch in text:
        if ch in translit:
            out.append(translit[ch])
        elif ch.isascii() and (ch.isalnum() or ch in "_-"):
            out.append(ch)
        elif ch.isspace() or ch in "-_":
            out.append("_")
    slug = re.sub(r"_+", "_", "".join(out)).strip("_")
    return slug or "ingredient"


def _as_list(value: Any, field: str) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    raise ValueError(f"{field} must be a list")


def _normalize_steps(raw_steps: list[Any]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for idx, step in enumerate(raw_steps, start=1):
        if isinstance(step, str):
            text = step.strip()
            if not text:
                continue
            normalized.append({"order": idx, "title": f"Шаг {idx}", "instruction": text})
            continue
        if not isinstance(step, dict):
            raise ValueError(f"steps[{idx - 1}] must be string or object")
        instruction = str(step.get("instruction") or step.get("text") or "").strip()
        if not instruction:
            continue
        normalized.append(
            {
                "order": int(step.get("order") or idx),
                "title": str(step.get("title") or f"Шаг {idx}").strip(),
                "instruction": instruction,
                **(
                    {"duration_minutes": int(step["duration_minutes"])}
                    if step.get("duration_minutes") is not None
                    else {}
                ),
                **({"tips": str(step["tips"]).strip()} if step.get("tips") else {}),
            }
        )
    return normalized


def validate_recipe_v2(raw: dict[str, Any]) -> dict[str, Any]:
    """Validate and normalize a Recipe V2 document."""
    errors: list[str] = []
    warnings: list[str] = []

    title = str(raw.get("title") or "").strip()
    if not title:
        errors.append("title is empty")

    meal_types = [str(x).strip() for x in _as_list(raw.get("meal_types"), "meal_types") if str(x).strip()]
    if not meal_types:
        errors.append("meal_types must contain at least one value")
    else:
        bad_meals = [m for m in meal_types if m not in ALLOWED_MEAL_TYPES]
        if bad_meals:
            errors.append(f"invalid meal_types: {bad_meals}")

    servings = raw.get("servings")
    if servings is None or int(servings) < 1:
        errors.append("servings must be >= 1")

    category = str(raw.get("category") or raw.get("recipe_category") or "").strip()
    if not category:
        errors.append("category is not defined")

    raw_ingredients = _as_list(raw.get("ingredients"), "ingredients")
    if not raw_ingredients:
        errors.append("ingredients must contain at least one item")

    raw_steps = _as_list(raw.get("steps"), "steps")
    try:
        steps = _normalize_steps(raw_steps)
    except ValueError as exc:
        errors.append(str(exc))
        steps = []
    if not steps:
        errors.append("steps must contain at least one non-empty item")

    nutrition = raw.get("nutrition_summary") or {}
    confidence = str(
        nutrition.get("confidence") or raw.get("nutrition_confidence") or ""
    ).strip()
    has_nutrition = any(
        nutrition.get(k) is not None
        for k in ("calories", "protein_g", "fat_g", "carbs_g")
    )
    if not has_nutrition and confidence != "unavailable":
        errors.append(
            "nutrition_summary missing and nutrition_confidence is not 'unavailable'"
        )
    if confidence and confidence not in ALLOWED_NUTRITION_CONFIDENCE:
        errors.append(f"invalid nutrition confidence: {confidence!r}")

    normalized_ingredients: list[dict[str, Any]] = []
    slug_seen: set[str] = set()

    for idx, item in enumerate(raw_ingredients):
        prefix = f"ingredients[{idx}]"
        if not isinstance(item, dict):
            errors.append(f"{prefix} must be an object")
            continue

        display_name = str(item.get("display_name") or item.get("name") or "").strip()
        if not display_name or display_name.lower() == "undefined":
            errors.append(f"{prefix}.display_name is empty or undefined")
            continue
        if len(display_name) > 120:
            warnings.append(f"{prefix}.display_name is very long ({len(display_name)} chars)")
        if QUANTITY_IN_NAME.search(display_name):
            errors.append(f"{prefix}.display_name contains embedded quantity/unit: {display_name!r}")

        unit = str(item.get("unit") or "").strip()
        if not unit or unit.lower() == "undefined":
            errors.append(f"{prefix}.unit is empty or undefined")
        elif unit not in ALLOWED_UNITS:
            errors.append(f"{prefix}.unit {unit!r} is not in whitelist")

        amount = item.get("amount")
        if amount is None:
            errors.append(f"{prefix}.amount is required")

        canonical_name = str(item.get("canonical_name") or display_name).strip().lower()
        canonical_slug = str(item.get("canonical_slug") or _slugify(canonical_name)).strip()
        if not SLUG_RE.match(canonical_slug):
            errors.append(f"{prefix}.canonical_slug invalid: {canonical_slug!r}")
        elif canonical_slug in slug_seen:
            errors.append(f"duplicate canonical_slug in recipe: {canonical_slug!r}")
        else:
            slug_seen.add(canonical_slug)

        if unit == "шт":
            name_lower = canonical_name.lower()
            if any(p in name_lower for p in WEIGHT_VOLUME_PRODUCTS):
                if not any(p in name_lower for p in PIECE_WHITELIST):
                    errors.append(
                        f"{prefix}: unit 'шт' unusual for {display_name!r}; use г/мл or whitelist piece product"
                    )

        shopping = str(item.get("shopping_category_slug") or "").strip()
        if shopping and shopping not in SHOPPING_CATEGORIES_V2:
            errors.append(f"{prefix}.shopping_category_slug invalid: {shopping!r}")
        if not shopping:
            shopping = infer_shopping_category_v2(display_name)
            warnings.append(f"{prefix}: inferred shopping_category_slug={shopping}")

        pantry = str(item.get("pantry_category_slug") or "").strip() or pantry_category_slug(shopping)
        if pantry not in SHOPPING_CATEGORIES_V2:
            errors.append(f"{prefix}.pantry_category_slug invalid: {pantry!r}")

        normalized_ingredients.append(
            {
                "display_name": display_name,
                "canonical_name": canonical_name,
                "canonical_slug": canonical_slug,
                "amount": amount,
                "unit": unit,
                **({"amount_grams": item["amount_grams"]} if item.get("amount_grams") is not None else {}),
                **({"amount_ml": item["amount_ml"]} if item.get("amount_ml") is not None else {}),
                "shopping_category_slug": shopping,
                "pantry_category_slug": pantry,
                "allergens": list(item.get("allergens") or []),
                "diet_flags": list(item.get("diet_flags") or []),
                "is_optional": bool(item.get("is_optional", False)),
                **(
                    {"preparation_note": str(item["preparation_note"]).strip()}
                    if item.get("preparation_note")
                    else {}
                ),
            }
        )

    full_text = title + " " + str(raw.get("description") or "")
    is_alcoholic = bool(raw.get("is_alcoholic")) or bool(ALCOHOL_KEYWORDS.search(full_text))
    has_pork = bool(PORK_KEYWORDS.search(full_text)) or any(
        PORK_KEYWORDS.search(str(i.get("display_name") or i.get("name") or ""))
        for i in raw_ingredients
        if isinstance(i, dict)
    )

    diet_tags = [str(x) for x in _as_list(raw.get("diet_tags"), "diet_tags")]
    excludes = [str(x) for x in _as_list(raw.get("excludes"), "excludes")]
    religious_tags = [str(x) for x in _as_list(raw.get("religious_tags"), "religious_tags")]

    if is_alcoholic and "no_alcohol" not in diet_tags and not raw.get("allows_alcohol"):
        errors.append("alcohol recipe requires allows_alcohol=true or explicit restriction metadata")

    if has_pork and "no_pork" not in excludes and "no_pork" not in religious_tags:
        if "halal" in religious_tags or "kosher" in religious_tags:
            errors.append("pork ingredient conflicts with halal/kosher tags without excludes metadata")

    difficulty = str(raw.get("difficulty") or "easy").strip()
    if difficulty not in ALLOWED_DIFFICULTIES:
        warnings.append(f"difficulty {difficulty!r} not in {sorted(ALLOWED_DIFFICULTIES)}")

    prep_time = int(raw.get("prep_time_minutes") or raw.get("prep_time") or 0)
    cook_time = int(raw.get("cook_time_minutes") or raw.get("cook_time") or 0)
    total_time = int(raw.get("total_time_minutes") or prep_time + cook_time)

    normalized_recipe: dict[str, Any] = {
        "title": title,
        "normalized_title": str(raw.get("normalized_title") or title).strip().lower(),
        "description": str(raw.get("description") or "").strip(),
        "meal_types": meal_types,
        "category": category,
        "servings": int(servings) if servings is not None else None,
        "prep_time_minutes": prep_time,
        "cook_time_minutes": cook_time,
        "total_time_minutes": total_time,
        "difficulty": difficulty,
        "image_url": raw.get("image_url"),
        "source_type": str(raw.get("source_type") or "seed"),
        "recipe_schema_version": 2,
        "status": str(raw.get("status") or "gold"),
        "nutrition_summary": {
            "calories": nutrition.get("calories"),
            "protein_g": nutrition.get("protein_g"),
            "fat_g": nutrition.get("fat_g"),
            "carbs_g": nutrition.get("carbs_g"),
            "fiber_g": nutrition.get("fiber_g"),
            "sugar_g": nutrition.get("sugar_g"),
            "salt_g": nutrition.get("salt_g"),
            "confidence": confidence or ("estimated" if has_nutrition else "unavailable"),
        },
        "ingredients": normalized_ingredients,
        "steps": steps,
        "diet_tags": diet_tags,
        "excludes": excludes,
        "allergens": [str(x) for x in _as_list(raw.get("allergens"), "allergens")],
        "religious_tags": religious_tags,
        "tags": list(raw.get("tags") or []),
    }

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "normalized_recipe": normalized_recipe,
    }
