"""Gold V3 menu hotfix: catalog-ready recipe binding and meal image enrichment."""

from __future__ import annotations

import random
from typing import Any

from sqlalchemy.orm import Session

from app.models.recipe import Recipe
from app.models.user import User
from app.schemas.menu import MenuDayPlan, MenuMeal, MenuVariant
from app.services.app_scope import AppScope
from app.services.menu_catalog_pool import (
    load_menu_catalog_pool,
    meal_from_catalog_recipe,
    recipe_image_fields,
)
from app.services.menu_recipe_builder import _pick_one

MAIN_MEAL_FALLBACK_TYPES = ("lunch", "dinner")


def attach_recipe_images(meal: MenuMeal, recipe: Recipe) -> MenuMeal:
    from app.services.recipes.mapper import public_title

    shown = public_title(recipe)
    return meal.model_copy(
        update={
            **recipe_image_fields(recipe),
            "name": shown,
            "display_title": shown,
        }
    )


def _pick_catalog_recipe(
    pool: list[Recipe],
    meal_type: str,
    used_ids: set[int],
    rng: random.Random,
) -> Recipe | None:
    exact = [r for r in pool if r.meal_type == meal_type and r.id not in used_ids]
    if exact:
        return _pick_one(exact, used_ids, rng)

    if meal_type in MAIN_MEAL_FALLBACK_TYPES or meal_type == "breakfast":
        fallback_pool = [
            r
            for r in pool
            if r.meal_type in MAIN_MEAL_FALLBACK_TYPES and r.id not in used_ids
        ]
        picked = _pick_one(fallback_pool, used_ids, rng)
        if picked:
            return picked

    return _pick_one(pool, used_ids, rng)


def ensure_meal_catalog_backed(
    meal: MenuMeal,
    pool: list[Recipe],
    pool_by_id: dict[int, Recipe],
    used_ids: set[int],
    rng: random.Random,
    *,
    persons: int,
) -> MenuMeal | None:
    if not pool:
        return meal if meal.recipe_id is not None else None

    recipe: Recipe | None = None
    if meal.recipe_id is not None and meal.recipe_id in pool_by_id:
        recipe = pool_by_id[meal.recipe_id]
    elif meal.recipe_id is not None:
        recipe = _pick_catalog_recipe(pool, meal.meal_type, used_ids, rng)
    else:
        recipe = _pick_catalog_recipe(pool, meal.meal_type, used_ids, rng)

    if recipe is None:
        return None

    used_ids.add(recipe.id)
    return meal_from_catalog_recipe(recipe, meal.meal_type, persons)


def _process_meals(
    meals: list[MenuMeal],
    pool: list[Recipe],
    pool_by_id: dict[int, Recipe],
    used_ids: set[int],
    rng: random.Random,
    *,
    persons: int,
) -> list[MenuMeal]:
    processed: list[MenuMeal] = []
    for meal in meals:
        fixed = ensure_meal_catalog_backed(
            meal,
            pool,
            pool_by_id,
            used_ids,
            rng,
            persons=persons,
        )
        if fixed is not None:
            processed.append(fixed)
    return processed


def finalize_menu_variant(
    db: Session,
    variant: MenuVariant,
    *,
    user: User | None = None,
    scope: AppScope | None = None,
    persons: int = 1,
) -> MenuVariant:
    """Backfill recipe_id from catalog-ready pool and attach recipe image URLs."""
    del scope  # reserved for future scope-specific pools
    profile = None
    if user is not None:
        from app.services.onboarding import get_or_create_profile

        profile = get_or_create_profile(db, user)

    pool = load_menu_catalog_pool(db, profile)
    if not pool:
        return variant

    pool_by_id = {recipe.id: recipe for recipe in pool}
    rng = random.Random(hash((variant.variant, variant.title)) % 2**32)
    used_ids: set[int] = set()

    if variant.days:
        new_days: list[MenuDayPlan] = []
        for day in variant.days:
            day_meals = _process_meals(
                list(day.meals),
                pool,
                pool_by_id,
                used_ids,
                rng,
                persons=persons,
            )
            new_days.append(day.model_copy(update={"meals": day_meals}))
        top_meals = new_days[0].meals if new_days else list(variant.meals)
        return variant.model_copy(update={"days": new_days, "meals": top_meals})

    new_meals = _process_meals(
        list(variant.meals),
        pool,
        pool_by_id,
        used_ids,
        rng,
        persons=persons,
    )
    return variant.model_copy(update={"meals": new_meals})


def finalize_menu_variants(
    db: Session,
    variants: list[MenuVariant],
    *,
    user: User | None,
    scope: AppScope | None,
    persons: int,
) -> list[MenuVariant]:
    return [
        finalize_menu_variant(db, variant, user=user, scope=scope, persons=persons)
        for variant in variants
    ]
