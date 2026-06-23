"""Stage Q3: catalog-ready pool for default GET /recipes.

Default user catalog shows only recipes that are safe to present in the UI:
active, with a hero image, and from a curated PlanAm source type.

Legacy/import rows without photos remain in the DB and are visible only when
``include_legacy=true`` (admin debug).
"""

from __future__ import annotations

from sqlalchemy import and_, or_
from sqlalchemy.orm import Query

from app.models.recipe import Recipe

CATALOG_READY_SOURCE_TYPES: frozenset[str] = frozenset(
    {
        "seed",
        "generated_original",
        "manual_original",
    }
)
GOLD_V3_CATALOG_READY_TAGS: frozenset[str] = frozenset(
    {
        "gold_v3",
        "recipe_schema_v3",
        "upgraded_from_legacy",
    }
)


def has_hero_image_url(recipe: Recipe) -> bool:
    return bool(recipe.hero_image_url and str(recipe.hero_image_url).strip())


def _recipe_tags(recipe: Recipe) -> set[str]:
    tag_rows = getattr(recipe, "tag_rows", None) or []
    if tag_rows:
        return {str(getattr(row, "tag", "")).strip() for row in tag_rows if getattr(row, "tag", None)}
    return {str(tag).strip() for tag in (getattr(recipe, "tags", None) or []) if tag}


def is_gold_v3_catalog_ready_recipe(recipe: Recipe) -> bool:
    return bool(_recipe_tags(recipe) & GOLD_V3_CATALOG_READY_TAGS)


def is_catalog_ready_recipe(recipe: Recipe) -> bool:
    if not has_hero_image_url(recipe):
        return False
    return (
        str(recipe.source_type or "") in CATALOG_READY_SOURCE_TYPES
        or is_gold_v3_catalog_ready_recipe(recipe)
    )


def catalog_ready_filter_enabled(*, include_legacy: bool) -> bool:
    return not include_legacy


def apply_catalog_ready_filter(
    query: Query,
    *,
    include_legacy: bool = False,
) -> Query:
    """Restrict to catalog-ready recipes unless legacy explicitly included."""
    if not catalog_ready_filter_enabled(include_legacy=include_legacy):
        return query

    gold_v3_tag_filter = or_(
        Recipe.tags.contains(["gold_v3"]),
        Recipe.tags.contains(["recipe_schema_v3"]),
        Recipe.tags.contains(["upgraded_from_legacy"]),
    )

    return query.filter(
        and_(
            Recipe.hero_image_url.isnot(None),
            Recipe.hero_image_url != "",
            or_(
                Recipe.source_type.in_(tuple(CATALOG_READY_SOURCE_TYPES)),
                gold_v3_tag_filter,
            ),
        )
    )


def filter_catalog_ready_recipes(
    recipes: list[Recipe],
    *,
    include_legacy: bool = False,
) -> list[Recipe]:
    if not catalog_ready_filter_enabled(include_legacy=include_legacy):
        return recipes
    return [r for r in recipes if is_catalog_ready_recipe(r)]
