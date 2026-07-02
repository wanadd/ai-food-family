"""Tests for Gold V3 menu catalog enrichment hotfix."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

API_ROOT = Path(__file__).resolve().parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.schemas.menu import MenuDayPlan, MenuIngredient, MenuMeal, MenuVariant  # noqa: E402
from app.services.menu_catalog_enrichment import finalize_menu_variant  # noqa: E402
from app.services.menu_catalog_pool import meal_from_catalog_recipe  # noqa: E402


def _catalog_recipe(
    recipe_id: int,
    *,
    meal_type: str,
    title: str,
    display_title: str | None = None,
) -> MagicMock:
    recipe = MagicMock()
    recipe.id = recipe_id
    recipe.is_active = True
    recipe.source_type = "seed"
    recipe.title = title
    recipe.display_title = display_title
    recipe.description = f"Описание {title}"
    recipe.meal_type = meal_type
    recipe.cooking_time_minutes = 30
    recipe.prep_time_minutes = 20
    recipe.calories_per_serving = 300
    recipe.hero_image_url = f"/recipe-images/{recipe_id}/hero.webp"
    recipe.image_url = f"/recipe-images/{recipe_id}/card_800.webp"
    recipe.thumbnail_url = f"/recipe-images/{recipe_id}/thumb_400.webp"
    return recipe


def _adhoc_variant() -> MenuVariant:
    meals = [
        MenuMeal(
            meal_type="breakfast",
            name="Йогурт с ягодами и гранолой",
            description="",
            prep_time_minutes=10,
            recipe_id=None,
        ),
        MenuMeal(
            meal_type="lunch",
            name="Куриные котлеты с гречкой",
            description="",
            prep_time_minutes=40,
            recipe_id=None,
        ),
        MenuMeal(
            meal_type="dinner",
            name="Омлет с овощами",
            description="",
            prep_time_minutes=25,
            recipe_id=None,
        ),
    ]
    return MenuVariant(
        variant="balanced",
        title="Тест",
        explanation="test",
        total_prep_minutes=75,
        meals=meals,
        ingredients=[MenuIngredient(name="Вода", amount="1 л")],
        plan_days=7,
        days=[
            MenuDayPlan(day_index=1, label="День 1", date_iso="2026-06-10", meals=meals),
            MenuDayPlan(
                day_index=2,
                label="День 2",
                date_iso="2026-06-11",
                meals=[
                    MenuMeal(
                        meal_type="breakfast",
                        name="Перловка",
                        description="",
                        prep_time_minutes=30,
                        recipe_id=257,
                    ),
                    MenuMeal(
                        meal_type="lunch",
                        name="Суп",
                        description="",
                        prep_time_minutes=40,
                        recipe_id=258,
                        image_url="/recipe-images/258/card_800.webp",
                    ),
                    MenuMeal(
                        meal_type="dinner",
                        name="Курица",
                        description="",
                        prep_time_minutes=35,
                        recipe_id=259,
                        image_url="/recipe-images/259/card_800.webp",
                    ),
                ],
            ),
        ],
    )


@patch("app.services.menu_catalog_enrichment.load_menu_catalog_pool")
def test_day_zero_has_no_null_recipe_id_when_pool_available(mock_pool):
    mock_pool.return_value = [
        _catalog_recipe(256, meal_type="breakfast", title="Куриные котлеты"),
        _catalog_recipe(257, meal_type="lunch", title="Перловка с брокколи"),
        _catalog_recipe(258, meal_type="dinner", title="Куриный суп"),
        _catalog_recipe(259, meal_type="dinner", title="Курица с яблоками"),
    ]
    db = MagicMock()
    user = MagicMock()

    result = finalize_menu_variant(db, _adhoc_variant(), user=user, persons=2)

    day0 = result.days[0].meals
    assert all(meal.recipe_id is not None for meal in day0)
    assert all(meal.image_url for meal in day0)


@patch("app.services.menu_catalog_enrichment.load_menu_catalog_pool")
def test_all_days_have_recipe_id(mock_pool):
    mock_pool.return_value = [
        _catalog_recipe(256, meal_type="breakfast", title="A"),
        _catalog_recipe(257, meal_type="lunch", title="B"),
        _catalog_recipe(258, meal_type="dinner", title="C"),
        _catalog_recipe(259, meal_type="dinner", title="D"),
        _catalog_recipe(260, meal_type="breakfast", title="E"),
    ]
    result = finalize_menu_variant(MagicMock(), _adhoc_variant(), user=MagicMock())

    for day in result.days or []:
        assert all(meal.recipe_id is not None for meal in day.meals)


@patch("app.services.menu_catalog_enrichment.load_menu_catalog_pool")
def test_recipe_backed_meals_have_image_url(mock_pool):
    mock_pool.return_value = [
        _catalog_recipe(261, meal_type="lunch", title="Суп со свиным фаршем"),
        _catalog_recipe(262, meal_type="dinner", title="Овощной суп-пюре"),
        _catalog_recipe(263, meal_type="breakfast", title="Салат с креветками"),
    ]
    result = finalize_menu_variant(MagicMock(), _adhoc_variant(), user=MagicMock())

    for day in result.days or []:
        for meal in day.meals:
            if meal.recipe_id is not None:
                assert meal.image_url
                assert meal.hero_image_url


@patch("app.services.menu_catalog_enrichment.load_menu_catalog_pool")
def test_different_recipe_ids_keep_different_images(mock_pool):
    mock_pool.return_value = [
        _catalog_recipe(256, meal_type="breakfast", title="A"),
        _catalog_recipe(257, meal_type="lunch", title="B"),
        _catalog_recipe(258, meal_type="dinner", title="C"),
    ]
    result = finalize_menu_variant(MagicMock(), _adhoc_variant(), user=MagicMock())
    day2 = result.days[1].meals
    urls = {meal.recipe_id: meal.image_url for meal in day2 if meal.recipe_id}
    assert len(urls) >= 2
    assert len(set(urls.values())) == len(set(urls.keys()))


def test_adhoc_meal_replaced_from_catalog_pool():
    recipe = _catalog_recipe(
        264,
        meal_type="lunch",
        title="Салат с курицей, яблоком и свежими овощами",
        display_title="Салат с курицей",
    )
    meal = meal_from_catalog_recipe(recipe, "lunch", 2)
    assert meal.recipe_id == 264
    assert meal.name == "Салат с курицей"
    assert meal.display_title == "Салат с курицей"
    assert meal.image_url == "/recipe-images/264/card_800.webp"
    assert meal.hero_image_url == "/recipe-images/264/hero.webp"


@patch("app.services.menu_catalog_enrichment.load_menu_catalog_pool")
def test_null_recipe_adhoc_meal_gets_replaced(mock_pool):
    mock_pool.return_value = [
        _catalog_recipe(265, meal_type="breakfast", title="Овощной суп"),
    ]
    variant = MenuVariant(
        variant="quick",
        title="Single",
        explanation="x",
        total_prep_minutes=20,
        meals=[
            MenuMeal(
                meal_type="breakfast",
                name="Ad-hoc омлет",
                description="",
                prep_time_minutes=15,
                recipe_id=None,
            )
        ],
        ingredients=[MenuIngredient(name="Яйца", amount="2 шт")],
    )
    result = finalize_menu_variant(MagicMock(), variant, user=MagicMock())
    assert result.meals[0].recipe_id == 265
    assert result.meals[0].image_url


@patch("app.services.menu_catalog_enrichment.load_menu_catalog_pool")
def test_explicit_empty_slot_stays_empty(mock_pool):
    mock_pool.return_value = [
        _catalog_recipe(265, meal_type="lunch", title="Овощной суп"),
    ]
    variant = MenuVariant(
        variant="quick",
        title="Single",
        explanation="x",
        total_prep_minutes=0,
        meals=[
            MenuMeal(
                meal_type="lunch",
                name="Свободно",
                description="",
                prep_time_minutes=0,
                recipe_id=None,
                slot_id="2026-07-02:lunch",
            )
        ],
        ingredients=[MenuIngredient(name="По плану", amount="—")],
    )

    result = finalize_menu_variant(MagicMock(), variant, user=MagicMock())

    assert result.meals[0].recipe_id is None
    assert result.meals[0].name == "Свободно"
    assert result.meals[0].slot_id == "2026-07-02:lunch"
