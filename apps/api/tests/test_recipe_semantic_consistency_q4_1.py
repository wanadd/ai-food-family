"""Tests for Stage Q4.1 semantic consistency gate and hotfix scripts."""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

API_ROOT = Path(__file__).resolve().parents[1]
ROOT = API_ROOT.parents[1]
SCRIPTS_DIR = ROOT / "backend" / "scripts"

if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.recipes.recipe_gold_v3_quality_gate import evaluate_recipe_gold_v3_quality_gate  # noqa: E402
from app.recipes.recipe_gold_v3_semantic_consistency import check_semantic_consistency  # noqa: E402


def _load_script(name: str, filename: str):
    path = SCRIPTS_DIR / filename
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


hotfix_mod = _load_script(
    "apply_recipe_semantic_text_hotfix_q4_1",
    "apply_recipe_semantic_text_hotfix_q4_1.py",
)
display_mod = _load_script("set_recipe_display_titles_q4", "set_recipe_display_titles_q4.py")


def _recipe(**overrides) -> dict:
    base = {
        "title": "Тестовое блюдо",
        "display_title": "Тестовое блюдо для карточки",
        "description": "Описание тестового блюда для проверки семантики в рецепте.",
        "ingredients": [
            {"name": "морковь", "shopping_name": "морковь"},
        ],
        "steps": [{"step_number": 1, "text": "Нарежьте морковь и потушите до мягкости."}],
    }
    base.update(overrides)
    return base


def test_tofu_title_without_tofu_fails():
    findings = check_semantic_consistency(
        _recipe(
            title="Овощной суп с тофу",
            display_title="Овощной суп с тофу для карточки",
            ingredients=[{"name": "морковь", "shopping_name": "морковь"}],
        )
    )
    assert any(f["code"] == "semantic_tofu_mismatch" for f in findings)


def test_squid_title_with_shrimp_ingredients_fails():
    findings = check_semantic_consistency(
        _recipe(
            title="Салат с кальмарами",
            display_title="Салат с кальмарами для карточки",
            ingredients=[{"name": "креветки", "shopping_name": "креветки"}],
        )
    )
    codes = {f["code"] for f in findings}
    assert "semantic_squid_mismatch" in codes or "semantic_squid_vs_shrimp" in codes


def test_shrimp_title_with_shrimp_ingredients_passes():
    findings = check_semantic_consistency(
        _recipe(
            title="Салат с креветками",
            display_title="Салат с креветками для карточки",
            ingredients=[{"name": "креветки", "shopping_name": "креветки"}],
        )
    )
    assert findings == []


def test_quality_gate_fails_on_semantic_mismatch():
    recipe = _recipe(
        title="Овощной суп с тофу",
        display_title="Овощной суп с тофу для карточки",
        schema_version="recipe_gold_v3",
        status="gold",
        source_type="generated_original",
        source_signal_ids=["sig_1"],
        meal_type="lunch",
        category="soup",
        cuisine_style="семейная",
        servings=4,
        prep_time_min=10,
        cook_time_min=20,
        total_time_min=30,
        difficulty="easy",
        family_fit="high",
        originality={
            "is_original_planam_recipe": True,
            "no_source_title_used": True,
            "no_source_steps_used": True,
            "no_direct_copy": True,
            "source_similarity_risk": "low",
        },
        nutrition_per_serving={
            "kcal": 220,
            "protein_g": 8,
            "fat_g": 6,
            "carbs_g": 30,
            "fiber_g": 4,
            "salt_g": 1.0,
            "sugar_g": 3,
        },
        nutrition_confidence="estimated",
        restriction_keys=[],
        allergen_keys=[],
        diet_tags=[],
        shopping={"aggregation_safe": True, "has_fractional_amounts": False, "rounding_notes": ""},
        image_prompt_data={
            "dish_visual_summary": "Vegetable soup in a bowl.",
            "serving_style": "единый сервиз PLANAM",
            "avoid_visuals": ["текст"],
        },
        quality={"score": 90, "flags": [], "warnings": []},
        hero_image_url="/recipe-images/999/hero.webp",
    )
    result = evaluate_recipe_gold_v3_quality_gate([recipe], min_score=0, avg_score=0)
    assert result["recommendation"] == "FAIL"
    assert "semantic_tofu_mismatch" in result["errors_by_code"]


def _make_db_recipe(recipe_id: int) -> SimpleNamespace:
    payload = hotfix_mod.TEXT_HOTFIX[recipe_id]
    return SimpleNamespace(
        id=recipe_id,
        title="Old title",
        display_title="Old display",
        description="Old description",
        ingredients=[{"name": "креветки"}],
        steps=[{"text": "Смешайте креветки с огурецом."}],
        hero_image_url="/recipe-images/263/hero.webp",
        source_type="seed",
        is_active=True,
        **{k: payload[k] for k in ()},
    )


def test_hotfix_dry_run_does_not_mutate_recipe():
    recipe = _make_db_recipe(263)
    before = hotfix_mod._snapshot(recipe)
    hotfix_mod.apply_text_hotfix_to_recipe(recipe, hotfix_mod.TEXT_HOTFIX[263], commit=False)
    after = hotfix_mod._snapshot(recipe)
    assert before == after


def test_hotfix_commit_updates_only_text_fields():
    recipe = _make_db_recipe(261)
    before = hotfix_mod._snapshot(recipe)
    ingredients_before = list(recipe.ingredients)
    steps_before = list(recipe.steps)
    hero_before = recipe.hero_image_url
    source_before = recipe.source_type

    hotfix_mod.apply_text_hotfix_to_recipe(recipe, hotfix_mod.TEXT_HOTFIX[261], commit=True)
    after = hotfix_mod._snapshot(recipe)

    assert before != after
    assert after["title"] == hotfix_mod.TEXT_HOTFIX[261]["title"]
    assert after["display_title"] == hotfix_mod.TEXT_HOTFIX[261]["display_title"]
    assert after["description"] == hotfix_mod.TEXT_HOTFIX[261]["description"]
    assert recipe.ingredients == ingredients_before
    assert recipe.steps == steps_before
    assert recipe.hero_image_url == hero_before
    assert recipe.source_type == source_before


def test_display_title_script_only_updates_display_title():
    assert display_mod.UPDATABLE_FIELDS == frozenset({"display_title"})
    recipe = SimpleNamespace(
        title="Full recipe title",
        display_title="Old short",
        description="Recipe description stays intact.",
    )
    changed = display_mod.apply_display_title_only(recipe, "New short title", commit=True)
    assert changed is True
    assert recipe.display_title == "New short title"
    assert recipe.title == "Full recipe title"
    assert recipe.description == "Recipe description stays intact."


def test_display_title_script_dry_run_leaves_fields_unchanged():
    recipe = SimpleNamespace(
        title="Full recipe title",
        display_title="Old short",
        description="Recipe description stays intact.",
    )
    changed = display_mod.apply_display_title_only(recipe, "New short title", commit=False)
    assert changed is True
    assert recipe.display_title == "Old short"
    assert recipe.title == "Full recipe title"
    assert recipe.description == "Recipe description stays intact."
