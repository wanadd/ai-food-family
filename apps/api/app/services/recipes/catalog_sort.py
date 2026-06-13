"""Default catalog sort: curated PlanAm seed recipes with photos first."""

from __future__ import annotations

from app.models.recipe import Recipe

DEFAULT_CATALOG_SORT = "quality"
LEGACY_CATALOG_SORT = "title"


def _has_hero_image(recipe: Recipe) -> bool:
    return bool(recipe.hero_image_url and str(recipe.hero_image_url).strip())


def catalog_quality_sort_key(recipe: Recipe) -> tuple[int, int, str]:
    """Lower tuple sorts first.

    Tier 0: seed + hero
    Tier 1: any hero
    Tier 2: rest
    Within tier: higher recipe id first (newer).
    """
    has_hero = _has_hero_image(recipe)
    is_seed = str(recipe.source_type or "") == "seed"
    if is_seed and has_hero:
        tier = 0
    elif has_hero:
        tier = 1
    else:
        tier = 2
    return (tier, -int(recipe.id), (recipe.title or "").lower())


def sort_recipes_catalog(
    recipes: list[Recipe],
    *,
    sort: str | None = None,
    goal: str | None = None,
) -> list[Recipe]:
    """Sort recipe list for GET /recipes.

    Default (``sort`` omitted or ``quality``): quality-first tiers, then id desc.
    ``title``: legacy alphabetical order.
    ``newest`` / ``id_desc``: id descending only.
    """
    normalized = (sort or DEFAULT_CATALOG_SORT).strip().lower()

    if normalized == LEGACY_CATALOG_SORT:
        return sorted(recipes, key=lambda r: (r.title or "").lower())

    if normalized in {"newest", "id_desc"}:
        return sorted(recipes, key=lambda r: -int(r.id))

    if goal == "sport":
        return sorted(
            recipes,
            key=lambda r: (
                catalog_quality_sort_key(r)[0],
                not bool(r.suitable_for_sport),
                -int(r.id),
                (r.title or "").lower(),
            ),
        )

    return sorted(recipes, key=catalog_quality_sort_key)
