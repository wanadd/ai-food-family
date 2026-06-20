"""Stage Q3: catalog-ready pool for default GET /recipes.

Default user catalog shows only recipes that are safe to present in the UI:
active, with a hero image, and from a curated PlanAm source type.

Legacy/import rows without photos remain in the DB and are visible only when
``include_legacy=true`` (admin debug).
"""

from __future__ import annotations

from sqlalchemy import and_
from sqlalchemy.orm import Query

from app.models.recipe import Recipe

CATALOG_READY_SOURCE_TYPES: frozenset[str] = frozenset(
    {
        "seed",
        "generated_original",
        "manual_original",
    }
)


def has_hero_image_url(recipe: Recipe) -> bool:
    return bool(recipe.hero_image_url and str(recipe.hero_image_url).strip())


def is_catalog_ready_recipe(recipe: Recipe) -> bool:
    if not has_hero_image_url(recipe):
        return False
    return str(recipe.source_type or "") in CATALOG_READY_SOURCE_TYPES


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

    return query.filter(
        and_(
            Recipe.hero_image_url.isnot(None),
            Recipe.hero_image_url != "",
            Recipe.source_type.in_(tuple(CATALOG_READY_SOURCE_TYPES)),
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
