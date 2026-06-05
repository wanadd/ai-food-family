"""Tests for recipe → daily menu plan integration."""

from __future__ import annotations

import os
import sys
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

API_ROOT = Path(__file__).resolve().parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.schemas.menu import MenuVariant  # noqa: E402
from app.services.app_scope import AppScope  # noqa: E402
from app.services.menu_recipe_plan import (  # noqa: E402
    add_recipe_to_plan,
    create_scaffold_menu,
    get_plan_for_date,
    make_slot_id,
    remove_menu_item,
)


def _recipe(
    *,
    recipe_id: int = 174,
    title: str = "Куриный суп",
    meal_type: str = "lunch",
) -> MagicMock:
    recipe = MagicMock()
    recipe.id = recipe_id
    recipe.title = title
    recipe.display_title = None
    recipe.original_title = title
    recipe.description = "Описание"
    recipe.meal_type = meal_type
    recipe.prep_time_minutes = 30
    recipe.cooking_time_minutes = 30
    recipe.servings = 4
    recipe.calories_per_serving = 320.0
    recipe.ingredients = []
    recipe.ingredient_rows = []
    return recipe


def test_create_scaffold_menu_has_week_days():
    menu = create_scaffold_menu(date(2026, 6, 5))
    assert menu.plan_days == 7
    assert menu.days is not None
    assert len(menu.days) == 7
    assert menu.days[0].date_iso == "2026-06-05"
    assert len(menu.days[0].meals) == 4


def test_make_slot_id_format():
    assert make_slot_id("2026-06-05", "dinner") == "2026-06-05:dinner"


@patch("app.services.menu.select_menu")
@patch("app.services.menu_recipe_plan.get_selected_menu", return_value=None)
@patch("app.services.recipe_storage.get_structured_ingredients", return_value=[])
def test_add_recipe_creates_menu(_ingredients, _selected, _select_menu):
    db = MagicMock()
    user = MagicMock(id=1)
    scope = AppScope(mode="personal", user_id=1, family_id=None)
    recipe = _recipe()

    item, menu, created = add_recipe_to_plan(
        db,
        user,
        scope,
        recipe,
        plan_date="2026-06-05",
        meal_type="dinner",
        servings=2,
    )

    assert created is True
    assert item["recipe_id"] == 174
    assert item["meal_type"] == "dinner"
    assert item["slot_id"] == "2026-06-05:dinner"
    assert menu.days is not None
    _select_menu.assert_called_once()


@patch("app.services.menu.select_menu")
@patch("app.services.menu_recipe_plan.get_selected_menu")
@patch("app.services.recipe_storage.get_structured_ingredients", return_value=[])
def test_add_recipe_duplicate_returns_existing(_ingredients, get_selected, _select_menu):
    db = MagicMock()
    user = MagicMock(id=1)
    scope = AppScope(mode="personal", user_id=1, family_id=None)
    recipe = _recipe()
    scaffold = create_scaffold_menu(date(2026, 6, 5))

    selected = MagicMock()
    selected.menu = scaffold
    get_selected.return_value = selected

    def capture_menu(db, user, scope, request):
        selected.menu = request.menu

    _select_menu.side_effect = capture_menu

    add_recipe_to_plan(
        db, user, scope, recipe, plan_date="2026-06-05", meal_type="dinner", servings=2
    )
    item, _menu, created = add_recipe_to_plan(
        db, user, scope, recipe, plan_date="2026-06-05", meal_type="dinner", servings=2
    )

    assert created is False
    assert item["recipe_id"] == 174


@patch("app.services.menu_recipe_plan.get_selected_menu", return_value=None)
def test_get_plan_for_date_empty(_selected):
    db = MagicMock()
    scope = AppScope(mode="personal", user_id=1, family_id=None)

    date_iso, items, menu = get_plan_for_date(db, scope, plan_date="2026-06-05")

    assert date_iso == "2026-06-05"
    assert items == []
    assert menu is None


@patch("app.services.menu.select_menu")
@patch("app.services.menu_recipe_plan.get_selected_menu")
@patch("app.services.recipe_storage.get_structured_ingredients", return_value=[])
def test_remove_menu_item_clears_slot(_ingredients, get_selected, _select_menu):
    db = MagicMock()
    user = MagicMock(id=1)
    scope = AppScope(mode="personal", user_id=1, family_id=None)
    recipe = _recipe()
    scaffold = create_scaffold_menu(date(2026, 6, 5))
    selected = MagicMock()
    selected.menu = scaffold
    get_selected.return_value = selected

    add_recipe_to_plan(
        db, user, scope, recipe, plan_date="2026-06-05", meal_type="dinner", servings=2
    )
    updated = remove_menu_item(db, user, scope, "2026-06-05:dinner")
    day = next(d for d in updated.days or [] if d.date_iso == "2026-06-05")
    dinner = next(m for m in day.meals if m.meal_type == "dinner")
    assert dinner.recipe_id is None
    assert dinner.name == "Свободно"
