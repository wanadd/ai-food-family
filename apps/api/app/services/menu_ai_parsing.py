"""Normalize OpenAI JSON payloads for menu dish replacement."""

from __future__ import annotations

import logging
from typing import Any

from app.schemas.menu import MealType, MenuMeal

logger = logging.getLogger(__name__)

MEAL_TYPES: tuple[MealType, ...] = ("breakfast", "lunch", "dinner", "snack")


def _int_or_none(val: Any) -> int | None:
    if val is None or val == "":
        return None
    try:
        return int(val)
    except (TypeError, ValueError):
        return None


def _meal_type_from_dict(raw: dict[str, Any]) -> MealType | None:
    for key in MEAL_TYPES:
        if key in raw:
            return key
    meal_type = raw.get("meal_type")
    if meal_type in MEAL_TYPES:
        return meal_type  # type: ignore[return-value]
    return None


def _coerce_meal_dict(
    raw: Any,
    *,
    fallback_meal: MenuMeal,
) -> dict[str, Any] | None:
    if isinstance(raw, str):
        name = raw.strip()
        if not name:
            return None
        return {
            "meal_type": fallback_meal.meal_type,
            "name": name,
            "description": fallback_meal.description,
            "prep_time_minutes": fallback_meal.prep_time_minutes,
            "calories_estimate": fallback_meal.calories_estimate,
            "recipe_id": fallback_meal.recipe_id,
        }

    if not isinstance(raw, dict):
        return None

    meal_type = _meal_type_from_dict(raw)
    if meal_type is not None and "name" not in raw and "title" not in raw:
        value = raw[meal_type]
        if isinstance(value, str):
            return {
                "meal_type": meal_type,
                "name": value.strip(),
                "description": raw.get("description") or "",
                "prep_time_minutes": raw.get("prep_time_minutes")
                or raw.get("prep_time")
                or fallback_meal.prep_time_minutes,
                "calories_estimate": raw.get("calories_estimate")
                or raw.get("calories")
                or fallback_meal.calories_estimate,
                "recipe_id": raw.get("recipe_id") or fallback_meal.recipe_id,
            }
        if isinstance(value, dict):
            merged = {**value}
            merged.setdefault("meal_type", meal_type)
            return merged

    if raw.get("name") or raw.get("title") or raw.get("meal_type"):
        return raw

    return None


def parse_replace_meal_response(
    data: Any,
    *,
    fallback_meal: MenuMeal,
) -> MenuMeal | None:
    """Parse OpenAI replace-dish JSON into MenuMeal.

    Supports:
    - {"meal": {"meal_type", "name", "prep_time_minutes", ...}}
    - {"meal": {"breakfast": "Блины"}}
    - {"breakfast": "Блины с ягодами"}
    - {"meal_type", "name", ...} at top level
    """
    if not isinstance(data, dict):
        logger.warning("Replace meal response is not a dict: %s", type(data).__name__)
        return None

    candidates: list[Any] = []
    if "meal" in data:
        candidates.append(data["meal"])
    candidates.append(data)

    meal_dict: dict[str, Any] | None = None
    for candidate in candidates:
        meal_dict = _coerce_meal_dict(candidate, fallback_meal=fallback_meal)
        if meal_dict is not None:
            break

    if meal_dict is None:
        logger.warning(
            "Unrecognized replace meal response shape; keys=%s",
            list(data.keys()),
        )
        return None

    meal_type = meal_dict.get("meal_type") or fallback_meal.meal_type
    if meal_type not in MEAL_TYPES:
        meal_type = fallback_meal.meal_type

    name = (
        meal_dict.get("name")
        or meal_dict.get("title")
        or fallback_meal.name
    )
    name = str(name).strip()
    if not name:
        name = fallback_meal.name

    description = meal_dict.get("description") or meal_dict.get("why_selected") or ""
    prep_raw = (
        meal_dict.get("prep_time_minutes")
        or meal_dict.get("prep_time")
        or fallback_meal.prep_time_minutes
        or 20
    )
    try:
        prep_time = max(0, min(300, int(prep_raw)))
    except (TypeError, ValueError):
        prep_time = fallback_meal.prep_time_minutes or 20

    calories = _int_or_none(
        meal_dict.get("calories_estimate") or meal_dict.get("calories")
    )
    if calories is None:
        calories = fallback_meal.calories_estimate

    recipe_id = meal_dict.get("recipe_id")
    if recipe_id is not None:
        try:
            recipe_id = int(recipe_id)
        except (TypeError, ValueError):
            recipe_id = fallback_meal.recipe_id
    else:
        recipe_id = fallback_meal.recipe_id

    try:
        return MenuMeal(
            meal_type=meal_type,  # type: ignore[arg-type]
            name=name,
            description=str(description),
            prep_time_minutes=prep_time,
            calories_estimate=calories,
            recipe_id=recipe_id,
        )
    except Exception:
        logger.warning("Failed to build MenuMeal from %s", meal_dict, exc_info=True)
        return None
