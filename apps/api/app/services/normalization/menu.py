"""Menu → shopping ingredient normalization — unified re-export surface.

Canonical implementation lives in ``shopping_item_utils``. These helpers turn a
menu ingredient (name + free-text amount + category hint) into a clean shopping
item, decide what to skip, and merge duplicates. Re-exported here so menu /
shopping / AI write-paths import from one place.
"""

from __future__ import annotations

from app.services.shopping_item_utils import (
    item_from_menu_ingredient,
    predict_menu_item_id,
    should_skip_menu_ingredient_for_shopping,
    sum_menu_items,
)

__all__ = [
    "should_skip_menu_ingredient_for_shopping",
    "predict_menu_item_id",
    "item_from_menu_ingredient",
    "sum_menu_items",
]
