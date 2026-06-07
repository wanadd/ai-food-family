"""Tests for honest ingredient amount formatting (no fake 'шт')."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

API_ROOT = Path(__file__).resolve().parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.services.ingredient_format import (  # noqa: E402
    format_ingredient_amount,
    normalize_unit_display,
    sanitize_amount_text,
)
from app.services.recipe_storage import get_structured_ingredients  # noqa: E402

fmt = format_ingredient_amount


def test_basic_units():
    assert fmt("800", "г") == "800 г"
    assert fmt("1", "кг") == "1 кг"
    assert fmt("50", "мл") == "50 мл"
    assert fmt("5", "ст.л.") == "5 ст.л."
    assert fmt("1", "зубчик") == "1 зубчик"


def test_to_taste_drops_unit():
    assert fmt("по вкусу", "шт") == "по вкусу"
    assert fmt("1", "шт", is_to_taste_flag=True) == "по вкусу"
    assert fmt("1", "шт", quantity_mode="to_taste") == "по вкусу"
    assert fmt("1", "шт", is_to_taste_flag=True, quantity_text="по вкусу") == "по вкусу"


def test_nemnogo_and_pinch():
    assert fmt("немного", "шт") == "немного"
    assert fmt("щепотка", "шт") == "щепотка"
    assert fmt("щепотка", "") == "щепотка"
    assert fmt("1", "щепотка") == "1 щепотка"


def test_empty_unit_never_becomes_sht():
    assert fmt("2", "") == "2"
    assert fmt("2", None) == "2"
    assert "шт" not in fmt("0.5", "")


def test_empty_quantity_and_unit():
    assert fmt("", "") == ""
    assert fmt(None, None) == ""


def test_real_pieces_keep_sht():
    assert fmt("3", "шт") == "3 шт"


def test_normalize_unit_display():
    assert normalize_unit_display("ст. л.") == "ст.л."
    assert normalize_unit_display("ч. л.") == "ч.л."
    assert normalize_unit_display("зуб.") == "зубчик"
    assert normalize_unit_display("пуч.") == "пучок"
    assert normalize_unit_display("") == ""


def test_sanitize_legacy_amounts():
    assert sanitize_amount_text("по вкусу шт") == "по вкусу"
    assert sanitize_amount_text("800 г шт") == "800 г"
    assert sanitize_amount_text("5 ст.л. шт") == "5 ст.л."
    assert sanitize_amount_text("1 зубчик шт") == "1 зубчик"
    # real pieces stay
    assert sanitize_amount_text("5 шт") == "5 шт"
    assert sanitize_amount_text("2 банана") == "2 банана"


def _row(**kw):
    base = dict(
        name="X", quantity="1", unit="шт", category="other", is_optional=False,
        notes=None, quantity_mode=None, quantity_text=None, is_to_taste=False,
    )
    base.update(kw)
    return SimpleNamespace(**base)


def test_structured_ingredients_rows_to_taste():
    recipe = SimpleNamespace(
        ingredient_rows=[
            _row(name="Фарш куриный", quantity="800", unit="г"),
            _row(name="Чеснок", quantity="1", unit="зубчик"),
            _row(name="Соль", quantity="по вкусу", unit="шт", is_to_taste=True),
        ],
        ingredients=None,
    )
    out = {i["name"]: i["amount"] for i in get_structured_ingredients(recipe)}
    assert out["Фарш куриный"] == "800 г"
    assert out["Чеснок"] == "1 зубчик"
    assert out["Соль"] == "по вкусу"


def test_structured_ingredients_legacy_jsonb_sanitized():
    recipe = SimpleNamespace(
        ingredient_rows=[],
        ingredients=[
            {"name": "Соль", "amount": "по вкусу шт"},
            {"name": "Молоко", "amount": "50 мл"},
        ],
    )
    out = {i["name"]: i["amount"] for i in get_structured_ingredients(recipe)}
    assert out["Соль"] == "по вкусу"
    assert out["Молоко"] == "50 мл"
    assert "по вкусу шт" not in out.values()
