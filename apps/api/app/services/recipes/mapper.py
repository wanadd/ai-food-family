"""ORM → DTO conversion for recipes.

Pure functions, no DB access. The mapper is the single place that knows
how to assemble a ``RecipeSummary`` / ``RecipeDetail`` from a ``Recipe``
ORM instance and the favourite-ids set.
"""

from __future__ import annotations

from app.models.recipe import Recipe
from app.schemas.recipe import RecipeDetail, RecipeIngredient, RecipeSummary
from app.services.recipe_storage import (
    get_allergens,
    get_restrictions,
    get_structured_ingredients,
    get_structured_steps,
    get_tags,
)


def prep_minutes(recipe: Recipe) -> int:
    return recipe.prep_time_minutes or recipe.cooking_time_minutes or 30


def public_title(recipe: Recipe) -> str:
    return recipe.display_title or recipe.title


def public_original_title(recipe: Recipe, *, shown_title: str) -> str | None:
    original = recipe.original_title or recipe.title
    if original.strip() == shown_title.strip():
        return None
    return original


def to_summary(
    recipe: Recipe,
    favorite_ids: set[int],
    *,
    fit_level: str | None = None,
) -> RecipeSummary:
    shown = public_title(recipe)
    return RecipeSummary(
        id=recipe.id,
        title=shown,
        display_title=recipe.display_title,
        description=recipe.description or "",
        meal_type=recipe.meal_type,
        category=recipe.category,
        prep_time_minutes=prep_minutes(recipe),
        cooking_time_minutes=recipe.cooking_time_minutes or prep_minutes(recipe),
        servings=recipe.servings,
        difficulty=recipe.difficulty,
        diets=recipe.diets or [],
        tags=get_tags(recipe),
        is_favorited=recipe.id in favorite_ids,
        is_drink=bool(recipe.is_drink),
        is_alcoholic=bool(recipe.is_alcoholic),
        calories_per_serving=recipe.calories_per_serving,
        protein_g=recipe.protein_g,
        fat_g=recipe.fat_g,
        carbs_g=recipe.carbs_g,
        suitable_for_children=recipe.suitable_for_children,
        suitable_for_sport=recipe.suitable_for_sport,
        suitable_for_event=recipe.suitable_for_event,
        fit_level=fit_level,  # type: ignore[arg-type]
        image_url=recipe.image_url,
    )


def to_detail(recipe: Recipe, favorite_ids: set[int]) -> RecipeDetail:
    summary = to_summary(recipe, favorite_ids)
    structured = get_structured_ingredients(recipe)
    return RecipeDetail(
        **summary.model_dump(),
        original_title=public_original_title(recipe, shown_title=summary.title),
        ingredients=[
            RecipeIngredient(
                name=i["name"],
                amount=i["amount"],
                quantity=i.get("quantity"),
                unit=i.get("unit"),
                category=i.get("category"),
                is_optional=i.get("is_optional", False),
            )
            for i in structured
        ],
        steps=get_structured_steps(recipe),
        allergens=get_allergens(recipe),
        restrictions=get_restrictions(recipe),
        sugar_g=recipe.sugar_g,
        caffeine_mg=recipe.caffeine_mg,
        alcohol_percent=recipe.alcohol_percent,
        cuisine=recipe.cuisine,
        source_type=recipe.source_type or "manual",
        created_at=recipe.created_at,
        updated_at=recipe.updated_at,
    )
