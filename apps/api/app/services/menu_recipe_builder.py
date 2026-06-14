"""Build daily menus from the recipe database (AI assists selection, not invention)."""

from __future__ import annotations

import random
from typing import Literal

from sqlalchemy.orm import Session, joinedload

from app.models.recipe import Recipe
from app.models.user import User
from app.services.menu_catalog_pool import meal_from_catalog_recipe, query_menu_catalog_recipes
from app.schemas.menu import MenuIngredient, MenuMeal, MenuVariant
from app.services.menu_context import MenuGenerationContext
from app.services.menu_labels import VARIANT_META
from app.services.pantry import get_active_items_for_scope
from app.services.recipe_storage import (
    aggregate_ingredients_for_shopping,
    get_structured_ingredients,
    scale_ingredients,
    servings_base,
)
from app.services.app_scope import AppScope
from app.services.meal_leftovers import list_active_leftovers
from app.services.menu_restriction_safety import (
    MIN_RECIPE_POOL_SIZE,
    apply_pre_ai_recipe_filter,
)

MealSlot = Literal["breakfast", "lunch", "dinner", "snack"]
DrinkMode = Literal[
    "none",
    "non_alcoholic",
    "sport",
    "tea_coffee",
    "cocktail",
    "custom",
]

FOOD_MEAL_TYPES = ("breakfast", "lunch", "dinner", "snack", "dessert")
DRINK_MEAL_TYPES = (
    "drink",
    "smoothie",
    "protein_shake",
    "tea",
    "coffee",
    "cocktail",
)


def _pantry_names(scope_items: list) -> set[str]:
    names: set[str] = set()
    for item in scope_items:
        n = getattr(item, "name", None) or (item.get("name") if isinstance(item, dict) else "")
        if n:
            names.add(str(n).lower())
    return names


def _leftover_titles(leftovers: list) -> set[str]:
    return {lo.dish_name.lower() for lo in leftovers}


def _recipe_matches_pantry(recipe: Recipe, pantry: set[str]) -> bool:
    for ing in get_structured_ingredients(recipe):
        name = ing["name"].lower()
        if any(p in name or name in p for p in pantry):
            return True
    return False


def _filter_candidates(
    recipes: list[Recipe],
    *,
    meal_types: tuple[str, ...],
    exclude_alcohol: bool = True,
    kids_only: bool = False,
    sport_only: bool = False,
    event_only: bool = False,
    exclude_allergens: set[str] | None = None,
    pantry: set[str] | None = None,
    from_pantry_only: bool = False,
) -> list[Recipe]:
    result: list[Recipe] = []
    for r in recipes:
        if not r.is_active:
            continue
        if r.meal_type not in meal_types:
            continue
        if exclude_alcohol and r.is_alcoholic:
            continue
        if kids_only and not r.suitable_for_children:
            continue
        if sport_only and not r.suitable_for_sport:
            continue
        if event_only and not r.suitable_for_event:
            continue
        if exclude_allergens:
            text = (r.title + " " + r.description).lower()
            for a in exclude_allergens:
                if a and a in text:
                    break
            else:
                pass
        if from_pantry_only and pantry and not _recipe_matches_pantry(r, pantry):
            continue
        result.append(r)
    return result


def _pick_one(candidates: list[Recipe], used_ids: set[int], rng: random.Random) -> Recipe | None:
    pool = [r for r in candidates if r.id not in used_ids]
    if not pool:
        pool = candidates
    if not pool:
        return None
    choice = rng.choice(pool)
    used_ids.add(choice.id)
    return choice


def _meal_from_recipe(recipe: Recipe, meal_type: str, persons: int) -> MenuMeal:
    return MenuMeal(
        meal_type=meal_type,  # type: ignore[arg-type]
        name=recipe.title,
        description=recipe.description or "",
        prep_time_minutes=recipe.cooking_time_minutes or recipe.prep_time_minutes or 30,
        calories_estimate=int(recipe.calories_per_serving) if recipe.calories_per_serving else None,
        recipe_id=recipe.id,
    )


def _ingredients_for_variant(
    meals_recipes: list[tuple[str, Recipe]],
    persons: int,
    pantry: set[str],
    leftovers: set[str],
) -> list[MenuIngredient]:
    raw_items: list[dict] = []
    for _slot, recipe in meals_recipes:
        title_lower = recipe.title.lower()
        if any(lo in title_lower or title_lower in lo for lo in leftovers):
            continue
        scaled = scale_ingredients(recipe, persons)
        for ing in scaled:
            name = ing["name"]
            name_lower = name.lower()
            in_pantry = any(p in name_lower or name_lower in p for p in pantry)
            if in_pantry:
                continue
            raw_items.append(ing)
    aggregated = aggregate_ingredients_for_shopping(raw_items)
    return [
        MenuIngredient(
            name=item["name"],
            amount=item["amount"],
            category=item.get("category"),
        )
        for item in aggregated
    ]


def build_menus_from_recipes(
    db: Session,
    user: User,
    context: MenuGenerationContext,
    scope: AppScope,
    *,
    persons: int,
    drink_mode: DrinkMode = "none",
    allow_alcohol: bool = False,
    plan_mode: str = "healthy",
) -> list[MenuVariant] | None:
    recipes = (
        query_menu_catalog_recipes(db)
        .options(
            joinedload(Recipe.ingredient_rows),
            joinedload(Recipe.step_rows),
        )
        .all()
    )
    from app.services.onboarding import get_or_create_profile

    profile = get_or_create_profile(db, user)
    recipes, pool_warnings = apply_pre_ai_recipe_filter(recipes, profile)
    if len(recipes) < MIN_RECIPE_POOL_SIZE:
        return None

    pantry_items = get_active_items_for_scope(db, scope)
    pantry = _pantry_names(pantry_items)
    leftovers = _leftover_titles(list_active_leftovers(db, scope))

    profile_allergies = {str(a).lower() for a in (profile.allergies or [])}
    safety_suffix = "\n".join(pool_warnings) if pool_warnings else ""

    rng = random.Random(hash(context.context_label) % 2**32)

    variants: list[MenuVariant] = []
    for variant_key in ("quick", "economy", "balanced"):
        meta = VARIANT_META[variant_key]  # type: ignore[index]
        used: set[int] = set()
        meals_recipes: list[tuple[str, Recipe]] = []

        for slot in ("breakfast", "lunch", "dinner"):
            max_time = {"quick": 25, "economy": 60, "balanced": 45}[variant_key]
            candidates = _filter_candidates(
                recipes,
                meal_types=FOOD_MEAL_TYPES,
                exclude_alcohol=True,
                exclude_allergens=profile_allergies,
            )
            candidates = [
                r
                for r in candidates
                if r.meal_type == slot
                and (r.cooking_time_minutes or 30) <= max_time
            ]
            if variant_key == "economy":
                candidates.sort(key=lambda r: r.calories_per_serving or 0)
            elif variant_key == "quick":
                candidates.sort(key=lambda r: r.cooking_time_minutes or 99)
            picked = _pick_one(candidates, used, rng)
            if picked:
                meals_recipes.append((slot, picked))

        if drink_mode != "none":
            drink_types: tuple[str, ...]
            if drink_mode == "sport" or plan_mode in ("sport", "mass", "cut"):
                drink_types = ("protein_shake", "smoothie", "drink")
            elif drink_mode == "tea_coffee":
                drink_types = ("tea", "coffee", "drink")
            elif drink_mode == "cocktail" and allow_alcohol:
                drink_types = ("cocktail", "drink")
            else:
                drink_types = ("drink", "smoothie", "drink")
            drink_candidates = _filter_candidates(
                recipes,
                meal_types=drink_types,
                exclude_alcohol=not allow_alcohol,
                sport_only=drink_mode == "sport",
            )
            drink = _pick_one(drink_candidates, used, rng)
            if drink:
                meals_recipes.append(("snack", drink))

        if len(meals_recipes) < 3:
            return None

        meals = [meal_from_catalog_recipe(r, slot, persons) for slot, r in meals_recipes]
        ingredients = _ingredients_for_variant(meals_recipes, persons, pantry, leftovers)
        total_prep = sum(m.prep_time_minutes for m in meals)

        variants.append(
            MenuVariant(
                variant=variant_key,  # type: ignore[arg-type]
                title=meta["title"],
                tagline=meta.get("tagline", ""),
                explanation=(
                    f"Меню собрано из базы ПланАм ({len(meals_recipes)} блюд). "
                    "Рецепты подобраны под ваш профиль; порции пересчитаны на "
                    f"{persons} чел."
                    + (f"\n{safety_suffix}" if safety_suffix else "")
                ),
                total_prep_minutes=total_prep,
                meals=meals,
                ingredients=ingredients or [
                    MenuIngredient(name="Вода", amount="1 л", category="drinks")
                ],
            )
        )

    return variants if len(variants) == 3 else None
