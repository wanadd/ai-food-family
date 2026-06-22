from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = ROOT / "backend" / "scripts"


def _load(name: str):
    path = SCRIPTS / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_extract_upgraded_recipe_ids_count_and_sources():
    common = _load("audit_gold_v3_post_apply_common")
    report = common.extract_upgraded_recipe_ids()
    assert report["recipe_id_count"] == 30
    assert len(report["recipe_ids"]) == 30
    source_names = {source["name"] for source in report["sources"]}
    assert "deterministic_plan_builder" in source_names
    assert "operation_cards" in source_names or "planned_recipe_ids" in source_names


def test_api_contract_validator_catches_source_leakage():
    common = _load("audit_gold_v3_post_apply_common")
    api = _load("audit_gold_v3_post_apply_api_contract")
    row = {
        "id": 2,
        "title": "Test",
        "display_title": "Test",
        "description": "Desc",
        "meal_type": "dinner",
        "servings": 4,
        "cooking_time_minutes": 30,
        "prep_time_minutes": 10,
        "calories_per_serving": 300,
        "protein_g": 20,
        "fat_g": 10,
        "carbs_g": 30,
        "tags": ["gold_v3"],
        "diets": [],
        "source_url": None,
        "hero_image_url": "/img.webp",
        "image_url": "/img.webp",
        "thumbnail_url": "/thumb.webp",
        "ingredients": [],
        "steps": [],
        "nutrition_coverage_json": {},
    }
    ingredients = [
        {"name": "курица", "quantity": "200", "unit": "г"},
        {"name": "рис", "quantity": "100", "unit": "г"},
        {"name": "морковь", "quantity": "1", "unit": "шт"},
    ]
    steps = [{"text": "Шаг 1"}, {"text": "Шаг 2"}, {"text": "Шаг 3"}]
    ok_item = api.evaluate_recipe(row, ingredients, steps)
    assert ok_item["ok"] is True

    leaky_row = dict(row)
    leaky_row["description"] = "source from povarenok"
    leaky_item = api.evaluate_recipe(leaky_row, ingredients, steps)
    assert leaky_item["ok"] is False
    assert any("source_leakage" in blocker for blocker in leaky_item["blockers"])


def test_menu_safety_catches_no_pork_contradiction():
    menu = _load("audit_gold_v3_post_apply_menu_safety")
    row = {
        "id": 2,
        "title": "Свинина тушеная",
        "display_title": "Свинина тушеная",
        "description": "",
        "meal_type": "dinner",
        "is_active": True,
        "source_type": "import",
        "tags": ["no_pork", "gold_v3"],
        "diets": [],
    }
    ingredients = [{"name": "свинина", "quantity": "200", "unit": "г"}]
    steps = [{"text": "Готовим"}]
    report = menu.evaluate_menu_safety([row], {2: ingredients}, {2: steps})
    assert report["hard_fail"] >= 1
    assert any("no_pork_plus_pork" in item["blockers"] for item in report["items"])


def test_shopping_flow_catches_duplicate_units():
    shopping = _load("audit_gold_v3_post_apply_shopping_flow")
    row = {
        "id": 2,
        "title": "Test",
        "display_title": "Test",
    }
    ingredients = [
        {
            "name": "молоко",
            "quantity": "1",
            "unit": "л",
            "quantity_text": "1 л л",
            "category": "dairy",
        }
    ]
    report = shopping.evaluate_shopping_flow([row], {2: ingredients})
    assert report["hard_fail"] >= 1
    assert any("duplicate_unit" in blocker for item in report["items"] for blocker in item["blockers"])


def test_title_garbage_detects_english_prefix():
    common = _load("audit_gold_v3_post_apply_common")
    assert common.title_garbage("High protein: курица") == ["english_prefix"]
    assert common.title_garbage("Курица запеченная") == []
