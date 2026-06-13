"""Tests for quality-first recipe catalog sorting (Stage Q2)."""

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
from app.services.recipes.catalog_sort import (  # noqa: E402
    catalog_quality_sort_key,
    sort_recipes_catalog,
)


def _recipe(
    *,
    rid: int,
    title: str,
    source_type: str = "import",
    hero_image_url: str | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        id=rid,
        title=title,
        source_type=source_type,
        hero_image_url=hero_image_url,
        suitable_for_sport=False,
        description="",
        meal_type="dinner",
        category="main",
        prep_time_minutes=20,
        cooking_time_minutes=20,
        servings=2,
        difficulty="easy",
        diets=[],
        is_drink=False,
        is_alcoholic=False,
        calories_per_serving=None,
        protein_g=None,
        suitable_for_children=True,
        suitable_for_event=False,
    )


def test_quality_sort_key_seed_with_hero_is_tier_zero():
    seed = _recipe(rid=265, title="Салат", source_type="seed", hero_image_url="/recipe-images/265/hero.webp")
    import_old = _recipe(rid=50, title="Ааа старый", source_type="import", hero_image_url="/x/hero.webp")
    assert catalog_quality_sort_key(seed)[0] < catalog_quality_sort_key(import_old)[0]


def test_seed_with_hero_ranks_above_import_with_hero():
    recipes = [
        _recipe(rid=40, title="Import soup", source_type="import", hero_image_url="/recipe-images/40/hero.webp"),
        _recipe(rid=256, title="Котлеты", source_type="seed", hero_image_url="/recipe-images/256/hero.webp"),
        _recipe(rid=257, title="Крупа", source_type="seed", hero_image_url="/recipe-images/257/hero.webp"),
    ]
    ordered = sort_recipes_catalog(recipes)
    assert [r.id for r in ordered[:2]] == [257, 256]


def test_seed_batch_256_265_above_old_import_without_images():
    recipes = [
        _recipe(rid=12, title="Борщ старый", source_type="import"),
        _recipe(rid=88, title="Каша import", source_type="import"),
        *[
            _recipe(
                rid=rid,
                title=f"Seed {rid}",
                source_type="seed",
                hero_image_url=f"/recipe-images/{rid}/hero.webp",
            )
            for rid in range(256, 266)
        ],
    ]
    ordered = sort_recipes_catalog(recipes)
    top_ids = [r.id for r in ordered[:10]]
    assert top_ids == list(range(265, 255, -1))


def test_title_sort_legacy_mode():
    recipes = [
        _recipe(rid=3, title="Яблоко", source_type="seed", hero_image_url="/a.webp"),
        _recipe(rid=1, title="Арбуз", source_type="import"),
    ]
    ordered = sort_recipes_catalog(recipes, sort="title")
    assert [r.title for r in ordered] == ["Арбуз", "Яблоко"]


def test_list_recipes_default_puts_seed_with_images_first():
    db = MagicMock()
    user = MagicMock(id=1)
    scope = AppScope(mode="personal", user_id=1, family_id=None)
    recipes = [
        _recipe(rid=10, title="Import без фото", source_type="import"),
        _recipe(rid=256, title="Котлеты с овощами", source_type="seed", hero_image_url="/recipe-images/256/hero.webp"),
        _recipe(rid=99, title="Import с фото", source_type="import", hero_image_url="/recipe-images/99/hero.webp"),
    ]

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
        result = catalog.list_recipes(db, user, scope=scope, limit=10)

    assert result.items[0].id == 256
    assert result.items[1].id == 99


def test_list_recipes_sort_title_preserves_alphabetical():
    db = MagicMock()
    user = MagicMock(id=1)
    scope = AppScope(mode="personal", user_id=1, family_id=None)
    recipes = [
        _recipe(rid=256, title="Я", source_type="seed", hero_image_url="/a.webp"),
        _recipe(rid=10, title="А", source_type="import"),
    ]

    with patch(
        "app.services.recipes.catalog.repository.favorite_ids_for_user",
        return_value=set(),
    ), patch(
        "app.services.recipes.catalog.repository.query_recipes",
        return_value=recipes,
    ), patch(
        "app.services.recipe_analysis.quick_recipe_fit_level",
        return_value=None,
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
        ),
    ):
        result = catalog.list_recipes(db, user, scope=scope, sort="title")

    assert [item.title for item in result.items] == ["А", "Я"]
