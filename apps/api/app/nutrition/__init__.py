"""PLANAM nutrition domain helpers (restrictions catalog, safety)."""

from app.nutrition.restrictions_catalog import (
    RestrictionDefinition,
    get_restriction_definition,
    get_unknown_restrictions,
    list_restrictions,
    list_restrictions_for_ui,
    normalize_restriction_key,
    normalize_restrictions,
)
from app.nutrition.restriction_safety import (
    RestrictionConflict,
    explain_recipe_restriction_conflicts,
    filter_recipes_for_profile,
    has_hard_conflicts,
    has_soft_conflicts,
    normalize_profile_restrictions,
    recipe_is_allowed_for_profile,
)

__all__ = [
    "RestrictionConflict",
    "RestrictionDefinition",
    "explain_recipe_restriction_conflicts",
    "filter_recipes_for_profile",
    "get_restriction_definition",
    "get_unknown_restrictions",
    "has_hard_conflicts",
    "has_soft_conflicts",
    "list_restrictions",
    "list_restrictions_for_ui",
    "normalize_profile_restrictions",
    "normalize_restriction_key",
    "normalize_restrictions",
    "recipe_is_allowed_for_profile",
]
