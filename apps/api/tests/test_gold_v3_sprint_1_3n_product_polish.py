from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import patch

from app.models.recipe import Recipe
from app.services.recipes.description_display import (
    build_description_fallback,
    public_description,
)
from app.services.recipes.mapper import to_detail


def _recipe(
    *,
    recipe_id: int = 2,
    description: str = "",
    title: str = "Курица с гречкой и овощами",
    meal_type: str = "dinner",
    tags: list[str] | None = None,
    ingredients: list[dict] | None = None,
) -> Recipe:
    recipe = Recipe(
        id=recipe_id,
        title=title,
        display_title=title,
        description=description,
        meal_type=meal_type,
        category="main",
        difficulty="easy",
        cooking_time_minutes=30,
        prep_time_minutes=20,
        servings=4,
        calories_per_serving=420.0,
        protein_g=32.0,
        fat_g=12.0,
        carbs_g=40.0,
        source_type="import",
        is_drink=False,
        is_alcoholic=False,
        suitable_for_children=True,
        suitable_for_sport=False,
        suitable_for_event=False,
        tags=tags or ["gold_v3", "recipe_schema_v3"],
        diets=[],
        ingredients=ingredients
        or [
            {"name": "курица", "amount": "200 г"},
            {"name": "гречка", "amount": "80 г"},
            {"name": "морковь", "amount": "1 шт"},
        ],
        steps=["Шаг 1", "Шаг 2", "Шаг 3"],
        created_at=datetime.now(timezone.utc),
    )
    recipe.ingredient_rows = []
    recipe.step_rows = []
    recipe.tag_rows = []
    return recipe


def test_empty_description_gets_safe_russian_fallback():
    recipe = _recipe(description="")
    text = public_description(recipe)
    assert text
    assert "куриц" in text.lower() or "греч" in text.lower()
    assert "povarenok" not in text.lower()
    assert "source_url" not in text.lower()


def test_existing_description_is_preserved():
    recipe = _recipe(description="Готовое описание блюда.")
    assert public_description(recipe) == "Готовое описание блюда."


def test_fallback_does_not_include_forbidden_markers():
    recipe = _recipe(description="", title="High protein: курица")
    text = public_description(recipe)
    assert "high protein" not in text.lower()
    assert "povarenok" not in text.lower()
    assert "source_url" not in text.lower()


def test_mapper_uses_description_fallback_in_api_payload():
    recipe = _recipe(description="")
    detail = to_detail(recipe, set())
    assert detail.description
    assert detail.description == public_description(recipe)


def test_ingredients_and_steps_are_structured_not_raw_json_strings():
    recipe = _recipe(description="Описание")
    detail = to_detail(recipe, set())
    assert all(isinstance(step, str) and not step.startswith("[") for step in detail.steps)
    assert all(ing.name for ing in detail.ingredients)
    assert all(not ing.amount.startswith("{") for ing in detail.ingredients)


def test_nutrition_display_avoids_nan_null_tokens():
    recipe = _recipe(description="Описание")
    detail = to_detail(recipe, set())
    blob = f"{detail.calories_per_serving} {detail.protein_g} {detail.fat_g} {detail.carbs_g}"
    assert "nan" not in blob.lower()
    assert "null" not in blob.lower()
    assert "undefined" not in blob.lower()


def test_product_polish_audit_catches_empty_user_facing_description():
    import importlib.util
    from pathlib import Path

    path = Path(__file__).resolve().parents[3] / "backend" / "scripts" / "audit_gold_v3_product_polish.py"
    spec = importlib.util.spec_from_file_location("audit_gold_v3_product_polish", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    evaluate_payload = module.evaluate_payload

    bad = evaluate_payload(
        2,
        {
            "id": 2,
            "title": "Тест",
            "description_display": "",
            "ingredients": [{"name": "рис", "amount": "100 г"}],
            "steps": ["Шаг"],
            "tags": ["gold_v3"],
            "calories_per_serving": 300,
            "protein_g": 10,
            "fat_g": 5,
            "carbs_g": 40,
        },
    )
    assert "description_empty_user_facing" in bad["blockers"]


def test_product_polish_audit_catches_source_leakage():
    import importlib.util
    from pathlib import Path

    path = Path(__file__).resolve().parents[3] / "backend" / "scripts" / "audit_gold_v3_product_polish.py"
    spec = importlib.util.spec_from_file_location("audit_gold_v3_product_polish", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    evaluate_payload = module.evaluate_payload

    bad = evaluate_payload(
        2,
        {
            "id": 2,
            "title": "Тест",
            "description_display": "описание с povarenok",
            "ingredients": [{"name": "рис", "amount": "100 г"}],
            "steps": ["Шаг"],
            "tags": [],
            "calories_per_serving": 300,
            "protein_g": 10,
            "fat_g": 5,
            "carbs_g": 40,
        },
    )
    assert any(b.startswith("source_leakage") for b in bad["blockers"])


def test_product_polish_audit_catches_raw_json_render_risk():
    import importlib.util
    from pathlib import Path

    path = Path(__file__).resolve().parents[3] / "backend" / "scripts" / "audit_gold_v3_product_polish.py"
    spec = importlib.util.spec_from_file_location("audit_gold_v3_product_polish", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    evaluate_payload = module.evaluate_payload

    bad = evaluate_payload(
        2,
        {
            "id": 2,
            "title": "Тест",
            "description_display": "нормальное описание",
            "ingredients": [{"name": "рис", "amount": "[{\"name\":\"x\"}]"}],
            "steps": ["Шаг"],
            "tags": [],
            "calories_per_serving": 300,
            "protein_g": 10,
            "fat_g": 5,
            "carbs_g": 40,
        },
    )
    assert any(b.startswith("raw_json_render_risk") for b in bad["blockers"])


def test_upgraded_recipe_id_gets_fallback_without_gold_v3_tag():
    recipe = _recipe(description="", tags=["gold_v2", "recipe_schema_v2"])
    assert public_description(recipe)


def test_build_description_fallback_uses_ingredients():
    recipe = _recipe(description="")
    with patch(
        "app.services.recipes.description_display.get_structured_ingredients",
        return_value=[
            {"name": "Курица"},
            {"name": "Гречка"},
            {"name": "Морковь"},
        ],
    ):
        text = build_description_fallback(recipe)
    assert "куриц" in text.lower()
    assert "греч" in text.lower()
