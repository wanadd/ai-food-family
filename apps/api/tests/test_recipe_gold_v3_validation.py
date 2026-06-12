"""Tests for Recipe Gold V3 schema validation (Stage E)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

API_ROOT = Path(__file__).resolve().parents[1]
ROOT = API_ROOT.parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.recipes.recipe_gold_v3_validation import validate_recipe_gold_v3  # noqa: E402
from app.recipes.recipe_gold_v3_schema import PRODUCTION_READY_MIN_SCORE  # noqa: E402

SAMPLES = ROOT / "exports" / "recipe_gold_v3_validation_samples.jsonl"
CLI = ROOT / "backend" / "scripts" / "validate_recipe_gold_v3.py"


def _ing(name: str, *, category: str = "овощи", amount: float = 100) -> dict:
    return {
        "name": name,
        "amount": amount,
        "unit": "г",
        "display_amount": f"{int(amount)} г",
        "category": category,
        "optional": False,
        "shopping_name": name,
    }


def _step(num: int, text: str) -> dict:
    return {"step_number": num, "text": text}


def _valid_recipe(**overrides) -> dict:
    base = {
        "schema_version": "recipe_gold_v3",
        "status": "gold",
        "source_type": "generated_original",
        "source_signal_ids": ["pov_sig_000001"],
        "originality": {
            "is_original_planam_recipe": True,
            "no_source_title_used": True,
            "no_source_steps_used": True,
            "no_direct_copy": True,
            "source_similarity_risk": "low",
            "originality_notes": "PLANAM original",
        },
        "title": "Куриное рагу с овощами",
        "subtitle": "Семейный ужин",
        "description": "Сытное домашнее блюдо с курицей и овощами. Готовится в одной сковороде без сложных техник.",
        "meal_type": "dinner",
        "category": "main",
        "cuisine_style": "семейная",
        "servings": 4,
        "prep_time_min": 15,
        "cook_time_min": 30,
        "total_time_min": 45,
        "difficulty": "easy",
        "family_fit": "high",
        "ingredients": [
            _ing("куриное филе", category="мясо_птица", amount=500),
            _ing("картофель", category="овощи", amount=300),
            _ing("морковь", category="овощи", amount=150),
            _ing("лук репчатый", category="овощи", amount=100),
        ],
        "steps": [
            _step(1, "Нарежьте курицу и овощи кубиками одинакового размера для равномерного приготовления."),
            _step(2, "Разогрейте сковороду с маслом и обжарьте курицу до золотистой корочки со всех сторон."),
            _step(3, "Добавьте овощи, перемешайте и тушите под крышкой 20 минут на среднем огне."),
            _step(4, "Перед подачей дайте блюду настояться 3–5 минут и посыпьте зеленью по желанию."),
        ],
        "nutrition_per_serving": {
            "kcal": 410,
            "protein_g": 30,
            "fat_g": 15,
            "carbs_g": 35,
            "fiber_g": 5,
        },
        "restriction_keys": ["no_pork", "no_alcohol"],
        "allergen_keys": [],
        "diet_tags": ["high_protein", "balanced"],
        "shopping": {
            "aggregation_safe": True,
            "has_fractional_amounts": False,
            "rounding_notes": "",
        },
        "image_prompt_data": {
            "dish_visual_summary": "Куриное рагу с овощами в глубокой тарелке",
            "serving_style": "единый сервиз PLANAM",
            "avoid_visuals": ["текст", "логотипы", "руки", "грязный фон"],
        },
        "quality": {"score": 0, "flags": [], "warnings": []},
    }
    base.update(overrides)
    return base


def test_valid_recipe_passes():
    result = validate_recipe_gold_v3(_valid_recipe())
    assert result.ok
    assert result.score >= PRODUCTION_READY_MIN_SCORE


def test_missing_required_field_fails():
    recipe = _valid_recipe()
    del recipe["title"]
    result = validate_recipe_gold_v3(recipe)
    assert not result.ok
    assert any(i.code == "missing_required_field" for i in result.errors)


def test_english_prefix_in_title_fails():
    result = validate_recipe_gold_v3(
        _valid_recipe(title="High protein: курица с рисом")
    )
    assert not result.ok
    assert any(i.code == "english_title_prefix" for i in result.errors)


def test_bowl_in_title_fails():
    result = validate_recipe_gold_v3(_valid_recipe(title="Творожная bowl с ягодами"))
    assert not result.ok
    assert any(i.code == "forbidden_bowl_in_title" for i in result.errors)


def test_title_too_short_fails():
    result = validate_recipe_gold_v3(_valid_recipe(title="Суп"))
    assert not result.ok
    assert any(i.code == "title_length" for i in result.errors)


def test_too_few_steps_fails():
    recipe = _valid_recipe()
    recipe["steps"] = recipe["steps"][:2]
    result = validate_recipe_gold_v3(recipe)
    assert not result.ok
    assert any(i.code == "too_few_steps" for i in result.errors)


def test_short_step_fails():
    recipe = _valid_recipe()
    recipe["steps"][0] = _step(1, "Короткий шаг")
    result = validate_recipe_gold_v3(recipe)
    assert not result.ok
    assert any(i.code == "step_too_short" for i in result.errors)


def test_too_few_ingredients_fails():
    recipe = _valid_recipe()
    recipe["ingredients"] = recipe["ingredients"][:2]
    result = validate_recipe_gold_v3(recipe)
    assert not result.ok
    assert any(i.code == "too_few_ingredients" for i in result.errors)


def test_missing_nutrition_fails():
    recipe = _valid_recipe()
    recipe["nutrition_per_serving"] = {"protein_g": 10, "fat_g": 5, "carbs_g": 20}
    result = validate_recipe_gold_v3(recipe)
    assert not result.ok
    assert any(i.code == "missing_kcal" for i in result.errors)


def test_kcal_macro_mismatch_fails():
    recipe = _valid_recipe()
    recipe["nutrition_per_serving"] = {
        "kcal": 900,
        "protein_g": 10,
        "fat_g": 5,
        "carbs_g": 20,
    }
    result = validate_recipe_gold_v3(recipe)
    assert not result.ok
    assert any(i.code == "kcal_macro_mismatch" for i in result.errors)


def test_unknown_restriction_key_fails():
    result = validate_recipe_gold_v3(
        _valid_recipe(restriction_keys=["totally_unknown_key"])
    )
    assert not result.ok
    assert any(i.code == "unknown_restriction_key" for i in result.errors)


def test_no_pork_with_bacon_fails():
    recipe = _valid_recipe(restriction_keys=["no_pork"])
    recipe["ingredients"][0] = _ing("бекон", category="свинина", amount=100)
    result = validate_recipe_gold_v3(recipe)
    assert not result.ok
    assert any(
        i.code in {"restriction_contradiction", "restriction_safety_conflict"}
        for i in result.errors
    )


def test_vegetarian_with_chicken_fails():
    recipe = _valid_recipe(diet_tags=["vegetarian"])
    result = validate_recipe_gold_v3(recipe)
    assert not result.ok
    assert any(i.code == "diet_contradiction" for i in result.errors)


def test_vegan_with_milk_fails():
    recipe = _valid_recipe(diet_tags=["vegan"])
    recipe["ingredients"] = [
        _ing("тофу", category="бобовые"),
        _ing("молоко", category="молочные продукты"),
        _ing("рис", category="крупы"),
        _ing("морковь", category="овощи"),
    ]
    result = validate_recipe_gold_v3(recipe)
    assert not result.ok
    assert any(i.code == "diet_contradiction" for i in result.errors)


def test_no_alcohol_with_wine_fails():
    recipe = _valid_recipe(restriction_keys=["no_alcohol"])
    recipe["ingredients"][-1] = _ing("вино", category="напитки", amount=100)
    result = validate_recipe_gold_v3(recipe)
    assert not result.ok
    assert any(
        i.code in {"restriction_contradiction", "restriction_safety_conflict"}
        for i in result.errors
    )


def test_missing_display_amount_fails():
    recipe = _valid_recipe()
    recipe["ingredients"][0]["display_amount"] = ""
    result = validate_recipe_gold_v3(recipe)
    assert not result.ok
    assert any(i.code == "missing_display_amount" for i in result.errors)


def test_ugly_fractional_amount_warns():
    recipe = _valid_recipe()
    recipe["ingredients"][0]["amount"] = 173.3333
    result = validate_recipe_gold_v3(recipe)
    assert any(i.code == "ugly_fractional_amount" for i in result.warnings)


def test_originality_flags_false_fail():
    recipe = _valid_recipe()
    recipe["originality"]["no_direct_copy"] = False
    result = validate_recipe_gold_v3(recipe)
    assert not result.ok
    assert any(i.code == "originality_direct_copy" for i in result.errors)


def test_high_similarity_risk_fails():
    recipe = _valid_recipe()
    recipe["originality"]["source_similarity_risk"] = "high"
    result = validate_recipe_gold_v3(recipe)
    assert not result.ok
    assert any(i.code == "high_similarity_risk" for i in result.errors)


def test_warnings_lower_score():
    recipe = _valid_recipe()
    recipe["nutrition_per_serving"]["fiber_g"] = None
    result = validate_recipe_gold_v3(recipe)
    assert result.ok
    assert result.score < 100


def test_valid_recipe_score_at_least_85():
    result = validate_recipe_gold_v3(_valid_recipe())
    assert result.score >= 85


def test_validator_cli_reads_samples_and_writes_report(tmp_path):
    report = tmp_path / "validation_report.md"
    proc = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "--input",
            str(SAMPLES),
            "--report",
            str(report),
            "--dry-run",
            "--fail-on-error",
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 1
    assert report.exists()
    content = report.read_text(encoding="utf-8")
    assert "Recipe Gold V3 Validation Report" in content
    assert "Valid:" in content
    lines = [json.loads(line) for line in SAMPLES.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(lines) == 5
