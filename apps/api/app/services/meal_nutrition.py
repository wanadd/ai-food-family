"""Resolve calories/macros for a meal check-in."""

from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from app.models.recipe import Recipe
from app.schemas.menu import MenuVariant

# Defaults when eating out without menu/recipe data (kcal).
OUT_STATUS_DEFAULTS: dict[str, int] = {
    "ate_work": 500,
    "ate_cafe": 550,
    "ate_restaurant": 650,
    "ate_delivery": 700,
    "ate_other": 500,
}

MEAL_TYPE_DEFAULTS: dict[str, int] = {
    "breakfast": 380,
    "lunch": 520,
    "dinner": 580,
    "snack": 220,
}


def _macros_from_calories(cal: float) -> tuple[float, float, float]:
    protein = cal * 0.25 / 4
    fat = cal * 0.30 / 9
    carbs = cal * 0.45 / 4
    return protein, fat, carbs


def _meals_for_date(menu: MenuVariant, on_date: date | None) -> list:
    on_date = on_date or date.today()
    if menu.days:
        iso = on_date.isoformat()
        for day in menu.days:
            if day.date_iso == iso:
                return day.meals
        idx = (on_date - date.today()).days
        if 0 <= idx < len(menu.days):
            return menu.days[idx].meals
    return menu.meals


def resolve_meal_nutrition(
    db: Session,
    *,
    meal_type: str,
    actual_status: str,
    menu: MenuVariant | None,
    recipe_id: int | None = None,
    planned_date: date | None = None,
) -> tuple[float | None, float | None, float | None, float | None]:
    """Return calories, protein_g, fat_g, carbs_g."""
    cal: float | None = None
    protein: float | None = None
    fat: float | None = None
    carbs: float | None = None

    if recipe_id:
        recipe = db.get(Recipe, recipe_id)
        if recipe and recipe.calories_per_serving:
            cal = float(recipe.calories_per_serving)
            if recipe.protein_g and recipe.protein_g > 0:
                protein = float(recipe.protein_g)
                fat = float(recipe.fat_g) if recipe.fat_g else None
                carbs = float(recipe.carbs_g) if recipe.carbs_g else None
                if fat is None or carbs is None:
                    p2, f2, c2 = _macros_from_calories(cal)
                    fat = fat if fat is not None else f2
                    carbs = carbs if carbs is not None else c2
                    protein = protein or p2
            else:
                protein, fat, carbs = _macros_from_calories(cal)

    if cal is None and menu:
        for meal in _meals_for_date(menu, planned_date):
            if meal.meal_type == meal_type:
                if meal.calories_estimate:
                    cal = float(meal.calories_estimate)
                if meal.recipe_id and not recipe_id:
                    return resolve_meal_nutrition(
                        db,
                        meal_type=meal_type,
                        actual_status=actual_status,
                        menu=menu,
                        recipe_id=meal.recipe_id,
                        planned_date=planned_date,
                    )
                break

    if cal is None and actual_status in OUT_STATUS_DEFAULTS:
        cal = float(OUT_STATUS_DEFAULTS[actual_status])

    if cal is None:
        cal = float(MEAL_TYPE_DEFAULTS.get(meal_type, 450))

    if protein is None:
        protein, fat, carbs = _macros_from_calories(cal)
    return cal, protein, fat, carbs
