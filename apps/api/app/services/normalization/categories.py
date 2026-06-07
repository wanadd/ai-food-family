"""Shopping/food category normalization — unified re-export surface.

Canonical taxonomy lives in ``categories_v1`` (slugs + legacy migration map)
and ``shopping_categories`` (runtime inference). This module exposes the public
API so callers import categories from one place.
"""

from __future__ import annotations

from app.services.categories_v1 import (
    CANONICAL_SLUGS,
    CATEGORY_ORDER,
    DEFAULT_CATEGORY_SLUG,
    DEPRECATED_SYSTEM_SLUGS,
    FORBIDDEN_CATEGORY_SLUG,
    LEGACY_SLUG_MAP,
    map_legacy_slug,
    normalize_category_slug,
)
from app.services.shopping_categories import (
    infer_category,
    is_food_category,
    normalize_category,
)
from app.services.shopping_item_utils import normalize_shopping_category


def is_valid_category(slug: str | None) -> bool:
    """True if ``slug`` is already a canonical V1 category slug."""
    return bool(slug) and slug in CANONICAL_SLUGS


def is_deprecated_category(slug: str | None) -> bool:
    """True if ``slug`` is a slug that must not survive migration."""
    if not slug:
        return False
    return slug in DEPRECATED_SYSTEM_SLUGS or slug == FORBIDDEN_CATEGORY_SLUG


__all__ = [
    "CANONICAL_SLUGS",
    "CATEGORY_ORDER",
    "DEFAULT_CATEGORY_SLUG",
    "DEPRECATED_SYSTEM_SLUGS",
    "FORBIDDEN_CATEGORY_SLUG",
    "LEGACY_SLUG_MAP",
    "map_legacy_slug",
    "normalize_category_slug",
    "normalize_category",
    "infer_category",
    "is_food_category",
    "normalize_shopping_category",
    "is_valid_category",
    "is_deprecated_category",
]
