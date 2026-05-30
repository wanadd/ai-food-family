"""Regression tests for recipes catalog list and search."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

API_ROOT = Path(__file__).resolve().parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.schemas.recipe import RecipeSummary  # noqa: E402
from app.services.app_scope import AppScope  # noqa: E402
from app.services.recipes import catalog  # noqa: E402
from app.services.recipes.types import RecipeListFilters  # noqa: E402


def _recipe(title: str, *, active: bool = True) -> MagicMock:
    recipe = MagicMock()
    recipe.id = hash(title) % 10000
    recipe.title = title
    recipe.description = ""
    recipe.meal_type = "lunch"
    recipe.category = "main"
    recipe.is_active = active
    recipe.prep_time_minutes = 20
    recipe.cooking_time_minutes = 20
    recipe.servings = 2
    recipe.difficulty = "easy"
    recipe.diets = []
    recipe.is_drink = False
    recipe.is_alcoholic = False
    recipe.calories_per_serving = None
    recipe.protein_g = None
    recipe.suitable_for_children = True
    recipe.suitable_for_sport = False
    recipe.suitable_for_event = False
    return recipe


def test_list_recipes_returns_items():
    db = MagicMock()
    user = MagicMock(id=1)
    scope = AppScope(mode="personal", user_id=1, family_id=None)
    recipes = [_recipe("Куриный суп"), _recipe("Греческий салат")]

    with patch(
        "app.services.recipes.catalog.repository.favorite_ids_for_user",
        return_value=set(),
    ), patch(
        "app.services.recipes.catalog.repository.query_recipes",
        return_value=recipes,
    ), patch(
        "app.services.recipe_analysis.quick_recipe_fit_level",
        return_value="good",
    ), patch(
        "app.services.recipes.catalog.to_summary",
        side_effect=lambda recipe, _fav, fit_level=None: RecipeSummary(
            id=recipe.id,
            title=recipe.title,
            description="",
            meal_type="lunch",
            category="main",
            prep_time_minutes=20,
            servings=2,
            difficulty="easy",
            diets=[],
            tags=[],
            is_favorited=False,
            fit_level=fit_level,
        ),
    ):
        result = catalog.list_recipes(db, user, scope=scope)

    assert result.total == 2
    assert {item.title for item in result.items} == {"Куриный суп", "Греческий салат"}


def test_list_recipes_cyrillic_search_does_not_error():
    db = MagicMock()
    user = MagicMock(id=1)
    scope = AppScope(mode="personal", user_id=1, family_id=None)
    chicken = _recipe("Куриный суп")

    def _query(_db, filters: RecipeListFilters):
        assert filters.q == "курица"
        return [chicken]

    with patch(
        "app.services.recipes.catalog.repository.favorite_ids_for_user",
        return_value=set(),
    ), patch(
        "app.services.recipes.catalog.repository.query_recipes",
        side_effect=_query,
    ), patch(
        "app.services.recipe_analysis.quick_recipe_fit_level",
        return_value="good",
    ), patch(
        "app.services.recipes.catalog.to_summary",
        side_effect=lambda recipe, _fav, fit_level=None: RecipeSummary(
            id=recipe.id,
            title=recipe.title,
            description="",
            meal_type="lunch",
            category="main",
            prep_time_minutes=20,
            servings=2,
            difficulty="easy",
            diets=[],
            tags=[],
            is_favorited=False,
            fit_level=fit_level,
        ),
    ):
        result = catalog.list_recipes(db, user, q="курица", scope=scope)

    assert result.total == 1
    assert result.items[0].title == "Куриный суп"


def test_list_recipes_passes_recipe_to_fit_level():
    db = MagicMock()
    user = MagicMock(id=1)
    scope = AppScope(mode="personal", user_id=1, family_id=None)
    recipes = [_recipe("A"), _recipe("B")]
    seen: list[str] = []

    with patch(
        "app.services.recipes.catalog.repository.favorite_ids_for_user",
        return_value=set(),
    ), patch(
        "app.services.recipes.catalog.repository.query_recipes",
        return_value=recipes,
    ), patch(
        "app.services.recipe_analysis.quick_recipe_fit_level",
        side_effect=lambda _db, _user, _scope, recipe: seen.append(recipe.title)
        or "good",
    ), patch(
        "app.services.recipes.catalog.to_summary",
        side_effect=lambda recipe, _fav, fit_level=None: RecipeSummary(
            id=recipe.id,
            title=recipe.title,
            description="",
            meal_type="lunch",
            category="main",
            prep_time_minutes=20,
            servings=2,
            difficulty="easy",
            diets=[],
            tags=[],
            is_favorited=False,
            fit_level=fit_level,
        ),
    ):
        catalog.list_recipes(db, user, scope=scope)

    assert seen == ["A", "B"]
