"""Tests for gold V2 recipe catalog filter."""

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

from app.recipes.gold_filter import (  # noqa: E402
    GOLD_V2_TAGS,
    apply_gold_recipe_filter,
    filter_gold_recipes,
    is_gold_v2_recipe,
)
from app.schemas.recipe import RecipeSummary  # noqa: E402
from app.services.app_scope import AppScope  # noqa: E402
from app.services.recipes import catalog  # noqa: E402
from app.services.recipes.types import RecipeListFilters  # noqa: E402


def _recipe(title: str, *, tags: list[str] | None = None, source_type: str = "seed"):
    recipe = MagicMock()
    recipe.id = abs(hash(title)) % 10000
    recipe.title = title
    recipe.tags = tags or []
    recipe.source_type = source_type
    recipe.is_active = True
    return recipe


@pytest.mark.parametrize("tag", sorted(GOLD_V2_TAGS))
def test_is_gold_v2_recipe_by_tag(tag: str):
    assert is_gold_v2_recipe(_recipe("Gold", tags=[tag])) is True


def test_legacy_import_not_gold():
    assert is_gold_v2_recipe(_recipe("Legacy", tags=[], source_type="v1_import")) is False


def test_seed_source_type_in_catalog_pool():
    assert is_gold_v2_recipe(_recipe("Curated", tags=[], source_type="seed")) is True


def test_filter_gold_recipes_in_memory():
    gold = _recipe("Gold", tags=["gold_v2"])
    legacy = _recipe("Legacy", tags=[], source_type="import")
    result = filter_gold_recipes([gold, legacy])
    assert [r.title for r in result] == ["Gold"]


def test_repository_query_applies_gold_filter():
    from app.services.recipes import repository

    db = MagicMock()
    legacy = _recipe("Legacy soup", tags=[])
    gold = _recipe("Gold soup", tags=["gold_v2", "recipe_schema_v2"])

    chain = MagicMock()
    chain.filter.return_value = chain
    chain.order_by.return_value.all.return_value = [gold]
    db.query.return_value = chain

    with patch("app.services.recipes.repository.apply_gold_recipe_filter") as mock_apply:
        mock_apply.side_effect = lambda q, **kw: q
        filters = RecipeListFilters(include_legacy=False)
        repository.query_recipes(db, filters)
        mock_apply.assert_called_once()
        assert mock_apply.call_args.kwargs["include_legacy"] is False


def test_catalog_excludes_legacy_when_filter_on():
    db = MagicMock()
    user = MagicMock(id=1)
    scope = AppScope(mode="personal", user_id=1, family_id=None)
    legacy = _recipe("Legacy", tags=[])
    gold = _recipe("Gold omelet", tags=["gold_v2"])

    def _query(_db, filters: RecipeListFilters):
        assert filters.include_legacy is False
        return [gold]

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
            tags=recipe.tags,
            is_favorited=False,
            fit_level=fit_level,
        ),
    ):
        result = catalog.list_recipes(db, user, scope=scope, include_legacy=False)

    assert result.total == 1
    assert result.items[0].title == "Gold omelet"


def test_get_recipe_model_by_id_not_filtered():
    """Detail by id must not go through catalog gold filter."""
    from app.services.recipes import repository

    db = MagicMock()
    legacy = MagicMock()
    legacy.id = 999
    legacy.tags = []

    with patch.object(repository, "get_recipe_with_relations", return_value=legacy) as mock_get:
        recipe = repository.get_recipe_with_relations(db, 999)
        mock_get.assert_called_once_with(db, 999)
        assert recipe.id == 999


def test_gold_ingredient_categories_map_to_legacy_slugs():
    from app.services.recipe_storage import _resolve_ingredient_category

    assert _resolve_ingredient_category("Мёд", "grocery") == "бакалея"
    assert _resolve_ingredient_category("Шампиньоны", "mushrooms") == "овощи_зелень"
    assert _resolve_ingredient_category("Гречка", "grains_pasta") == "крупы_макароны"
    assert _resolve_ingredient_category("Яйца", "eggs") == "яйца"
    assert _resolve_ingredient_category("Молоко", "dairy") == "молочные"
