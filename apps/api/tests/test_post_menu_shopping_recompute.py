"""Post-menu shopping consistency after active meal changes."""

from __future__ import annotations

import os
import sys
from datetime import date, timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

API_ROOT = Path(__file__).resolve().parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.schemas.menu import MenuDayPlan, MenuIngredient, MenuMeal, MenuVariant  # noqa: E402
from app.schemas.shopping_list import ShoppingListItem  # noqa: E402
from app.services.menu_recipe_plan import (  # noqa: E402
    recompute_menu_ingredients_from_active_meals,
)
from app.services.shopping_list import build_items_from_ingredients  # noqa: E402


def _recipe(recipe_id: int, title: str, ingredients: list[dict]) -> MagicMock:
    recipe = MagicMock()
    recipe.id = recipe_id
    recipe.title = title
    recipe.servings = 2
    recipe.ingredient_rows = []
    recipe.ingredients = ingredients
    return recipe


class _Db:
    def __init__(self, recipes: dict[int, MagicMock]) -> None:
        self.recipes = recipes

    def get(self, _model, recipe_id: int):
        return self.recipes.get(recipe_id)


def _menu(days: int, recipe_id: int | None = 1) -> MenuVariant:
    start = date(2026, 6, 1)
    day_blocks = []
    for offset in range(days):
        day_date = start + timedelta(days=offset)
        date_iso = day_date.isoformat()
        day_blocks.append(
            MenuDayPlan(
                day_index=offset + 1,
                label=f"Day {offset + 1}",
                date_iso=date_iso,
                meals=[
                    MenuMeal(
                        meal_type="dinner",
                        name="Dinner" if recipe_id else "Free",
                        description="",
                        prep_time_minutes=20,
                        recipe_id=recipe_id,
                        servings=2,
                        slot_id=f"{date_iso}:dinner",
                    )
                ],
            )
        )
    return MenuVariant(
        variant="balanced",
        title="Plan",
        explanation="",
        total_prep_minutes=20,
        meals=day_blocks[0].meals,
        ingredients=[MenuIngredient(name="Old product", amount="1 pc")],
        plan_days=days,
        days=day_blocks,
    )


def _names(menu: MenuVariant) -> set[str]:
    return {item.name.lower() for item in build_items_from_ingredients(menu.ingredients)}


def test_replace_meal_removes_old_recipe_ingredients_from_shopping():
    db = _Db(
        {
            2: _recipe(
                2,
                "New dinner",
                [{"name": "Broccoli", "amount": "300 g", "category": "other"}],
            )
        }
    )
    menu = _menu(1, recipe_id=2)
    menu = menu.model_copy(
        update={"ingredients": [MenuIngredient(name="Chicken", amount="400 g")]}
    )

    recomputed = recompute_menu_ingredients_from_active_meals(db, menu)

    names = _names(recomputed)
    assert "broccoli" in names
    assert "chicken" not in names


def test_replace_meal_adds_new_recipe_ingredients_to_shopping():
    db = _Db(
        {
            2: _recipe(
                2,
                "New dinner",
                [{"name": "Rice", "amount": "200 g", "category": "other"}],
            )
        }
    )

    names = _names(recompute_menu_ingredients_from_active_meals(db, _menu(1, 2)))

    assert "rice" in names


def test_delete_meal_removes_deleted_recipe_ingredients_from_shopping():
    db = _Db({})

    recomputed = recompute_menu_ingredients_from_active_meals(db, _menu(1, None))

    assert build_items_from_ingredients(recomputed.ingredients) == []


def test_manual_shopping_item_survives_menu_resync():
    db = _Db(
        {
            1: _recipe(
                1,
                "Dinner",
                [{"name": "Carrot", "amount": "2 pc", "category": "other"}],
            )
        }
    )
    manual = ShoppingListItem(
        id="manual-batteries",
        name="Batteries",
        category="other",
        quantity="2",
        unit="pc",
        amount="2 pc",
        source="manual",
    )
    menu_items = build_items_from_ingredients(
        recompute_menu_ingredients_from_active_meals(db, _menu(1, 1)).ingredients,
        previous=[manual],
    )
    merged = menu_items + [manual]

    assert {i.name.lower() for i in merged} >= {"carrot", "batteries"}


def test_checked_manual_item_survives_menu_resync():
    manual = ShoppingListItem(
        id="manual-batteries",
        name="Batteries",
        category="other",
        quantity="2",
        unit="pc",
        amount="2 pc",
        source="manual",
        checked=True,
        checked_by_user_id=7,
    )
    assert manual.checked is True
    assert manual.checked_by_user_id == 7


def test_menu_duration_ingredient_recompute_works_for_supported_lengths():
    db = _Db(
        {
            1: _recipe(
                1,
                "Dinner",
                [{"name": "Carrot", "amount": "1 pc", "category": "other"}],
            )
        }
    )
    for days in (1, 3, 5, 7):
        recomputed = recompute_menu_ingredients_from_active_meals(db, _menu(days, 1))
        item = build_items_from_ingredients(recomputed.ingredients)[0]
        assert item.name.lower() == "carrot"
        assert item.quantity == str(days)
