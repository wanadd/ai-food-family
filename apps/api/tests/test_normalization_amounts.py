"""Tests for the unified amounts/units normalization surface."""

from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

API_ROOT = Path(__file__).resolve().parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.services.normalization import amounts  # noqa: E402


def test_reexports_resolve_to_canonical():
    from app.services import amount_parser, ingredient_format, shopping_item_utils

    assert amounts.normalize_unit is amount_parser.normalize_unit
    assert amounts.parse_amount is amount_parser.parse_amount
    assert amounts.normalize_unit_display is ingredient_format.normalize_unit_display
    assert amounts.normalize_shopping_unit is shopping_item_utils.normalize_shopping_unit


def test_normalize_unit_canonical():
    assert amounts.normalize_unit("гр") == "г"
    assert amounts.normalize_unit("ШТ") == "шт"


def test_display_unit_never_invents_pieces():
    # ingredient_format display normalizer must keep empty empty
    assert amounts.normalize_unit_display("") == ""
    assert amounts.normalize_unit_display("гр") == "г"


def test_shopping_unit_expands_abbreviations():
    assert amounts.normalize_shopping_unit("пуч.") == "пучок"
    assert amounts.normalize_shopping_unit("ст. л.") == "ст.л."


def test_parse_shopping_amount_fraction():
    value, unit = amounts.parse_shopping_amount("1/2 ст.л.")
    assert value == 0.5
    assert unit == "ст.л."


def test_clean_float_strips_garbage():
    assert amounts.clean_float(0.6000000000000001) == 0.6
    assert amounts.clean_float(2.0) == 2.0


def test_normalize_shopping_quantity_rounds_pieces_up():
    qty, unit = amounts.normalize_shopping_quantity("1.2", "шт", "яйцо")
    assert qty == "2"
    assert unit == "шт"
