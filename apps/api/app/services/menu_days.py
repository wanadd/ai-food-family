"""Build multi-day menu plans from a single-day variant."""

from __future__ import annotations

import random
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.models.recipe import Recipe
from app.models.user import User
from app.services.menu_catalog_pool import load_menu_catalog_pool, meal_from_catalog_recipe
from app.schemas.menu import MenuDayPlan, MenuIngredient, MenuMeal, MenuVariant
from app.services.app_scope import AppScope
from app.services.menu_recipe_builder import (
    FOOD_MEAL_TYPES,
    _filter_candidates,
    _ingredients_for_variant,
    _pantry_names,
    _pick_one,
)
from app.services.meal_leftovers import list_active_leftovers
from app.services.onboarding import get_or_create_profile
from app.services.pantry import get_active_items_for_scope

MEAL_SLOTS = ("breakfast", "lunch", "dinner", "snack")


def day_label(day_index: int, start: date | None = None) -> str:
    start = start or date.today()
    d = start + timedelta(days=day_index - 1)
    weekday = d.strftime("%a")
    ru = {"Mon": "Пн", "Tue": "Вт", "Wed": "Ср", "Thu": "Чт", "Fri": "Пт", "Sat": "Сб", "Sun": "Вс"}
    return f"День {day_index} · {d.strftime('%d.%m')} ({ru.get(weekday, weekday)})"


def expand_variant_to_plan_days(
    db: Session,
    variant: MenuVariant,
    plan_days: int,
    *,
    user: User | None = None,
    scope: AppScope | None = None,
) -> MenuVariant:
    plan_days = max(1, min(30, plan_days))
    if plan_days <= 1:
        return variant.model_copy(update={"plan_days": 1})

    if variant.days and len(variant.days) >= plan_days:
        return variant.model_copy(update={"plan_days": plan_days})

    start = date.today()
    rng = random.Random(hash(variant.title) % 2**32)
    used_recipe_ids: set[int] = set()

    for m in variant.meals:
        if m.recipe_id:
            used_recipe_ids.add(m.recipe_id)

    days_out: list[MenuDayPlan] = []
    all_meal_recipe_pairs: list[tuple[str, Recipe]] = []

    recipes: list[Recipe] = []
    profile_allergies: set[str] = set()
    pantry: set[str] = set()
    leftovers: set[str] = set()
    persons = 1

    if user and scope:
        profile = get_or_create_profile(db, user)
        recipes = load_menu_catalog_pool(db, profile)
        profile_allergies = {str(a).lower() for a in (profile.allergies or [])}
        pantry = _pantry_names(get_active_items_for_scope(db, scope))
        leftovers = _leftover_titles(list_active_leftovers(db, scope))

    day1_needs_rebuild = any(not m.recipe_id for m in variant.meals)
    if recipes and user and scope and day1_needs_rebuild:
        day1_pairs: list[tuple[str, Recipe]] = []
        for slot in ("breakfast", "lunch", "dinner"):
            candidates = _filter_candidates(
                recipes,
                meal_types=FOOD_MEAL_TYPES,
                exclude_alcohol=True,
                exclude_allergens=profile_allergies,
            )
            candidates = [r for r in candidates if r.meal_type == slot]
            picked = _pick_one(candidates, used_recipe_ids, rng)
            if picked:
                day1_pairs.append((slot, picked))
                used_recipe_ids.add(picked.id)
        if len(day1_pairs) >= 2:
            day1_meals = [
                meal_from_catalog_recipe(r, slot, persons) for slot, r in day1_pairs
            ]
            all_meal_recipe_pairs.extend(day1_pairs)
        else:
            day1_meals = list(variant.meals)
    else:
        day1_meals = list(variant.meals)

    days_out.append(
        MenuDayPlan(
            day_index=1,
            label=day_label(1, start),
            date_iso=start.isoformat(),
            meals=day1_meals,
        )
    )

    for day_idx in range(2, plan_days + 1):
        day_date = start + timedelta(days=day_idx - 1)
        meals: list[MenuMeal] = []

        if recipes and user and scope:
            day_pairs: list[tuple[str, Recipe]] = []
            for slot in ("breakfast", "lunch", "dinner"):
                candidates = _filter_candidates(
                    recipes,
                    meal_types=FOOD_MEAL_TYPES,
                    exclude_alcohol=True,
                    exclude_allergens=profile_allergies,
                )
                candidates = [r for r in candidates if r.meal_type == slot]
                picked = _pick_one(candidates, used_recipe_ids, rng)
                if picked:
                    day_pairs.append((slot, picked))
                    used_recipe_ids.add(picked.id)

            if len(day_pairs) >= 2:
                meals = [
                    meal_from_catalog_recipe(r, slot, persons) for slot, r in day_pairs
                ]
                all_meal_recipe_pairs.extend(day_pairs)
        else:
            # Fallback: сдвиг блюд с небольшим суффиксом в названии
            for i, m in enumerate(variant.meals):
                meals.append(
                    m.model_copy(
                        update={
                            "name": m.name if day_idx == 2 else f"{m.name} (вар. {day_idx})",
                        }
                    )
                )

        if not meals:
            meals = list(variant.meals)

        days_out.append(
            MenuDayPlan(
                day_index=day_idx,
                label=day_label(day_idx, start),
                date_iso=day_date.isoformat(),
                meals=meals,
            )
        )

    merged_ingredients = list(variant.ingredients)
    if all_meal_recipe_pairs and user and scope:
        extra = _ingredients_for_variant(all_meal_recipe_pairs, persons, pantry, leftovers)
        seen = {i.name.lower() for i in merged_ingredients}
        for ing in extra:
            if ing.name.lower() not in seen:
                merged_ingredients.append(ing)
                seen.add(ing.name.lower())

    return variant.model_copy(
        update={
            "plan_days": plan_days,
            "days": days_out,
            "meals": days_out[0].meals,
            "ingredients": merged_ingredients or variant.ingredients,
        }
    )


def _leftover_titles(leftovers) -> set[str]:
    return {lo.dish_name.lower() for lo in leftovers}
