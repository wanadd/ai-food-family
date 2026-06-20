"""Tests for the unified menu->shopping normalization surface."""

from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

API_ROOT = Path(__file__).resolve().parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.services.normalization import ingredients, menu  # noqa: E402


def test_menu_reexports_resolve_to_canonical():
    from app.services import shopping_item_utils

    assert menu.item_from_menu_ingredient is shopping_item_utils.item_from_menu_ingredient
    assert menu.sum_menu_items is shopping_item_utils.sum_menu_items


def test_skip_pantry_staples():
    assert menu.should_skip_menu_ingredient_for_shopping("соль", "по вкусу") is True
    assert menu.should_skip_menu_ingredient_for_shopping("вода", "200 мл") is True


def test_keep_real_ingredient():
    assert menu.should_skip_menu_ingredient_for_shopping("куриная грудка", "500 г") is False


def test_item_from_menu_ingredient_builds_clean_item():
    item = menu.item_from_menu_ingredient("Яйцо куриное", "2 шт", "мясо_птица", None)
    assert item.category == "яйца"
    assert item.quantity == "2"
    assert item.unit == "шт"


def test_sum_menu_items_adds_quantities():
    a = menu.item_from_menu_ingredient("Молоко", "200 мл", "молочные", None)
    b = menu.item_from_menu_ingredient("Молоко", "300 мл", "молочные", None)
    summed = menu.sum_menu_items(a, b)
    assert summed.quantity == "500"


def test_format_ingredient_amount_never_invents_pieces():
    assert ingredients.format_ingredient_amount("по вкусу", None) == "по вкусу"
    assert ingredients.format_ingredient_amount("", "") == ""
    assert ingredients.format_ingredient_amount("2", "зубчик") == "2 зубчик"


def test_is_suspicious_amount_flags_redundant_pieces():
    assert ingredients.is_suspicious_amount("по вкусу шт") is True
    assert ingredients.is_suspicious_amount("800 г шт") is True
    assert ingredients.is_suspicious_amount("5 шт") is False
    assert ingredients.is_suspicious_amount("200 г") is False
