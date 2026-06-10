"""Tests for Recipe V2 validation."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

API_ROOT = Path(__file__).resolve().parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.recipes.recipe_v2_validation import validate_recipe_v2  # noqa: E402


def _minimal_recipe(**overrides):
    base = {
        "title": "Тестовый суп",
        "meal_types": ["lunch"],
        "category": "soup",
        "servings": 2,
        "prep_time_minutes": 5,
        "cook_time_minutes": 20,
        "nutrition_summary": {
            "calories": 200,
            "protein_g": 10,
            "fat_g": 5,
            "carbs_g": 25,
            "confidence": "estimated",
        },
        "ingredients": [
            {
                "display_name": "Морковь",
                "canonical_name": "морковь",
                "canonical_slug": "carrot",
                "amount": 1,
                "unit": "шт",
                "shopping_category_slug": "vegetables_greens",
            }
        ],
        "steps": [{"order": 1, "instruction": "Сварить."}],
    }
    base.update(overrides)
    return base


def test_valid_minimal_recipe():
    result = validate_recipe_v2(_minimal_recipe())
    assert result["valid"] is True
    assert not result["errors"]


def test_rejects_empty_title():
    result = validate_recipe_v2(_minimal_recipe(title=""))
    assert result["valid"] is False
    assert any("title" in e for e in result["errors"])


def test_rejects_quantity_in_ingredient_name():
    result = validate_recipe_v2(
        _minimal_recipe(
            ingredients=[
                {
                    "display_name": "капуста 1 л",
                    "amount": 1,
                    "unit": "шт",
                }
            ]
        )
    )
    assert result["valid"] is False


def test_rejects_bad_unit():
    result = validate_recipe_v2(
        _minimal_recipe(
            ingredients=[
                {
                    "display_name": "Мука",
                    "amount": 200,
                    "unit": "гр.",
                }
            ]
        )
    )
    assert result["valid"] is False


def test_rejects_pcs_for_flour():
    result = validate_recipe_v2(
        _minimal_recipe(
            ingredients=[
                {
                    "display_name": "Мука пшеничная",
                    "canonical_slug": "flour",
                    "amount": 1,
                    "unit": "шт",
                }
            ]
        )
    )
    assert result["valid"] is False


def test_rejects_missing_nutrition_without_unavailable():
    result = validate_recipe_v2(
        _minimal_recipe(nutrition_summary={"confidence": "estimated"})
    )
    assert result["valid"] is False


def test_allows_unavailable_nutrition():
    result = validate_recipe_v2(
        _minimal_recipe(
            nutrition_summary={"confidence": "unavailable"},
        )
    )
    assert result["valid"] is True


def test_rejects_duplicate_canonical_slug():
    ing = {
        "display_name": "Лук",
        "canonical_slug": "onion",
        "amount": 1,
        "unit": "шт",
    }
    result = validate_recipe_v2(_minimal_recipe(ingredients=[ing, ing]))
    assert result["valid"] is False
