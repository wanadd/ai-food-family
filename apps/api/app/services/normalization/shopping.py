"""Shopping list item normalization — unified re-export surface.

Canonical implementation lives in ``shopping_item_utils``. Re-exported here so
shopping CRUD / sync write-paths import item helpers from one place.
"""

from __future__ import annotations

from app.services.shopping_item_utils import (
    display_amount,
    make_item_id,
    new_manual_item_id,
    normalize_item,
    normalize_name,
)

__all__ = [
    "normalize_item",
    "display_amount",
    "make_item_id",
    "new_manual_item_id",
    "normalize_name",
]
