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

from app.schemas.menu import MenuDayPlan, MenuIngredient, MenuMeal, MenuVariant  # noqa: E402
from app.services.app_scope import AppScope  # noqa: E402
from app.services.menu_recipe_plan import (  # noqa: E402
    add_recipe_to_plan,
    create_scaffold_menu,
    get_plan_for_date,
    make_slot_id,
    parse_slot_id,
    remove_menu_item,
    replace_recipe_in_slot,
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


def _db_with_recipes(*recipes: MagicMock) -> MagicMock:
    db = MagicMock()
    by_id = {recipe.id: recipe for recipe in recipes}
    db.get.side_effect = lambda _model, recipe_id: by_id.get(recipe_id)
    return db


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


@patch("app.services.menu.select_menu")
@patch("app.services.menu_recipe_plan.get_selected_menu")
@patch("app.services.recipe_storage.get_structured_ingredients", return_value=[])
def test_replace_existing_slot(_ingredients, get_selected, _select_menu):
    user = MagicMock(id=1)
    scope = AppScope(mode="personal", user_id=1, family_id=None)
    recipe_a = _recipe(recipe_id=174, title="Суп")
    recipe_b = _recipe(recipe_id=173, title="Салат")
    db = _db_with_recipes(recipe_a, recipe_b)
    scaffold = create_scaffold_menu(date(2026, 6, 5))
    selected = MagicMock()
    selected.menu = scaffold
    get_selected.return_value = selected

    def capture_menu(db, user, scope, request):
        selected.menu = request.menu

    _select_menu.side_effect = capture_menu

    add_recipe_to_plan(
        db, user, scope, recipe_a, plan_date="2026-06-05", meal_type="dinner", servings=2
    )
    item, menu = replace_recipe_in_slot(
        db, user, scope, recipe_b, slot_id="2026-06-05:dinner", servings=2
    )

    assert item["recipe_id"] == 173
    day = next(d for d in menu.days or [] if d.date_iso == "2026-06-05")
    dinner = next(m for m in day.meals if m.meal_type == "dinner")
    assert dinner.recipe_id == 173
    assert _select_menu.call_args.args[3].finalize_catalog is False


@patch("app.services.menu.select_menu")
@patch("app.services.menu_recipe_plan.get_selected_menu", return_value=None)
@patch("app.services.recipe_storage.get_structured_ingredients", return_value=[])
def test_replace_empty_slot_requires_existing_selected_menu(_ingredients, _selected, _select_menu):
    db = _db_with_recipes(_recipe(recipe_id=175))
    user = MagicMock(id=1)
    scope = AppScope(mode="personal", user_id=1, family_id=None)
    recipe = _recipe(recipe_id=175)

    with pytest.raises(ValueError, match="Меню не найдено"):
        replace_recipe_in_slot(
            db, user, scope, recipe, slot_id="2026-06-05:lunch", servings=2
        )

    _select_menu.assert_not_called()


@patch("app.services.menu.select_menu")
@patch("app.services.menu_recipe_plan.get_selected_menu")
@patch("app.services.recipe_storage.get_structured_ingredients", return_value=[])
def test_replace_one_slot_preserves_other_slots_and_days(
    _ingredients, get_selected, _select_menu
):
    user = MagicMock(id=1)
    scope = AppScope(mode="personal", user_id=1, family_id=None)
    breakfast = _recipe(recipe_id=1, title="Каша", meal_type="breakfast")
    lunch = _recipe(recipe_id=2, title="Суп", meal_type="lunch")
    dinner = _recipe(recipe_id=3, title="Рагу", meal_type="dinner")
    new_lunch = _recipe(recipe_id=4, title="Салат", meal_type="lunch")
    db = _db_with_recipes(breakfast, lunch, dinner, new_lunch)
    day_1_meals = [
        MenuMeal(
            meal_type="breakfast",
            name="Каша",
            description="",
            prep_time_minutes=10,
            recipe_id=1,
            servings=2,
            slot_id="2026-06-05:breakfast",
        ),
        MenuMeal(
            meal_type="lunch",
            name="Суп",
            description="",
            prep_time_minutes=20,
            recipe_id=2,
            servings=2,
            slot_id="2026-06-05:lunch",
        ),
        MenuMeal(
            meal_type="dinner",
            name="Рагу",
            description="",
            prep_time_minutes=30,
            recipe_id=3,
            servings=2,
            slot_id="2026-06-05:dinner",
        ),
    ]
    menu = MenuVariant(
        variant="balanced",
        title="Plan",
        explanation="",
        total_prep_minutes=60,
        meals=list(day_1_meals),
        ingredients=[MenuIngredient(name="Old product", amount="1 pc")],
        plan_days=7,
        days=[
            MenuDayPlan(
                day_index=1,
                label="Day 1",
                date_iso="2026-06-05",
                meals=day_1_meals,
            ),
            MenuDayPlan(
                day_index=2,
                label="Day 2",
                date_iso="2026-06-06",
                meals=[
                    MenuMeal(
                        meal_type="lunch",
                        name="Суп день 2",
                        description="",
                        prep_time_minutes=20,
                        recipe_id=2,
                        servings=2,
                        slot_id="2026-06-06:lunch",
                    )
                ],
            ),
        ],
    )
    before_day_2 = menu.days[1].model_dump(mode="json")
    selected = MagicMock()
    selected.menu = menu
    get_selected.return_value = selected

    item, updated = replace_recipe_in_slot(
        db, user, scope, new_lunch, slot_id="2026-06-05:lunch", servings=2
    )

    assert item["recipe_id"] == 4
    assert len(updated.days or []) == 2
    day_1 = next(d for d in updated.days or [] if d.date_iso == "2026-06-05")
    assert [meal.meal_type for meal in day_1.meals] == [
        "breakfast",
        "lunch",
        "dinner",
    ]
    assert [meal.recipe_id for meal in day_1.meals] == [1, 4, 3]
    assert updated.days[1].model_dump(mode="json") == before_day_2
    assert _select_menu.call_args.args[3].finalize_catalog is False


@patch("app.services.menu.select_menu")
@patch("app.services.menu_recipe_plan.get_selected_menu")
@patch("app.services.recipe_storage.get_structured_ingredients", return_value=[])
def test_remove_one_slot_does_not_match_other_day_by_meal_type(
    _ingredients, get_selected, _select_menu
):
    db = _db_with_recipes(_recipe(recipe_id=2))
    user = MagicMock(id=1)
    scope = AppScope(mode="personal", user_id=1, family_id=None)
    day_1_meals = [
        MenuMeal(
            meal_type="lunch",
            name="Суп",
            description="",
            prep_time_minutes=20,
            recipe_id=2,
            servings=2,
            slot_id="2026-06-05:lunch",
        )
    ]
    menu = MenuVariant(
        variant="balanced",
        title="Plan",
        explanation="",
        total_prep_minutes=20,
        meals=list(day_1_meals),
        ingredients=[MenuIngredient(name="Old product", amount="1 pc")],
        plan_days=2,
        days=[
            MenuDayPlan(
                day_index=1,
                label="Day 1",
                date_iso="2026-06-05",
                meals=day_1_meals,
            ),
            MenuDayPlan(
                day_index=2,
                label="Day 2",
                date_iso="2026-06-06",
                meals=[
                    MenuMeal(
                        meal_type="lunch",
                        name="Суп день 2",
                        description="",
                        prep_time_minutes=20,
                        recipe_id=2,
                        servings=2,
                        slot_id="2026-06-06:lunch",
                    )
                ],
            ),
        ],
    )
    selected = MagicMock()
    selected.menu = menu
    get_selected.return_value = selected

    updated = remove_menu_item(db, user, scope, "2026-06-05:lunch")

    day_1 = next(d for d in updated.days or [] if d.date_iso == "2026-06-05")
    day_2 = next(d for d in updated.days or [] if d.date_iso == "2026-06-06")
    assert day_1.meals[0].recipe_id is None
    assert day_2.meals[0].recipe_id == 2
    assert _select_menu.call_args.args[3].finalize_catalog is False


def test_parse_slot_id_valid():
    assert parse_slot_id("2026-06-05:dinner") == ("2026-06-05", "dinner")


def test_parse_slot_id_invalid_date():
    with pytest.raises(ValueError, match="YYYY-MM-DD"):
        parse_slot_id("not-a-date:dinner")


def test_parse_slot_id_unknown_meal_type_defaults_to_lunch():
    assert parse_slot_id("2026-06-05:brunch") == ("2026-06-05", "lunch")


def test_parse_slot_id_missing_colon():
    with pytest.raises(ValueError, match="Invalid"):
        parse_slot_id("2026-06-05dinner")
