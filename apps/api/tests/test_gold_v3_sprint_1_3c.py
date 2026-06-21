from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

ROOT = Path(__file__).resolve().parents[3]
API_ROOT = ROOT / "apps" / "api"
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.services.recipes.mapper import image_ready, is_gold_v3_recipe, recipe_schema, to_summary  # noqa: E402
from app.nutrition.restriction_safety import recipe_is_allowed_for_profile  # noqa: E402


def _load_script(name: str):
    path = ROOT / "backend" / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _seed_recipe(**overrides):
    recipe = SimpleNamespace(
        id=256,
        title="Нежные куриные котлеты с овощами",
        display_title="Куриные котлеты",
        description="",
        meal_type="dinner",
        category="main",
        prep_time_minutes=20,
        cooking_time_minutes=30,
        servings=4,
        difficulty="medium",
        diets=[],
        tags=["gold_v3", "recipe_schema_v3", "status:gold"],
        tag_rows=None,
        is_drink=False,
        is_alcoholic=False,
        calories_per_serving=320,
        protein_g=24,
        fat_g=14,
        carbs_g=18,
        suitable_for_children=True,
        suitable_for_sport=False,
        suitable_for_event=False,
        image_url="/recipe-images/256/card_800.webp",
        hero_image_url="/recipe-images/256/hero.webp",
        thumbnail_url="/recipe-images/256/thumb_400.webp",
        source_type="seed",
        nutrition_confidence=None,
        nutrition_calculated_at=None,
    )
    for key, value in overrides.items():
        setattr(recipe, key, value)
    return recipe


def test_gold_v3_pilot_seed_exact_ids():
    data = json.loads((ROOT / "data/recipe_v2/gold_v3_pilot_10_seed.json").read_text(encoding="utf-8"))
    ids = [recipe["id"] for recipe in data["recipes"]]
    assert ids == list(range(256, 266))
    assert len(data["recipes"]) == 10


def test_mapper_gold_v3_flags_do_not_break_summary():
    recipe = _seed_recipe()
    assert is_gold_v3_recipe(recipe) is True
    assert recipe_schema(recipe) == "gold_v3"
    assert image_ready(recipe) is True
    summary = to_summary(recipe, set())
    assert summary.is_gold_v3 is True
    assert summary.recipe_schema == "gold_v3"
    assert summary.image_ready is True


def test_asset_verify_public_url_mode_mocked():
    mod = _load_script("verify_gold_v3_pilot_10_assets")

    class FakeResponse:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

    with patch.object(mod, "urlopen", return_value=FakeResponse()):
        rows, ok = mod.public_url_rows("https://planam.example", timeout=0.1)

    assert ok is True
    assert len(rows) == 10
    assert rows[0]["hero.webp_status"] == 200


def test_restore_dry_run_refuses_non_gold_without_force():
    mod = _load_script("restore_gold_v3_pilot_10")
    recipes = mod.load_seed()

    with patch.object(
        mod,
        "db_plan",
        return_value={
            "db_available": True,
            "blocked": True,
            "blocker_ids": [256],
            "existing": [{"id": 256, "tags": []}],
            "error": "Existing pilot ID rows are not tagged gold_v3.",
        },
    ):
        plan = mod.db_plan(recipes, force=False)

    assert plan["blocked"] is True
    assert plan["blocker_ids"] == [256]


def test_repair_script_produces_valid_candidate_records():
    mod = _load_script("repair_gold_recipes_30_candidate")
    raw = {
        "title": "High protein: Курица #1",
        "meal_types": ["dinner"],
        "category": "main",
        "ingredients": [
            {"display_name": "Курица", "amount": 200, "unit": "г", "shopping_category_slug": "meat"},
            {"display_name": "Рис", "amount": 100, "unit": "г", "shopping_category_slug": "grains"},
            {"display_name": "Морковь", "amount": 1, "unit": "шт", "shopping_category_slug": "vegetables"},
        ],
        "steps": [
            {"instruction": "Нарезать ингредиенты."},
            {"instruction": "Потушить до готовности."},
            {"instruction": "Подать тёплым."},
        ],
        "nutrition_summary": {"calories": 300, "protein_g": 25, "fat_g": 8, "carbs_g": 32},
    }
    repaired, _warnings = mod.repair_record(raw, 1)
    assert repaired["schema_version"] == "recipe_gold_v3"
    assert repaired["source_type"] == "gold_v3_candidate"
    assert repaired["meal_type"] == "dinner"
    assert repaired["title"] == "Курица"
    assert "high_protein" in repaired["tags"]
    assert repaired["image_prompt"]


def test_repair_script_removes_pro_english_prefixes():
    mod = _load_script("repair_gold_recipes_30_candidate")
    raw = {
        "title": "Pro high protein: куриная грудка и киноа",
        "meal_types": ["lunch"],
        "category": "main",
        "ingredients": [
            {"display_name": "Куриная грудка", "amount": 200, "unit": "г", "shopping_category_slug": "meat"},
            {"display_name": "Киноа", "amount": 80, "unit": "г", "shopping_category_slug": "grains"},
            {"display_name": "Брокколи", "amount": 100, "unit": "г", "shopping_category_slug": "vegetables"},
        ],
        "steps": [
            {"instruction": "Отварить киноа."},
            {"instruction": "Запечь курицу."},
            {"instruction": "Подать с брокколи."},
        ],
        "nutrition_summary": {"calories": 450, "protein_g": 48, "fat_g": 14, "carbs_g": 32},
    }
    repaired, _warnings = mod.repair_record(raw, 28)
    assert repaired["title"] == "Куриная грудка и киноа"
    assert repaired["normalized_title"] == "куриная грудка и киноа"
    assert "high_protein" in repaired["tags"]
    assert "vegetarian" not in repaired["tags"]


def test_quality_gate_catches_core_blockers():
    mod = _load_script("quality_gate_gold_recipes_30_candidate")
    bad = {
        "schema_version": "recipe_gold_v3",
        "source_type": "gold_v3_candidate",
        "meal_type": "",
        "title": "High protein: Свинина с картофелем",
        "tags": ["no_pork"],
        "ingredients": [{"name": "свинина", "amount": 100, "unit": "г", "shopping_category_slug": "meat"}],
        "steps": [{"text": "Готовить."}],
        "nutrition_per_serving": {"kcal": 300, "protein_g": None, "fat_g": 10, "carbs_g": 20},
        "image_prompt": "",
    }
    ok, blockers = mod.validate_record(bad, set())
    assert ok is False
    assert "title_garbage" in blockers
    assert "meal_type_missing" in blockers
    assert "no_pork_plus_pork" in blockers
    assert "nutrition_core_incomplete" in blockers


def test_quality_gate_catches_generic_pro_english_title_prefix():
    mod = _load_script("quality_gate_gold_recipes_30_candidate")
    bad = {
        "schema_version": "recipe_gold_v3",
        "source_type": "gold_v3_candidate",
        "meal_type": "lunch",
        "title": "Pro high protein: куриная грудка и киноа",
        "tags": ["high_protein"],
        "ingredients": [
            {"name": "куриная грудка", "amount": 200, "unit": "г", "shopping_category_slug": "meat"},
            {"name": "киноа", "amount": 80, "unit": "г", "shopping_category_slug": "grains"},
            {"name": "брокколи", "amount": 100, "unit": "г", "shopping_category_slug": "vegetables"},
        ],
        "steps": [{"text": "Раз."}, {"text": "Два."}, {"text": "Три."}],
        "nutrition_per_serving": {"kcal": 450, "protein_g": 48, "fat_g": 14, "carbs_g": 32},
        "image_prompt": "Фото блюда.",
    }
    ok, blockers = mod.validate_record(bad, set())
    assert ok is False
    assert "title_garbage" in blockers


def test_vegetarian_restriction_blocks_kurinoe_file():
    recipe = SimpleNamespace(
        title="Куриные котлеты",
        description="",
        ingredients=[{"name": "куриное филе"}],
        tags=[],
        diets=[],
        allergens=[],
        restrictions=[],
        is_alcoholic=False,
    )
    profile = SimpleNamespace(
        restrictions=["vegetarian"],
        diets=[],
        allergies=[],
        banned_foods="",
        medical_restrictions="",
    )
    assert recipe_is_allowed_for_profile(recipe, profile) is False
