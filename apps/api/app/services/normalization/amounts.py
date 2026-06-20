"""Amount / unit normalization — unified re-export surface.

Delegates to the canonical implementations. There are intentionally three unit
normalizers in the codebase because they serve different display contexts; this
module documents and exposes all three under one import so callers stop reaching
into individual modules:

* ``normalize_unit``          — storage/canonical units (``amount_parser``).
* ``normalize_unit_display``  — recipe UI display, never invents ``шт``
  (``ingredient_format``).
* ``normalize_shopping_unit`` — shopping display (``пуч.`` → ``пучок``)
  (``shopping_item_utils``).

Do not duplicate logic here — change the canonical module instead.
"""

from __future__ import annotations

from app.services.amount_parser import (
    format_amount,
    merge_amount_strings,
    normalize_unit,
    parse_amount,
)
from app.services.ingredient_format import normalize_unit_display
from app.services.shopping_item_utils import (
    clean_float,
    normalize_shopping_quantity,
    normalize_shopping_unit,
    parse_shopping_amount,
)

__all__ = [
    "normalize_unit",
    "parse_amount",
    "format_amount",
    "merge_amount_strings",
    "normalize_unit_display",
    "normalize_shopping_unit",
    "parse_shopping_amount",
    "normalize_shopping_quantity",
    "clean_float",
]
