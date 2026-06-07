"""Ingredient display / name normalization — unified re-export surface.

Canonical implementations:
* display amount formatting — ``ingredient_format`` (never invents ``шт``);
* name keys for dedup — ``recipe_storage.normalize_name_key`` and
  ``shopping_item_utils.normalize_name``;
* recipe title normalization — ``recipes.title_normalize``.
"""

from __future__ import annotations

from app.services.ingredient_format import (
    format_ingredient_amount,
    is_to_taste,
    normalize_unit_display,
    sanitize_amount_text,
)
from app.services.recipe_storage import normalize_name_key
from app.services.shopping_item_utils import normalize_name

try:  # title_normalize is part of the recipe engine package
    from app.services.recipes.title_normalize import normalize_title
except Exception:  # pragma: no cover - defensive, keeps surface importable
    def normalize_title(value: str) -> str:  # type: ignore[misc]
        return (value or "").strip()


# Suspicious amount markers used by the project health audit. An ingredient
# display amount that still ends in a redundant "шт" after a real unit or a
# to-taste phrase indicates dirty legacy data.
def is_suspicious_amount(amount: str | None) -> bool:
    """True if a stored display amount looks like dirty legacy data."""
    raw = (amount or "").strip()
    if not raw:
        return False
    return sanitize_amount_text(raw) != raw


__all__ = [
    "format_ingredient_amount",
    "is_to_taste",
    "normalize_unit_display",
    "sanitize_amount_text",
    "normalize_name_key",
    "normalize_name",
    "normalize_title",
    "is_suspicious_amount",
]
