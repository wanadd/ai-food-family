"""Catalog-ready seed recipe pool for menu generation (Gold V3 hotfix)."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session, joinedload

from app.models.recipe import Recipe
from app.recipes.gold_filter import query_active_recipes
from app.schemas.menu import MenuMeal
from app.services.menu_restriction_safety import apply_pre_ai_recipe_filter

MENU_CATALOG_SOURCE_TYPES: frozenset[str] = frozenset({"seed"})


def has_menu_catalog_hero(recipe: Recipe) -> bool:
    return bool(recipe.hero_image_url and str(recipe.hero_image_url).strip())


def is_menu_catalog_ready_recipe(recipe: Recipe) -> bool:
    return (
        bool(recipe.is_active)
        and str(recipe.source_type or "") in MENU_CATALOG_SOURCE_TYPES
        and has_menu_catalog_hero(recipe)
    )


def query_menu_catalog_recipes(db: Session):
    """Active seed recipes with hero images (256–265 pool on prod)."""
    return (
        query_active_recipes(db)
        .filter(Recipe.source_type.in_(tuple(MENU_CATALOG_SOURCE_TYPES)))
        .filter(Recipe.hero_image_url.isnot(None))
        .filter(Recipe.hero_image_url != "")
    )


def load_menu_catalog_pool(db: Session, profile: Any | None) -> list[Recipe]:
    recipes = query_menu_catalog_recipes(db).options(joinedload(Recipe.ingredient_rows)).all()
    recipes = [r for r in recipes if is_menu_catalog_ready_recipe(r)]
    if profile is not None:
        recipes, _ = apply_pre_ai_recipe_filter(recipes, profile)
    return recipes


def recipe_image_fields(recipe: Recipe) -> dict[str, str | None]:
    hero = (recipe.hero_image_url or "").strip() or None
    card = (recipe.image_url or recipe.thumbnail_url or hero or "").strip() or None
    thumb = (recipe.thumbnail_url or recipe.image_url or hero or "").strip() or None
    return {
        "image_url": card or hero,
        "hero_image_url": hero,
        "thumbnail_url": thumb,
    }


def meal_from_catalog_recipe(recipe: Recipe, meal_type: str, persons: int) -> MenuMeal:
    from app.services.menu_recipe_builder import _meal_from_recipe

    meal = _meal_from_recipe(recipe, meal_type, persons)
    return meal.model_copy(update=recipe_image_fields(recipe))
