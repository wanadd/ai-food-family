"""Tests for Gold V3 UI text contract (Stage Q4)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

API_ROOT = Path(__file__).resolve().parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.recipes.recipe_gold_v3_quality_gate import evaluate_recipe_gold_v3_quality_gate  # noqa: E402
from app.recipes.recipe_gold_v3_ui_contract import (  # noqa: E402
    DISPLAY_TITLE_MAX_LEN,
    check_ui_text_contract,
)
from app.services.recipes.mapper import normalize_nutrition_confidence, to_summary  # noqa: E402
from types import SimpleNamespace


def _base_recipe(**overrides) -> dict:
    recipe = {
        "schema_version": "recipe_gold_v3",
        "status": "gold",
        "source_type": "generated_original",
        "source_signal_ids": ["sig_1"],
        "originality": {
            "is_original_planam_recipe": True,
            "no_source_title_used": True,
            "no_source_steps_used": True,
            "no_direct_copy": True,
            "source_similarity_risk": "low",
        },
        "title": "Салат с курицей, яблоком и свежими овощами",
        "display_title": "Салат с курицей и яблоком",
        "description": (
            "Лёгкий салат с нежной курицей, хрустящим яблоком и сезонными овощами — "
            "удобный обед без долгой готовки для всей семьи."
        ),
        "meal_type": "lunch",
        "category": "salad",
        "cuisine_style": "семейная",
        "servings": 4,
        "prep_time_min": 15,
        "cook_time_min": 10,
        "total_time_min": 25,
        "difficulty": "easy",
        "family_fit": "high",
        "ingredients": [
            {
                "name": "куриное филе",
                "amount": 300,
                "unit": "г",
                "display_amount": "300 г",
                "category": "мясо_птица",
                "optional": False,
                "shopping_name": "куриное филе",
            },
            {
                "name": "яблоко",
                "amount": 2,
                "unit": "шт",
                "display_amount": "2 шт",
                "category": "фрукты/ягоды",
                "optional": False,
                "shopping_name": "яблоко",
            },
            {
                "name": "огурец",
                "amount": 2,
                "unit": "шт",
                "display_amount": "2 шт",
                "category": "овощи",
                "optional": False,
                "shopping_name": "огурец",
            },
            {
                "name": "масло оливковое",
                "amount": 20,
                "unit": "мл",
                "display_amount": "20 мл",
                "category": "масла/соусы",
                "optional": False,
                "shopping_name": "оливковое масло",
            },
        ],
        "steps": [
            {"step_number": 1, "text": "Куриное филе отварите до готовности, остудите и нарежьте небольшими кусочками для салата."},
            {"step_number": 2, "text": "Яблоко и огурец промойте, нарежьте тонкими ломтиками или кубиками одинакового размера."},
            {"step_number": 3, "text": "Смешайте курицу с овощами и фруктами в глубокой миске, добавьте масло и аккуратно перемешайте."},
            {"step_number": 4, "text": "Подавайте салат сразу, пока яблоко остаётся свежим и сохраняет приятную хрустящую текстуру."},
        ],
        "nutrition_per_serving": {
            "kcal": 320,
            "protein_g": 24,
            "fat_g": 14,
            "carbs_g": 18,
            "fiber_g": 4,
            "salt_g": 1.1,
            "sugar_g": 6,
        },
        "nutrition_confidence": "estimated",
        "restriction_keys": [],
        "allergen_keys": [],
        "diet_tags": [],
        "shopping": {"aggregation_safe": True, "has_fractional_amounts": False, "rounding_notes": ""},
        "image_prompt_data": {
            "dish_visual_summary": "Fresh chicken salad with apple on a light ceramic plate.",
            "serving_style": "единый сервиз PLANAM",
            "avoid_visuals": ["текст", "логотипы", "руки", "грязный фон"],
        },
        "quality": {"score": 90, "flags": [], "warnings": []},
        "hero_image_url": "/recipe-images/264/hero.webp",
    }
    recipe.update(overrides)
    return recipe


def test_missing_display_title_fails_contract():
    findings = check_ui_text_contract(_base_recipe(display_title=""))
    codes = {f["code"] for f in findings if f["severity"] == "error"}
    assert "display_title_card_safe" in codes


def test_display_title_too_long_fails():
    long_title = "С" * (DISPLAY_TITLE_MAX_LEN + 1)
    findings = check_ui_text_contract(_base_recipe(display_title=long_title))
    assert any(f["code"] == "display_title_card_safe" for f in findings)


def test_title_with_hash_fails_technical_check():
    findings = check_ui_text_contract(_base_recipe(title="Котлеты #1 с овощами"))
    assert any(f["code"] == "no_technical_title" for f in findings)


def test_nutrition_confidence_high_fails_contract():
    findings = check_ui_text_contract(_base_recipe(nutrition_confidence="high"))
    assert any(f["code"] == "nutrition_confidence_allowed" for f in findings)


def test_quality_gate_fails_without_display_title():
    recipe = _base_recipe(display_title="")
    result = evaluate_recipe_gold_v3_quality_gate([recipe], min_score=0, avg_score=0)
    assert result["recommendation"] == "FAIL"
    assert "display_title_card_safe" in result["errors_by_code"]


def test_mapper_normalizes_high_confidence_for_summary():
    assert normalize_nutrition_confidence("high") == "estimated"


def test_to_summary_survives_high_confidence():
    recipe = SimpleNamespace(
        id=256,
        title="Котлеты с овощами",
        display_title="Куриные котлеты с овощами",
        description="",
        meal_type="dinner",
        category="main",
        prep_time_minutes=20,
        cooking_time_minutes=20,
        servings=4,
        difficulty="easy",
        diets=[],
        tags=[],
        tag_rows=None,
        is_drink=False,
        is_alcoholic=False,
        calories_per_serving=300.0,
        protein_g=12.0,
        fat_g=10.0,
        carbs_g=30.0,
        suitable_for_children=True,
        suitable_for_sport=False,
        suitable_for_event=False,
        image_url="/recipe-images/256/card_800.webp",
        hero_image_url="/recipe-images/256/hero.webp",
        thumbnail_url="/recipe-images/256/thumb_400.webp",
        nutrition_confidence="high",
        nutrition_calculated_at=None,
        nutrition_kcal_per_serving=300.0,
        nutrition_protein_per_serving=12.0,
        nutrition_fat_per_serving=10.0,
        nutrition_carbs_per_serving=30.0,
        nutrition_kcal_total=None,
        nutrition_protein_total=None,
        nutrition_fat_total=None,
        nutrition_carbs_total=None,
        nutrition_servings=4.0,
        nutrition_serving_size_text=None,
        nutrition_needs_review=False,
        nutrition_review_reason=None,
    )
    summary = to_summary(recipe, set())
    assert summary.nutrition_summary is not None
    assert summary.nutrition_summary.confidence == "estimated"
