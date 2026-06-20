"""Tests for Recipe V2 product taxonomy."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

API_ROOT = Path(__file__).resolve().parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.recipes.product_taxonomy import (  # noqa: E402
    SHOPPING_CATEGORIES_V2,
    infer_shopping_category_v2,
    legacy_shopping_slug,
)


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("Шампиньоны", "mushrooms"),
        ("Мёд", "grocery"),
        ("Мед цветочный", "grocery"),
        ("Оливковое масло", "grocery"),
        ("Гречка", "grains_pasta"),
        ("Рис basmati", "grains_pasta"),
        ("Яйца", "eggs"),
        ("Куриное филе", "meat_poultry"),
        ("Индейка", "meat_poultry"),
        ("Лосось", "fish_seafood"),
        ("Треска", "fish_seafood"),
        ("Молоко 2.5%", "dairy"),
        ("Творог", "dairy"),
        ("Укроп", "vegetables_greens"),
        ("Петрушка", "vegetables_greens"),
        ("Кинза", "vegetables_greens"),
        ("Неизвестный продукт XYZ", "other"),
    ],
)
def test_infer_shopping_category_v2(name: str, expected: str):
    assert infer_shopping_category_v2(name) == expected
    assert expected in SHOPPING_CATEGORIES_V2


def test_legacy_shopping_slug_maps_v2_to_russian():
    assert legacy_shopping_slug("meat_poultry") == "мясо_птица"
    assert legacy_shopping_slug("grains_pasta") == "крупы_макароны"
    assert legacy_shopping_slug("unknown") == "другое"
