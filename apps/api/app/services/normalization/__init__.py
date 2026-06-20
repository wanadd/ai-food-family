"""PLANAM V1 unified normalization layer.

Single import surface for every "normalize / parse / validate" helper used
across the project. The goal of this package is **consolidation, not
re-implementation**: food helpers (amounts, units, categories, ingredients,
menu→shopping) simply re-export the existing canonical implementations so the
rest of the codebase has *one* place to import from instead of reaching into
``amount_parser`` / ``shopping_item_utils`` / ``ingredient_format`` /
``shopping_categories`` directly.

The profile / notifications / subscription modules contain new pure validators
that previously lived inline (or did not exist) and are now centralized here.

Design rules:
* Pure functions, no DB access (callers own persistence).
* Additive and backwards-compatible — existing canonical functions are
  untouched; this package wraps them.
* Never invent data (no fake ``шт`` units, no dropping of unknown-but-valid
  values).

See ``reports/planam_project_consolidation_audit.md`` (§ Normalization layer)
for the rationale and the migration plan for callers.
"""

from __future__ import annotations

from app.services.normalization import (
    amounts,
    categories,
    ingredients,
    menu,
    notifications,
    profile,
    shopping,
    subscription,
)

__all__ = [
    "amounts",
    "categories",
    "ingredients",
    "menu",
    "shopping",
    "profile",
    "notifications",
    "subscription",
]
