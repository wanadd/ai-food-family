from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


def _load_module(name: str, rel_path: str):
    path = ROOT / rel_path
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def _row(**overrides):
    base = {
        "id": 2,
        "title": "Омлет с овощами",
        "display_title": "Омлет с овощами",
        "description": "Омлет с яйцами и овощами.",
        "meal_type": "breakfast",
        "category": "main",
        "servings": 2,
        "calories_per_serving": 260,
        "protein_g": 16,
        "fat_g": 14,
        "carbs_g": 10,
        "nutrition_coverage_json": {"coverage": "ok"},
        "nutrition_serving_size_text": "1 порция",
        "yield_type": "cooked",
        "tags": [],
    }
    base.update(overrides)
    return base


def _ingredients(*names: str):
    return [{"name": name} for name in names]


def _steps(*texts: str):
    return [{"text": text} for text in texts]


def test_outlier_low_kcal_full_meal_is_flagged():
    audit = _load_module("audit_gold_v3_nutrition_realism", "backend/scripts/audit_gold_v3_nutrition_realism.py")
    item = audit.evaluate_nutrition_realism(
        _row(calories_per_serving=50),
        _ingredients("яйца", "молоко", "перец"),
        _steps("Нарежьте овощи.", "Смешайте яйца.", "Обжарьте омлет."),
    )
    assert "kcal_lt_80_full_meal" in item["flags"]
    assert item["proposed_action"] == "needs_recalc"


def test_high_protein_impossible_value_is_flagged():
    audit = _load_module("audit_gold_v3_nutrition_realism", "backend/scripts/audit_gold_v3_nutrition_realism.py")
    item = audit.evaluate_nutrition_realism(
        _row(protein_g=140),
        _ingredients("индейка", "гречка", "морковь"),
        _steps("Нарежьте индейку.", "Отварите гречку.", "Смешайте и подайте."),
    )
    assert "protein_gt_100g" in item["flags"]


def test_missing_serving_is_flagged():
    audit = _load_module("audit_gold_v3_nutrition_realism", "backend/scripts/audit_gold_v3_nutrition_realism.py")
    item = audit.evaluate_nutrition_realism(
        _row(servings=None, nutrition_servings=None, estimated_servings=None),
        _ingredients("индейка", "гречка", "морковь"),
        _steps("Нарежьте.", "Отварите.", "Подайте."),
    )
    assert "serving_count_missing_or_invalid" in item["flags"]
    assert item["proposed_action"] == "missing_data"


def test_dry_grain_dish_with_suspicious_carbs_is_flagged():
    audit = _load_module("audit_gold_v3_nutrition_realism", "backend/scripts/audit_gold_v3_nutrition_realism.py")
    item = audit.evaluate_nutrition_realism(
        _row(title="Гречка с индейкой", display_title="Гречка с индейкой", carbs_g=8, yield_type=None),
        _ingredients("гречка", "индейка", "морковь"),
        _steps("Отварите гречку.", "Приготовьте индейку.", "Соедините."),
    )
    assert "grain_dish_carbs_too_low" in item["flags"]
    assert "dry_grain_yield_unknown" in item["flags"]


def test_valid_looking_recipe_passes():
    audit = _load_module("audit_gold_v3_nutrition_realism", "backend/scripts/audit_gold_v3_nutrition_realism.py")
    item = audit.evaluate_nutrition_realism(
        _row(),
        _ingredients("яйца", "молоко", "перец"),
        _steps("Нарежьте овощи.", "Смешайте яйца.", "Обжарьте омлет."),
    )
    assert item["proposed_action"] == "ok"
    assert item["flags"] == []


def test_title_ingredient_mismatch_is_flagged():
    consistency = _load_module("audit_gold_v3_recipe_consistency", "backend/scripts/audit_gold_v3_recipe_consistency.py")
    item = consistency.evaluate_recipe_consistency(
        _row(title="Гречка с индейкой", display_title="Гречка с индейкой"),
        _ingredients("рис", "курица", "морковь"),
        _steps("Отварите рис.", "Приготовьте курицу.", "Соедините."),
    )
    assert "title_main_ingredient_missing:индейк" in item["hard_fail"]
    assert "title_main_ingredient_missing:греч" in item["hard_fail"]


def test_bad_title_term_still_blocked():
    consistency = _load_module("audit_gold_v3_recipe_consistency", "backend/scripts/audit_gold_v3_recipe_consistency.py")
    item = consistency.evaluate_recipe_consistency(
        _row(title="Индейка с овощами без свинины", display_title="Индейка с овощами без свинины"),
        _ingredients("индейка", "морковь", "кабачок"),
        _steps("Нарежьте индейку.", "Потушите овощи.", "Соедините и подайте."),
    )
    assert "bad_title_term:без свинины" in item["hard_fail"]
