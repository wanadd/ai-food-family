"""Tests for catalog-ready default pool (Stage Q3)."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

API_ROOT = Path(__file__).resolve().parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.schemas.recipe import RecipeSummary  # noqa: E402
from app.services.app_scope import AppScope  # noqa: E402
from app.services.recipes import catalog  # noqa: E402
from app.services.recipes.catalog_ready import (  # noqa: E402
    CATALOG_READY_SOURCE_TYPES,
    GOLD_V3_CATALOG_READY_TAGS,
    filter_catalog_ready_recipes,
    is_catalog_ready_recipe,
)
from app.services.recipes.types import RecipeListFilters  # noqa: E402


def _recipe(
    *,
    rid: int,
    title: str,
    source_type: str = "import",
    hero_image_url: str | None = None,
    tags: list[str] | None = None,
):
    return SimpleNamespace(
        id=rid,
        title=title,
        source_type=source_type,
        hero_image_url=hero_image_url,
        tags=tags or [],
        tag_rows=[],
        is_active=True,
    )


def test_catalog_ready_source_types():
    assert "seed" in CATALOG_READY_SOURCE_TYPES
    assert "import" not in CATALOG_READY_SOURCE_TYPES
    assert "gold_v3" in GOLD_V3_CATALOG_READY_TAGS


@pytest.mark.parametrize(
    "source_type,hero,expected",
    [
        ("seed", "/recipe-images/256/hero.webp", True),
        ("generated_original", "/recipe-images/1/hero.webp", True),
        ("manual_original", "/recipe-images/2/hero.webp", True),
        ("seed", None, False),
        ("seed", "", False),
        ("import", "/recipe-images/99/hero.webp", False),
        ("v1_import", "/recipe-images/99/hero.webp", False),
    ],
)
def test_is_catalog_ready_recipe(source_type, hero, expected):
    recipe = _recipe(rid=1, title="Test", source_type=source_type, hero_image_url=hero)
    assert is_catalog_ready_recipe(recipe) is expected


def test_filter_catalog_ready_hides_legacy_import_without_hero():
    recipes = [
        _recipe(rid=12, title="Old import", source_type="import"),
        _recipe(rid=256, title="Seed", source_type="seed", hero_image_url="/a.webp"),
    ]
    result = filter_catalog_ready_recipes(recipes)
    assert [r.id for r in result] == [256]


def test_filter_catalog_ready_includes_gold_v3_import_with_hero():
    recipes = [
        _recipe(
            rid=227,
            title="Gold V3 import",
            source_type="import",
            hero_image_url="/recipe-images/227/hero.webp",
            tags=["gold_v3", "recipe_schema_v3", "upgraded_from_legacy"],
        ),
        _recipe(
            rid=20,
            title="Legacy import with photo",
            source_type="import",
            hero_image_url="/recipe-images/20/hero.webp",
        ),
    ]
    result = filter_catalog_ready_recipes(recipes)
    assert [r.id for r in result] == [227]


def test_filter_catalog_ready_include_legacy_returns_all():
    recipes = [
        _recipe(rid=12, title="Old import", source_type="import"),
        _recipe(rid=256, title="Seed", source_type="seed", hero_image_url="/a.webp"),
    ]
    result = filter_catalog_ready_recipes(recipes, include_legacy=True)
    assert [r.id for r in result] == [12, 256]


def test_seed_batch_256_265_only_in_default_pool():
    recipes = [
        *[
            _recipe(
                rid=rid,
                title=f"Seed {rid}",
                source_type="seed",
                hero_image_url=f"/recipe-images/{rid}/hero.webp",
            )
            for rid in range(256, 266)
        ],
        _recipe(rid=10, title="Import no photo", source_type="import"),
        _recipe(rid=20, title="Import with photo", source_type="import", hero_image_url="/x.webp"),
    ]
    result = filter_catalog_ready_recipes(recipes)
    assert len(result) == 10
    assert {r.id for r in result} == set(range(256, 266))


def test_gold_v3_batch_2_227_265_visible_in_default_pool():
    recipes = [
        _recipe(rid=2, title="Gold 2", source_type="import", hero_image_url="/2.webp", tags=["gold_v3"]),
        *[
            _recipe(
                rid=rid,
                title=f"Gold {rid}",
                source_type="import",
                hero_image_url=f"/recipe-images/{rid}/hero.webp",
                tags=["gold_v3", "recipe_schema_v3"],
            )
            for rid in range(227, 256)
        ],
        *[
            _recipe(
                rid=rid,
                title=f"Seed {rid}",
                source_type="seed",
                hero_image_url=f"/recipe-images/{rid}/hero.webp",
                tags=["gold_v3", "recipe_schema_v3"],
            )
            for rid in range(256, 266)
        ],
        _recipe(rid=20, title="Legacy import with photo", source_type="import", hero_image_url="/x.webp"),
    ]
    result = filter_catalog_ready_recipes(recipes)
    assert len(result) == 40
    assert {r.id for r in result} == {2, *range(227, 266)}


def test_repository_query_applies_catalog_ready_filter():
    from app.services.recipes import repository

    db = MagicMock()
    chain = MagicMock()
    chain.filter.return_value = chain
    chain.order_by.return_value.all.return_value = []
    db.query.return_value = chain

    with patch("app.services.recipes.repository.apply_catalog_ready_filter") as mock_apply:
        mock_apply.side_effect = lambda q, **kw: q
        repository.query_recipes(db, RecipeListFilters(include_legacy=False))
        mock_apply.assert_called_once()
        assert mock_apply.call_args.kwargs["include_legacy"] is False


def test_list_recipes_default_returns_only_catalog_ready_from_repository():
    db = MagicMock()
    user = MagicMock(id=1)
    scope = AppScope(mode="personal", user_id=1, family_id=None)
    catalog_ready = [
        _recipe(
            rid=rid,
            title=f"Seed {rid}",
            source_type="seed",
            hero_image_url=f"/recipe-images/{rid}/hero.webp",
        )
        for rid in range(256, 266)
    ]

    with patch(
        "app.services.recipes.catalog.repository.favorite_ids_for_user",
        return_value=set(),
    ), patch(
        "app.services.recipes.catalog.repository.query_recipes",
        return_value=catalog_ready,
    ), patch(
        "app.services.recipe_analysis.quick_recipe_fit_level",
        return_value="good",
    ), patch(
        "app.services.recipes.catalog.to_summary",
        side_effect=lambda recipe, _fav, fit_level=None: RecipeSummary(
            id=recipe.id,
            title=recipe.title,
            description="",
            meal_type="dinner",
            category="main",
            prep_time_minutes=20,
            servings=2,
            difficulty="easy",
            diets=[],
            tags=[],
            is_favorited=False,
            fit_level=fit_level,
            hero_image_url=recipe.hero_image_url,
        ),
    ):
        result = catalog.list_recipes(db, user, scope=scope, limit=200)

    assert result.total == 10
    assert len(result.items) == 10
    assert result.items[0].id == 265
