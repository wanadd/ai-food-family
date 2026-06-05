"""Tests for ingredient → shopping category inference."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

API_ROOT = Path(__file__).resolve().parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.services.shopping_categories import infer_category  # noqa: E402


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("Куриное филе", "мясо"),
        ("Фарш говяжий", "мясо"),
        ("Лосось", "рыба"),
        ("Креветки", "рыба"),
        ("Картофель", "овощи"),
        ("Морковь", "овощи"),
        ("Помидоры", "овощи"),
        ("Чеснок", "овощи"),
        ("Яблоки", "фрукты"),
        ("Банан", "фрукты"),
        ("Молоко 2.5%", "молочное"),
        ("Творог 5%", "молочное"),
        ("Сыр твёрдый", "молочное"),
        ("Яйца С1", "яйца"),
        ("Рис", "крупы"),
        ("Гречка", "крупы"),
        ("Макароны", "крупы"),
        ("Булгур", "крупы"),
        ("Хлеб белый", "хлеб"),
        ("Лаваш", "хлеб"),
        ("Мука пшеничная", "бакалея"),
        ("Сахар", "бакалея"),
        ("Соль", "бакалея"),
        ("Масло растительное", "бакалея"),
        ("Паприка", "специи"),
        ("Укроп свежий", "зелень"),
        ("Петрушка", "зелень"),
        ("Вода", "напитки"),
        ("Чай чёрный", "напитки"),
        ("Неизвестный продукт XYZ", "продукты"),
    ],
)
def test_infer_category_common_products(name: str, expected: str):
    assert infer_category(name, None) == expected
