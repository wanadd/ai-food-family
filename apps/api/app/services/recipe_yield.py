"""Recipe and menu cooking yield helpers (Phase 4C)."""

from __future__ import annotations

from typing import Any

from app.models.recipe import Recipe
from app.schemas.menu import MenuMeal


YIELD_TYPES = frozenset({"servings", "volume", "weight", "count"})
COOK_STRATEGIES = frozenset(
    {"cook_now", "cook_with_leftovers", "cook_for_two_days", "use_existing_leftovers"}
)


def recipe_yield_from_model(recipe: Recipe | None) -> dict[str, Any]:
    if recipe is None:
        return default_servings_yield(servings=1)
    if recipe.yield_type and recipe.recipe_yield_amount:
        return {
            "yield_type": recipe.yield_type,
            "recipe_yield_amount": float(recipe.recipe_yield_amount),
            "recipe_yield_unit": recipe.recipe_yield_unit or "порция",
            "serving_size_amount": recipe.serving_size_amount,
            "serving_size_unit": recipe.serving_size_unit,
            "estimated_servings": recipe.estimated_servings or recipe.servings,
        }
    servings = float(recipe.servings or 1)
    return default_servings_yield(servings=servings)


def default_servings_yield(*, servings: float) -> dict[str, Any]:
    return {
        "yield_type": "servings",
        "recipe_yield_amount": servings,
        "recipe_yield_unit": "порция",
        "serving_size_amount": 1.0,
        "serving_size_unit": "порция",
        "estimated_servings": servings,
    }


def planned_menu_yield_for_meal(
    meal: MenuMeal,
    recipe: Recipe | None = None,
) -> dict[str, Any]:
    if meal.planned_yield_amount is not None and meal.planned_yield_unit:
        return {
            "planned_yield_amount": meal.planned_yield_amount,
            "planned_yield_unit": meal.planned_yield_unit,
            "planned_serving_size_amount": meal.planned_serving_size_amount,
            "planned_serving_size_unit": meal.planned_serving_size_unit,
            "planned_servings": meal.planned_servings,
            "expected_leftover_amount": meal.expected_leftover_amount,
            "expected_leftover_unit": meal.expected_leftover_unit,
            "cook_strategy": meal.cook_strategy or "cook_now",
            "yield_type": meal.yield_type or "servings",
        }
    base = recipe_yield_from_model(recipe)
    servings = float(meal.servings or base.get("estimated_servings") or 1)
    return {
        "planned_yield_amount": base["recipe_yield_amount"],
        "planned_yield_unit": base["recipe_yield_unit"],
        "planned_serving_size_amount": base.get("serving_size_amount"),
        "planned_serving_size_unit": base.get("serving_size_unit"),
        "planned_servings": servings,
        "expected_leftover_amount": None,
        "expected_leftover_unit": None,
        "cook_strategy": "cook_now",
        "yield_type": base.get("yield_type") or "servings",
    }


def sync_batch_physical_from_payload(
    batch,
    *,
    total_amount_value: float | None = None,
    total_amount_unit: str | None = None,
    remaining_amount_value: float | None = None,
    remaining_amount_unit: str | None = None,
    serving_size_value: float | None = None,
    serving_size_unit: str | None = None,
    yield_type: str | None = None,
    estimated_total_servings: float | None = None,
    estimated_remaining_servings: float | None = None,
) -> None:
    if total_amount_value is not None:
        batch.total_amount_value = total_amount_value
    if total_amount_unit is not None:
        batch.total_amount_unit = total_amount_unit
    if remaining_amount_value is not None:
        batch.remaining_amount_value = remaining_amount_value
    if remaining_amount_unit is not None:
        batch.remaining_amount_unit = remaining_amount_unit
    if serving_size_value is not None:
        batch.serving_size_value = serving_size_value
    if serving_size_unit is not None:
        batch.serving_size_unit = serving_size_unit
    if yield_type is not None:
        batch.yield_type = yield_type
    if estimated_total_servings is not None:
        batch.estimated_total_servings = estimated_total_servings
    if estimated_remaining_servings is not None:
        batch.estimated_remaining_servings = estimated_remaining_servings
