from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from app.services.recipes.mapper import to_detail, to_summary
from app.services.recipes.title_display import public_recipe_title


def test_halal_chicken_title_cleaned():
    assert public_recipe_title("Халяль-курица с булгуром") == "Курица с булгуром"


def test_lentil_soup_title_cleaned():
    result = public_recipe_title("Постный гороховый суп")
    assert "постн" not in result.lower()
    assert result == "Гороховый суп с овощами"


def test_smoothie_bowl_title_cleaned():
    result = public_recipe_title("Смузи-боул с бананом и орехами")
    lowered = result.lower()
    assert "смузи" not in lowered
    assert "боул" not in lowered
    assert result == "Банановый завтрак с орехами"


def test_cottage_bowl_title_cleaned():
    assert public_recipe_title("Творожная боул с фруктами") == "Творог с фруктами"


def test_avocado_toast_title_cleaned():
    result = public_recipe_title("Тост с авокадо и яйцом")
    assert "тост" not in result.lower()
    assert result == "Хлеб с авокадо и яйцом"


def test_stir_fry_title_cleaned():
    result = public_recipe_title("Быстрый стир-фрай с курицей")
    lowered = result.lower()
    assert "стир-фрай" not in lowered
    assert "стир" not in lowered
    assert result == "Курица с овощами на сковороде"


def test_light_dinner_prefix_removed():
    result = public_recipe_title("Лёгкий ужин: салат с тунцом")
    assert ":" not in result
    assert "лёгкий" not in result.lower()
    assert result == "Салат с тунцом и овощами"


def test_family_dinner_prefix_removed():
    result = public_recipe_title("Семейный ужин: тефтели в томатном соусе")
    assert ":" not in result
    assert result == "Тефтели в томатном соусе"


@pytest.mark.parametrize(
    "title",
    ["Гречка с индейкой", "Омлет с овощами"],
)
def test_normal_titles_preserved(title: str):
    assert public_recipe_title(title) == title


def test_mapper_uses_cleaned_title_for_upgraded_recipe(monkeypatch: pytest.MonkeyPatch):
    recipe = SimpleNamespace(
        id=239,
        title="Халяль-курица с булгуром",
        display_title="Халяль-курица с булгуром",
        original_title=None,
        description="Описание",
        meal_type="lunch",
        category="main",
        prep_time_minutes=10,
        cooking_time_minutes=20,
        servings=2,
        difficulty="easy",
        diets=[],
        calories_per_serving=300,
        protein_g=20,
        fat_g=10,
        carbs_g=30,
        suitable_for_children=True,
        suitable_for_sport=False,
        suitable_for_event=False,
        image_url=None,
        hero_image_url=None,
        thumbnail_url=None,
        sugar_g=None,
        caffeine_mg=None,
        alcohol_percent=None,
        cuisine=None,
        source_type="legacy",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        is_drink=False,
        is_alcoholic=False,
        nutrition_confidence=None,
        nutrition_calculated_at=None,
        nutrition_kcal_total=None,
        nutrition_protein_total=None,
        nutrition_fat_total=None,
        nutrition_carbs_total=None,
        nutrition_kcal_per_serving=None,
        nutrition_protein_per_serving=None,
        nutrition_fat_per_serving=None,
        nutrition_carbs_per_serving=None,
        nutrition_servings=None,
        nutrition_serving_size_text=None,
        nutrition_needs_review=False,
        nutrition_review_reason=None,
        ingredient_rows=[],
        step_rows=[],
        tag_rows=[],
    )

    def _get_tags(_recipe):
        return ["upgraded_from_legacy"]

    def _get_structured_ingredients(_recipe):
        return [{"name": "Курица", "amount": "200 г"}]

    def _get_structured_steps(_recipe):
        return ["Шаг 1", "Шаг 2", "Шаг 3"]

    def _get_allergens(_recipe):
        return []

    def _get_restrictions(_recipe):
        return []

    monkeypatch.setattr("app.services.recipes.mapper.get_tags", _get_tags)
    monkeypatch.setattr("app.services.recipes.mapper.get_structured_ingredients", _get_structured_ingredients)
    monkeypatch.setattr("app.services.recipes.mapper.get_structured_steps", _get_structured_steps)
    monkeypatch.setattr("app.services.recipes.mapper.get_allergens", _get_allergens)
    monkeypatch.setattr("app.services.recipes.mapper.get_restrictions", _get_restrictions)
    monkeypatch.setattr("app.services.recipes.description_display.get_tags", _get_tags)
    monkeypatch.setattr("app.services.recipes.description_display.get_structured_ingredients", _get_structured_ingredients)

    summary = to_summary(recipe, set())
    detail = to_detail(recipe, set())
    assert summary.title == "Курица с булгуром"
    assert summary.display_title == "Курица с булгуром"
    assert detail.title == "Курица с булгуром"
    assert "халяль" not in detail.title.lower()
