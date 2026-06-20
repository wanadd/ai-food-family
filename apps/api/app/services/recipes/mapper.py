"""ORM → DTO conversion for recipes.

Pure functions, no DB access. The mapper is the single place that knows
how to assemble a ``RecipeSummary`` / ``RecipeDetail`` from a ``Recipe``
ORM instance and the favourite-ids set.
"""

from __future__ import annotations

from app.models.recipe import Recipe
from app.schemas.recipe import (
    NutritionSummary,
    RecipeDetail,
    RecipeIngredient,
    RecipeSummary,
)
from app.services.recipe_storage import (
    get_allergens,
    get_restrictions,
    get_structured_ingredients,
    get_structured_steps,
    get_tags,
)

ALLOWED_NUTRITION_CONFIDENCE = frozenset(
    {"exact", "estimated", "low_confidence", "unavailable"}
)


def normalize_nutrition_confidence(raw: str | None) -> str | None:
    """Map DB/import values to NutritionSummary.confidence literals."""
    if raw is None:
        return None
    value = str(raw).strip()
    if not value:
        return None
    if value in ALLOWED_NUTRITION_CONFIDENCE:
        return value
    return "estimated"


def prep_minutes(recipe: Recipe) -> int:
    return recipe.prep_time_minutes or recipe.cooking_time_minutes or 30


def public_title(recipe: Recipe) -> str:
    return recipe.display_title or recipe.title


def public_original_title(recipe: Recipe, *, shown_title: str) -> str | None:
    original = recipe.original_title or recipe.title
    if original.strip() == shown_title.strip():
        return None
    return original


def nutrition_summary(recipe: Recipe) -> NutritionSummary | None:
    """Build the recipe-level nutrition summary; None when not yet calculated.

    Reads the additive recipes.nutrition_* columns. Safe on older DBs where the
    columns may be missing (returns None).
    """
    confidence = normalize_nutrition_confidence(
        getattr(recipe, "nutrition_confidence", None)
    )
    calculated_at = getattr(recipe, "nutrition_calculated_at", None)
    if not confidence and calculated_at is None:
        return None
    return NutritionSummary(
        kcal_total=getattr(recipe, "nutrition_kcal_total", None),
        protein_total=getattr(recipe, "nutrition_protein_total", None),
        fat_total=getattr(recipe, "nutrition_fat_total", None),
        carbs_total=getattr(recipe, "nutrition_carbs_total", None),
        kcal_per_serving=getattr(recipe, "nutrition_kcal_per_serving", None),
        protein_per_serving=getattr(recipe, "nutrition_protein_per_serving", None),
        fat_per_serving=getattr(recipe, "nutrition_fat_per_serving", None),
        carbs_per_serving=getattr(recipe, "nutrition_carbs_per_serving", None),
        servings=getattr(recipe, "nutrition_servings", None),
        serving_size_text=getattr(recipe, "nutrition_serving_size_text", None),
        confidence=confidence,
        needs_review=bool(getattr(recipe, "nutrition_needs_review", False)),
        review_reason=getattr(recipe, "nutrition_review_reason", None),
        calculated_at=calculated_at,
    )


def to_summary(
    recipe: Recipe,
    favorite_ids: set[int],
    *,
    fit_level: str | None = None,
) -> RecipeSummary:
    shown = public_title(recipe)
    full = (recipe.title or "").strip()
    full_title = full if full and full != shown.strip() else None
    return RecipeSummary(
        id=recipe.id,
        title=shown,
        display_title=recipe.display_title or shown,
        full_title=full_title,
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
        hero_image_url=recipe.hero_image_url,
        thumbnail_url=recipe.thumbnail_url,
        nutrition_summary=nutrition_summary(recipe),
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
