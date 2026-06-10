"""Gold Recipe V2 catalog filter (Stage 2A).

When ``settings.recipe_gold_v2_only`` is enabled, catalog/menu/search pools
include only recipes tagged with at least one gold marker. Recipe detail by id
is not filtered here — callers load by primary key directly.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import or_
from sqlalchemy.orm import Query, Session

from app.config import settings
from app.models.recipe import Recipe

GOLD_V2_TAGS: frozenset[str] = frozenset(
    {"gold_v2", "recipe_schema_v2", "status:gold"}
)


def normalize_tags(tags: Any) -> list[str]:
    if not tags:
        return []
    if isinstance(tags, list):
        return [str(t) for t in tags]
    return []


def is_gold_v2_recipe(recipe: Recipe) -> bool:
    return bool(GOLD_V2_TAGS.intersection(normalize_tags(recipe.tags)))


def gold_filter_enabled(*, include_legacy: bool | None = None) -> bool:
    if include_legacy is True:
        return False
    if include_legacy is False:
        return True
    return bool(settings.recipe_gold_v2_only)


def apply_gold_recipe_filter(
    query: Query,
    *,
    include_legacy: bool | None = None,
) -> Query:
    """Restrict query to gold V2 recipes unless legacy explicitly included."""
    if not gold_filter_enabled(include_legacy=include_legacy):
        return query

    return query.filter(
        or_(
            Recipe.tags.contains(["gold_v2"]),
            Recipe.tags.contains(["recipe_schema_v2"]),
            Recipe.tags.contains(["status:gold"]),
        )
    )


def query_active_recipes(
    db: Session,
    *,
    include_legacy: bool | None = None,
) -> Query:
    """Active recipes, optionally limited to gold V2."""
    query = db.query(Recipe).filter(Recipe.is_active.is_(True))
    return apply_gold_recipe_filter(query, include_legacy=include_legacy)


def filter_gold_recipes(recipes: list[Recipe], *, include_legacy: bool = False) -> list[Recipe]:
    """In-memory filter for already-loaded recipe lists."""
    if not gold_filter_enabled(include_legacy=include_legacy):
        return recipes
    return [r for r in recipes if is_gold_v2_recipe(r)]
