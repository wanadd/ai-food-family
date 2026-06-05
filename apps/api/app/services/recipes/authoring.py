"""Authoring operations: create, update, favorite toggle, add-to-shopping.

Sprint 1 constraint: structural refactor only. Behaviour is preserved from
the legacy ``app.services.recipes`` module.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.recipe import Recipe, RecipeFavorite
from app.models.user import User
from app.schemas.menu import MenuIngredient, MenuMeal, MenuVariant
from app.schemas.recipe import (
    FavoriteToggleResponse,
    RecipeCreateRequest,
    RecipeDetail,
    RecipeUpdateRequest,
)
from app.services import shopping_list as shopping_list_service
from app.services.app_scope import AppScope
from app.services.recipe_storage import (
    aggregate_ingredients_for_shopping,
    persist_recipe_structure,
    scale_ingredients,
)
from . import repository as repository_module
from app.deps import is_admin_user
from app.services.recipes.access import DRAFT_OWNER_PREFIX, DRAFT_SOURCE_TYPE
from app.services.recipes.mapper import to_detail


def toggle_favorite(
    db: Session,
    user: User,
    recipe_id: int,
) -> FavoriteToggleResponse | None:
    recipe = repository_module.get_recipe_by_id(db, recipe_id)
    if recipe is None:
        return None

    existing = repository_module.find_favorite(db, user.id, recipe_id)
    if existing is not None:
        db.delete(existing)
        db.commit()
        return FavoriteToggleResponse(recipe_id=recipe_id, is_favorited=False)

    db.add(RecipeFavorite(user_id=user.id, recipe_id=recipe_id))
    db.commit()
    return FavoriteToggleResponse(recipe_id=recipe_id, is_favorited=True)


def create_recipe(
    db: Session,
    payload: RecipeCreateRequest,
    *,
    user: User,
) -> RecipeDetail:
    as_admin = is_admin_user(user)
    source_type = payload.source_type
    is_active = True
    source_url: str | None = None
    if not as_admin:
        source_type = DRAFT_SOURCE_TYPE
        is_active = False
        source_url = f"{DRAFT_OWNER_PREFIX}{user.id}"

    recipe = Recipe(
        title=payload.title,
        description=payload.description,
        meal_type=payload.meal_type,
        category=payload.category,
        cooking_time_minutes=payload.cooking_time_minutes,
        prep_time_minutes=payload.cooking_time_minutes,
        servings=payload.servings,
        difficulty=payload.difficulty,
        is_drink=payload.is_drink,
        is_alcoholic=payload.is_alcoholic,
        source_type=source_type,
        source_url=source_url,
        is_active=is_active,
    )
    db.add(recipe)
    db.flush()

    ingredients = [i.model_dump() for i in payload.ingredients]
    persist_recipe_structure(
        db,
        recipe,
        ingredients=ingredients,
        steps=payload.steps,
        tags=payload.tags,
        allergens=payload.allergens,
        restrictions=payload.restrictions,
    )
    db.commit()
    db.refresh(recipe)
    return to_detail(recipe, set())


def update_recipe(
    db: Session,
    recipe_id: int,
    payload: RecipeUpdateRequest,
) -> RecipeDetail | None:
    recipe = repository_module.get_recipe_by_id(db, recipe_id)
    if recipe is None:
        return None

    if payload.title is not None:
        recipe.title = payload.title
    if payload.description is not None:
        recipe.description = payload.description
    if payload.is_active is not None:
        recipe.is_active = payload.is_active

    db.commit()
    db.refresh(recipe)
    return to_detail(recipe, set())


def _menu_meal_type_for_recipe(recipe: Recipe) -> str:
    meal_type = recipe.meal_type or "lunch"
    if meal_type in {"breakfast", "lunch", "dinner", "snack"}:
        return meal_type
    return "snack"


def add_recipe_to_shopping(
    db: Session,
    user: User,
    scope: AppScope,
    recipe: Recipe,
    *,
    servings: int | None = None,
) -> None:
    _ = user
    target = servings or recipe.servings or 4
    scaled = scale_ingredients(recipe, target)
    aggregated = aggregate_ingredients_for_shopping(scaled)

    ingredients = [
        MenuIngredient(
            name=i["name"],
            amount=i["amount"],
            category=i.get("category"),
        )
        for i in aggregated
    ]

    menu = MenuVariant(
        variant="balanced",
        title=recipe.title,
        explanation="Ингредиенты из рецепта",
        total_prep_minutes=recipe.cooking_time_minutes or 30,
        meals=[
            MenuMeal(
                meal_type=_menu_meal_type_for_recipe(recipe),
                name=recipe.title,
                description=recipe.description or "",
                prep_time_minutes=recipe.cooking_time_minutes or 30,
                calories_estimate=(
                    int(recipe.calories_per_serving)
                    if recipe.calories_per_serving is not None
                    else None
                ),
                recipe_id=recipe.id,
            )
        ],
        ingredients=ingredients,
    )
    shopping_list_service.sync_from_menu(db, scope, menu, None)

