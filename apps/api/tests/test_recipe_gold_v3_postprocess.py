"""Tests for Gold V3 recipe postprocess normalization."""

from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

API_ROOT = Path(__file__).resolve().parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.recipes.recipe_gold_v3_postprocess import (  # noqa: E402
    _normalize_category,
    _normalize_unit,
    postprocess_generated_recipe,
)


def test_normalize_unit_aliases():
    assert _normalize_unit("шт.") == "шт"
    assert _normalize_unit("ст. л.") == "ст.л."
    assert _normalize_unit("ч. ложка") == "ч.л."
    assert _normalize_unit("гр") == "г"


def test_normalize_category_aliases():
    assert _normalize_category("жиры") == "масла/соусы"
    assert _normalize_category("мясо птицы") == "мясо_птица"
    assert _normalize_category("другие") == "прочее"
