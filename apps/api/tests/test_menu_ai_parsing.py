"""Tests for OpenAI replace-dish response normalization."""

from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

API_ROOT = Path(__file__).resolve().parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.schemas.menu import MenuMeal  # noqa: E402
from app.services.menu_ai_parsing import parse_replace_meal_response  # noqa: E402

FALLBACK = MenuMeal(
    meal_type="breakfast",
    name="Старый завтрак",
    description="Было",
    prep_time_minutes=10,
    calories_estimate=350,
)


def test_parse_standard_meal_object():
    result = parse_replace_meal_response(
        {
            "meal": {
                "meal_type": "breakfast",
                "name": "Блины с ягодами",
                "description": "Лёгкий завтрак",
                "prep_time_minutes": 15,
                "calories_estimate": 420,
            },
            "ingredients": [],
        },
        fallback_meal=FALLBACK,
    )
    assert result is not None
    assert result.meal_type == "breakfast"
    assert result.name == "Блины с ягодами"
    assert result.prep_time_minutes == 15
    assert result.calories_estimate == 420


def test_parse_shorthand_meal_type_key():
    result = parse_replace_meal_response(
        {"breakfast": "Блины с ягодами"},
        fallback_meal=FALLBACK,
    )
    assert result is not None
    assert result.meal_type == "breakfast"
    assert result.name == "Блины с ягодами"
    assert result.prep_time_minutes == 10
    assert result.calories_estimate == 350


def test_parse_nested_shorthand_under_meal():
    result = parse_replace_meal_response(
        {"meal": {"breakfast": "Омлет с сыром"}, "ingredients": []},
        fallback_meal=FALLBACK,
    )
    assert result is not None
    assert result.meal_type == "breakfast"
    assert result.name == "Омлет с сыром"


def test_parse_top_level_without_meal_wrapper():
    result = parse_replace_meal_response(
        {
            "meal_type": "lunch",
            "name": "Суп-пюре",
            "prep_time_minutes": 25,
        },
        fallback_meal=FALLBACK,
    )
    assert result is not None
    assert result.meal_type == "lunch"
    assert result.name == "Суп-пюре"
    assert result.prep_time_minutes == 25


def test_parse_uses_fallback_prep_and_calories():
    result = parse_replace_meal_response(
        {"meal": {"breakfast": "Творог с фруктами"}},
        fallback_meal=FALLBACK,
    )
    assert result is not None
    assert result.prep_time_minutes == 10
    assert result.calories_estimate == 350


def test_parse_invalid_returns_none():
    assert parse_replace_meal_response(None, fallback_meal=FALLBACK) is None
    assert parse_replace_meal_response({"foo": "bar"}, fallback_meal=FALLBACK) is None
