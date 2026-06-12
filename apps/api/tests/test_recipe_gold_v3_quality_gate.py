"""Tests for Recipe Gold V3 quality gate (Stage G/H)."""

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

from app.recipes.recipe_gold_v3_quality_gate import (  # noqa: E402
    evaluate_recipe_gold_v3_quality_gate,
    explain_originality_against_signal,
    explain_recipe_pair_similarity,
    ingredient_overlap_score,
    jaccard_similarity,
    title_similarity_score,
    _main_ingredient_family,
)

QUALITY_GATE_SOURCE = API_ROOT / "app" / "recipes" / "recipe_gold_v3_quality_gate.py"

CLI = ROOT / "backend" / "scripts" / "quality_gate_recipe_gold_v3.py"


def _ing(name: str, *, category: str = "╨╛╨▓╨╛╤Й╨╕", amount: float = 100) -> dict:
    return {
        "name": name,
        "amount": amount,
        "unit": "╨│",
        "display_amount": f"{int(amount)} ╨│",
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
        },
        "title": "╨Ъ╤Г╤А╨╕╨╜╨╛╨╡ ╤А╨░╨│╤Г ╤Б ╨╛╨▓╨╛╤Й╨░╨╝╨╕",
        "description": "╨б╤Л╤В╨╜╨╛╨╡ ╨┤╨╛╨╝╨░╤И╨╜╨╡╨╡ ╨▒╨╗╤О╨┤╨╛ ╤Б ╨║╤Г╤А╨╕╤Ж╨╡╨╣ ╨╕ ╨╛╨▓╨╛╤Й╨░╨╝╨╕ ╨┤╨╗╤П ╤Б╨╡╨╝╨╡╨╣╨╜╨╛╨│╨╛ ╤Г╨╢╨╕╨╜╨░.",
        "meal_type": "dinner",
        "category": "main",
        "cuisine_style": "╤Б╨╡╨╝╨╡╨╣╨╜╨░╤П",
        "servings": 4,
        "prep_time_min": 15,
        "cook_time_min": 30,
        "total_time_min": 45,
        "difficulty": "easy",
        "family_fit": "high",
        "ingredients": [
            _ing("╨║╤Г╤А╨╕╨╜╨╛╨╡ ╤Д╨╕╨╗╨╡", category="╨╝╤П╤Б╨╛_╨┐╤В╨╕╤Ж╨░", amount=500),
            _ing("╨║╨░╤А╤В╨╛╤Д╨╡╨╗╤М", category="╨╛╨▓╨╛╤Й╨╕", amount=300),
            _ing("╨╝╨╛╤А╨║╨╛╨▓╤М", category="╨╛╨▓╨╛╤Й╨╕", amount=150),
            _ing("╨╗╤Г╨║ ╤А╨╡╨┐╤З╨░╤В╤Л╨╣", category="╨╛╨▓╨╛╤Й╨╕", amount=100),
        ],
        "steps": [
            _step(1, "╨Э╨░╤А╨╡╨╢╤М╤В╨╡ ╨║╤Г╤А╨╕╤Ж╤Г ╨╕ ╨╛╨▓╨╛╤Й╨╕ ╨║╤Г╨▒╨╕╨║╨░╨╝╨╕ ╨╛╨┤╨╕╨╜╨░╨║╨╛╨▓╨╛╨│╨╛ ╤А╨░╨╖╨╝╨╡╤А╨░ ╨┤╨╗╤П ╤А╨░╨▓╨╜╨╛╨╝╨╡╤А╨╜╨╛╨│╨╛ ╨┐╤А╨╕╨│╨╛╤В╨╛╨▓╨╗╨╡╨╜╨╕╤П."),
            _step(2, "╨а╨░╨╖╨╛╨│╤А╨╡╨╣╤В╨╡ ╤Б╨║╨╛╨▓╨╛╤А╨╛╨┤╤Г ╤Б ╨╝╨░╤Б╨╗╨╛╨╝ ╨╕ ╨╛╨▒╨╢╨░╤А╤М╤В╨╡ ╨║╤Г╤А╨╕╤Ж╤Г ╨┤╨╛ ╨╖╨╛╨╗╨╛╤В╨╕╤Б╤В╨╛╨╣ ╨║╨╛╤А╨╛╤З╨║╨╕ ╤Б╨╛ ╨▓╤Б╨╡╤Е ╤Б╤В╨╛╤А╨╛╨╜."),
            _step(3, "╨Ф╨╛╨▒╨░╨▓╤М╤В╨╡ ╨╛╨▓╨╛╤Й╨╕, ╨┐╨╡╤А╨╡╨╝╨╡╤И╨░╨╣╤В╨╡ ╨╕ ╤В╤Г╤И╨╕╤В╨╡ ╨┐╨╛╨┤ ╨║╤А╤Л╤И╨║╨╛╨╣ ╨┤╨▓╨░╨┤╤Ж╨░╤В╤М ╨╝╨╕╨╜╤Г╤В ╨╜╨░ ╤Б╤А╨╡╨┤╨╜╨╡╨╝ ╨╛╨│╨╜╨╡."),
            _step(4, "╨Я╨╡╤А╨╡╨┤ ╨┐╨╛╨┤╨░╤З╨╡╨╣ ╨┤╨░╨╣╤В╨╡ ╨▒╨╗╤О╨┤╤Г ╨╜╨░╤Б╤В╨╛╤П╤В╤М╤Б╤П ╨╕ ╨┐╨╛╤Б╤Л╨┐╤М╤В╨╡ ╨╖╨╡╨╗╨╡╨╜╤М╤О ╨┐╨╛ ╨╢╨╡╨╗╨░╨╜╨╕╤О."),
        ],
        "nutrition_per_serving": {
            "kcal": 410,
            "protein_g": 30,
            "fat_g": 15,
            "carbs_g": 35,
            "fiber_g": 5,
            "salt_g": 1.2,
            "sugar_g": 3,
        },
        "restriction_keys": ["no_pork", "no_alcohol"],
        "allergen_keys": [],
        "diet_tags": ["balanced"],
        "shopping": {"aggregation_safe": True, "has_fractional_amounts": False, "rounding_notes": ""},
        "image_prompt_data": {
            "dish_visual_summary": "╨Ъ╤Г╤А╨╕╨╜╨╛╨╡ ╤А╨░╨│╤Г ╨▓ ╤В╨░╤А╨╡╨╗╨║╨╡",
            "serving_style": "╨╡╨┤╨╕╨╜╤Л╨╣ ╤Б╨╡╤А╨▓╨╕╨╖ PLANAM",
            "avoid_visuals": ["╤В╨╡╨║╤Б╤В", "╨╗╨╛╨│╨╛╤В╨╕╨┐╤Л", "╤А╤Г╨║╨╕", "╨│╤А╤П╨╖╨╜╤Л╨╣ ╤Д╨╛╨╜"],
        },
        "quality": {"score": 0, "flags": [], "warnings": []},
    }
    base.update(overrides)
    return base


def test_source_url_leak_fails():
    recipe = _valid_recipe(source_url="https://example.com")
    issues = explain_originality_against_signal(recipe, None)
    assert any(i["code"] == "source_url_leak" for i in issues)


def test_original_title_leak_fails():
    recipe = _valid_recipe(original_title="╨б╤В╨░╤А╤Л╨╣ ╤А╨╡╤Ж╨╡╨┐╤В")
    issues = explain_originality_against_signal(recipe, None)
    assert any(i["code"] == "original_title_leak" for i in issues)


def test_original_steps_leak_fails():
    recipe = _valid_recipe(original_steps=["╤И╨░╨│ 1"])
    issues = explain_originality_against_signal(recipe, None)
    assert any(i["code"] == "original_steps_leak" for i in issues)


def test_real_source_title_in_signal_fails():
    signal = {
        "signal_id": "pov_sig_x",
        "original_title": "╨Ф╨╛╨╝╨░╤И╨╜╨╕╨╡ ╨║╤Г╤А╨╕╨╜╤Л╨╡ ╨║╨╛╤В╨╗╨╡╤В╤Л ╤Б ╨║╨░╤А╤В╨╛╤Д╨╡╨╗╤М╨╜╤Л╨╝ ╨┐╤О╤А╨╡",
    }
    recipe = _valid_recipe(title="╨Ф╨╛╨╝╨░╤И╨╜╨╕╨╡ ╨║╤Г╤А╨╕╨╜╤Л╨╡ ╨║╨╛╤В╨╗╨╡╤В╤Л ╤Б ╨║╨░╤А╤В╨╛╤Д╨╡╨╗╤М╨╜╤Л╨╝ ╨┐╤О╤А╨╡")
    issues = explain_originality_against_signal(recipe, signal)
    assert any(i["code"] == "title_too_close_to_signal" for i in issues)
    assert any(i["code"] == "source_leakage_in_signal" for i in issues)


def test_abstract_signal_phrase_similarity_warning_not_hard_fail():
    signal = {
        "signal_id": "pov_sig_x",
        "dish_family": "╤Б╤Г╨┐",
        "generation_prompt_hints": [
            "╤Б╨┤╨╡╨╗╨░╤В╤М ╨╛╤А╨╕╨│╨╕╨╜╨░╨╗╤М╨╜╨╛╨╡ ╤Б╨╡╨╝╨╡╨╣╨╜╨╛╨╡ ╨▒╨╗╤О╨┤╨╛ (╤Б╤Г╨┐) ╨╜╨░ ╨╛╤Б╨╜╨╛╨▓╨╡ ╨╛╨▓╨╛╤Й╨╕",
        ],
    }
    recipe = _valid_recipe(
        title="╨Ю╨▓╨╛╤Й╨╜╨╛╨╣ ╤Б╤Г╨┐ ╤Б ╨╝╨╛╤А╨║╨╛╨▓╤М╤О",
        source_signal_ids=["pov_sig_x"],
    )
    issues = explain_originality_against_signal(recipe, signal)
    assert not any(i["code"] == "title_too_close_to_signal" for i in issues)
    assert any(i["code"] == "title_moderately_similar" for i in issues)
    result = evaluate_recipe_gold_v3_quality_gate(
        [recipe],
        signals=[signal],
        min_score=85,
        avg_score=0,
    )
    assert result["recommendation"] == "PASS"


def test_safe_different_title_passes_signal_check():
    signal = {"signal_id": "pov_sig_x", "generation_prompt_hints": ["╨╗╤С╨│╨║╨╕╨╣ ╨╛╨▒╨╡╨┤"]}
    recipe = _valid_recipe(title="╨в╤Г╤И╤С╨╜╨░╤П ╨╕╨╜╨┤╨╡╨╣╨║╨░ ╤Б ╨╛╨▓╨╛╤Й╨░╨╝╨╕")
    issues = explain_originality_against_signal(recipe, signal)
    assert not any(i["code"] == "title_too_close_to_signal" for i in issues)


def test_pair_duplicate_titles_fail():
    a = _valid_recipe(title="╨б╤Г╨┐ ╤Б ╤Д╤А╨╕╨║╨░╨┤╨╡╨╗╤М╨║╨░╨╝╨╕")
    b = _valid_recipe(title="╨б╤Г╨┐ ╤Б ╤Д╤А╨╕╨║╨░╨┤╨╡╨╗╤М╨║╨░╨╝╨╕")
    issues = explain_recipe_pair_similarity(a, b, index_a=0, index_b=1)
    assert any(i["code"] == "title_too_close_to_recipe" for i in issues)


def test_pair_high_ingredient_overlap_fails():
    a = _valid_recipe()
    b = _valid_recipe(title="╨Ф╤А╤Г╨│╨╛╨╡ ╨▒╨╗╤О╨┤╨╛ ╤Б ╨║╤Г╤А╨╕╤Ж╨╡╨╣")
    assert ingredient_overlap_score(a, b) >= 0.85
    issues = explain_recipe_pair_similarity(a, b, index_a=0, index_b=1)
    assert any(i["code"] == "ingredients_too_duplicate" for i in issues)


def test_moderate_overlap_warning():
    a = _valid_recipe(
        title="╨Ю╨▓╨╛╤Й╨╜╨╛╨╡ ╤А╨░╨│╤Г A",
        ingredients=[
            _ing("╨║╨░╤А╤В╨╛╤Д╨╡╨╗╤М"),
            _ing("╨╝╨╛╤А╨║╨╛╨▓╤М"),
            _ing("╨╗╤Г╨║ ╤А╨╡╨┐╤З╨░╤В╤Л╨╣"),
            _ing("╤Б╨╡╨╗╤М╨┤╨╡╤А╨╡╨╣"),
            _ing("╨║╨░╨┐╤Г╤Б╤В╨░"),
        ],
    )
    b = _valid_recipe(
        title="╨Ю╨▓╨╛╤Й╨╜╨╛╨╡ ╤А╨░╨│╤Г B",
        ingredients=[
            _ing("╨║╨░╤А╤В╨╛╤Д╨╡╨╗╤М"),
            _ing("╨╝╨╛╤А╨║╨╛╨▓╤М"),
            _ing("╨╗╤Г╨║ ╤А╨╡╨┐╤З╨░╤В╤Л╨╣"),
            _ing("╤Б╨╡╨╗╤М╨┤╨╡╤А╨╡╨╣"),
            _ing("╨║╨░╨▒╨░╤З╨╛╨║"),
        ],
    )
    assert 0.65 <= ingredient_overlap_score(a, b) < 0.85
    issues = explain_recipe_pair_similarity(a, b, index_a=0, index_b=1)
    assert any(i["code"] == "ingredient_overlap_moderate" for i in issues)


def _veg_only_ings(prefix: str) -> list[dict]:
    return [
        _ing(f"{prefix}_kartofel"),
        _ing(f"{prefix}_morkov"),
        _ing(f"{prefix}_luk"),
        _ing(f"{prefix}_kapusta"),
    ]


def test_category_overconcentration_hard_fail():
    recipes = []
    for i in range(7):
        recipes.append(
            _valid_recipe(
                title=f"╨б╤Г╨┐ ╨╜╨╛╨╝╨╡╤А {i}",
                category="soup",
                meal_type="lunch",
                ingredients=_veg_only_ings(f"soup{i}"),
                steps=[
                    _step(1, f"╨Я╨╛╨┤╨│╨╛╤В╨╛╨▓╨║╨░ ╤Б╤Г╨┐╨░ {i}a: ╨╜╨░╤А╨╡╨╢╤М╤В╨╡ ╨╛╨▓╨╛╤Й╨╕ ╨╕ ╨┐╤А╨╛╨╝╨╛╨╣╤В╨╡ ╨╖╨╡╨╗╨╡╨╜╤М."),
                    _step(2, f"╨б╤Г╨┐ {i}b: ╨╛╨▒╨╢╨░╤А╤М╤В╨╡ ╨╛╤Б╨╜╨╛╨▓╤Г ╨╜╨░ ╤Б╨║╨╛╨▓╨╛╤А╨╛╨┤╨╡ ╨┤╨╛ ╨░╤А╨╛╨╝╨░╤В╨░."),
                    _step(3, f"╨б╤Г╨┐ {i}c: ╨╖╨░╨╗╨╡╨╣╤В╨╡ ╨▓╨╛╨┤╨╛╨╣ ╨╕ ╨▓╨░╤А╨╕╤В╨╡ ╨┤╨▓╨░╨┤╤Ж╨░╤В╤М ╨╝╨╕╨╜╤Г╤В."),
                    _step(4, f"╨б╤Г╨┐ {i}d: ╨┐╨╛╨┤╨░╨╣╤В╨╡ ╨│╨╛╤А╤П╤З╨╕╨╝ ╤Б ╨╖╨╡╨╗╨╡╨╜╤М╤О."),
                ],
            )
        )
    recipes.extend(
        _valid_recipe(
            title=f"╨б╨░╨╗╨░╤В {i}",
            category="salad",
            meal_type="lunch",
            ingredients=_veg_only_ings(f"salad{i}"),
        )
        for i in range(3)
    )
    result = evaluate_recipe_gold_v3_quality_gate(recipes, min_score=85, avg_score=0)
    assert result["errors_by_code"].get("batch_category_overconcentration", 0) > 0


def test_meal_type_overconcentration_warning():
    recipes = [
        _valid_recipe(
            title=f"╨Ю╨▒╨╡╨┤ {i}",
            meal_type="lunch",
            category="main" if i % 2 else "side",
            ingredients=_veg_only_ings(f"lunch{i}"),
        )
        for i in range(9)
    ] + [
        _valid_recipe(
            title="╨г╨╢╨╕╨╜",
            meal_type="dinner",
            category="main",
            ingredients=_veg_only_ings("dinner"),
        )
    ]
    result = evaluate_recipe_gold_v3_quality_gate(recipes, min_score=85, avg_score=0)
    assert result["warnings_by_code"].get("meal_type_concentration_warning", 0) > 0
    assert result["recommendation"] != "FAIL" or result["errors_by_code"]


def test_low_score_fails():
    recipe = _valid_recipe(title="")
    result = evaluate_recipe_gold_v3_quality_gate([recipe], min_score=85, avg_score=90)
    assert result["recommendation"] == "FAIL"
    assert (
        result["errors_by_code"].get("low_score", 0) > 0
        or result["errors_by_code"].get("invalid_recipe", 0) > 0
    )


def test_missing_shopping_name_fails():
    from app.recipes.recipe_gold_v3_quality_gate import _check_shopping

    ings = [
        {
            "name": "╨║╨░╤А╤В╨╛╤Д╨╡╨╗╤М",
            "amount": 100,
            "unit": "╨│",
            "display_amount": "100 ╨│",
            "category": "╨╛╨▓╨╛╤Й╨╕",
            "optional": False,
            "shopping_name": "",
        },
        _ing("╨╝╨╛╤А╨║╨╛╨▓╤М"),
        _ing("╨╗╤Г╨║ ╤А╨╡╨┐╤З╨░╤В╤Л╨╣"),
        _ing("╨┐╨╡╤А╨╡╤Ж ╨▒╨╛╨╗╨│╨░╤А╤Б╨║╨╕╨╣"),
    ]
    recipe = _valid_recipe(ingredients=ings)
    issues = _check_shopping(recipe, recipe_index=0)
    assert any(i["code"] == "missing_shopping_name" for i in issues)


def test_diverse_batch_passes_quality_gate():
    titles = [
        "╨в╤Г╤И╤С╨╜╨░╤П ╨╕╨╜╨┤╨╡╨╣╨║╨░",
        "╨Ю╨▓╨╛╤Й╨╜╨╛╨╣ ╤Б╤Г╨┐",
        "╨б╨░╨╗╨░╤В ╤Б ╤Д╨░╤Б╨╛╨╗╤М╤О",
        "╨У╤А╨╡╤З╨║╨░ ╤Б ╨│╤А╨╕╨▒╨░╨╝╨╕",
        "╨Ч╨░╨┐╨╡╤З╤С╨╜╨╜╨░╤П ╤А╤Л╨▒╨░",
        "╨Ъ╨░╨▒╨░╤З╨║╨╕ ╤Д╨░╤А╤И╨╕╤А╨╛╨▓╨░╨╜╨╜╤Л╨╡",
        "╨а╨░╨│╤Г ╨╕╨╖ ╤В╨╡╨╗╤П╤В╨╕╨╜╤Л",
        "╨б╤Г╨┐-╨┐╤О╤А╨╡",
        "╨Ю╨▓╨╛╤Й╨╜╨░╤П ╨╖╨░╨┐╨╡╨║╨░╨╜╨║╨░",
        "╨Я╨░╤Б╤В╨░ ╤Б ╨╛╨▓╨╛╤Й╨░╨╝╨╕",
    ]
    categories = ["main", "soup", "salad", "side", "main", "main", "main", "soup", "main", "main"]
    recipes = []
    for i, (title, cat) in enumerate(zip(titles, categories)):
        steps = [
            _step(1, f"╨г╨╜╨╕╨║╨░╨╗╤М╨╜╨░╤П ╨┐╨╛╨┤╨│╨╛╤В╨╛╨▓╨║╨░ {i}a: ╨╜╨░╤А╨╡╨╢╤М╤В╨╡ ╨┐╤А╨╛╨┤╤Г╨║╤В╤Л ╨║╤Г╨▒╨╕╨║╨░╨╝╨╕ ╨┤╨╗╤П {title}."),
            _step(2, f"╨в╨╡╤Е╨╜╨╕╨║╨░ {i}b: ╨╕╤Б╨┐╨╛╨╗╤М╨╖╤Г╨╣╤В╨╡ ╤Б╨║╨╛╨▓╨╛╤А╨╛╨┤╤Г ╨╕╨╗╨╕ ╨║╨░╤Б╤В╤А╤О╨╗╤О ╨┤╨╗╤П {title}."),
            _step(3, f"╨б╨▒╨╛╤А╨║╨░ {i}c: ╤Б╨╛╨╡╨┤╨╕╨╜╨╕╤В╨╡ ╨║╨╛╨╝╨┐╨╛╨╜╨╡╨╜╤В╤Л ╨╕ ╨┤╨╛╨▓╨╡╨┤╨╕╤В╨╡ {title} ╨┤╨╛ ╨│╨╛╤В╨╛╨▓╨╜╨╛╤Б╤В╨╕."),
            _step(4, f"╨д╨╕╨╜╨░╨╗ {i}d: ╨╛╤Д╨╛╤А╨╝╨╕╤В╨╡ {title} ╨╕ ╨┐╨╛╨┤╨░╨╣╤В╨╡ ╤Б╨╡╨╝╤М╨╡."),
        ]
        recipes.append(
            _valid_recipe(
                title=title,
                category=cat,
                meal_type="lunch" if i < 8 else "dinner",
                source_signal_ids=[f"pov_sig_{i:06d}"],
                steps=steps,
                ingredients=[
                    _ing(f"╨╕╨╜╨│╤А╨╡╨┤╨╕╨╡╨╜╤В_{i}_a", category="╨╛╨▓╨╛╤Й╨╕", amount=100 + i),
                    _ing(f"╨╕╨╜╨│╤А╨╡╨┤╨╕╨╡╨╜╤В_{i}_b", category="╨║╤А╤Г╨┐╤Л", amount=80 + i),
                    _ing(f"╤Б╨┐╨╡╤Ж╨╕╤П_{i}", category="╤Б╨┐╨╡╤Ж╨╕╨╕", amount=10),
                    _ing(f"╨╝╨░╤Б╨╗╨╛_{i}", category="╨╝╨░╤Б╨╗╨░/╤Б╨╛╤Г╤Б╤Л", amount=20),
                ],
            )
        )
    result = evaluate_recipe_gold_v3_quality_gate(
        recipes, min_score=85, avg_score=90
    )
    assert result["recommendation"] == "PASS", result["errors_by_code"]
    assert result["summary"]["valid"] == 10


def test_jaccard_and_title_similarity():
    assert jaccard_similarity("╨║╤Г╤А╨╕╨╜╨╛╨╡ ╤А╨░╨│╤Г", "╨║╤Г╤А╨╕╨╜╨╛╨╡ ╤А╨░╨│╤Г ╤Б ╨╛╨▓╨╛╤Й╨░╨╝╨╕") > 0.3
    assert title_similarity_score("╨б╤Г╨┐ ╤Б ╤Д╤А╨╕╨║╨░╨┤╨╡╨╗╤М╨║╨░╨╝╨╕", "╨б╤Г╨┐ ╤Б ╤Д╤А╨╕╨║╨░╨┤╨╡╨╗╤М╨║╨░╨╝╨╕") >= 0.8


def test_cli_report_writes_pass(tmp_path):
    inp = tmp_path / "in.jsonl"
    report = tmp_path / "report.md"
    recipes = [
        _valid_recipe(
            title="╨С╨╗╤О╨┤╨╛ ╨╛╨┤╨╕╨╜",
            category="main",
            ingredients=[
                _ing("╨╕╨╜╨┤╨╡╨╣╨║╨░", category="╨╝╤П╤Б╨╛_╨┐╤В╨╕╤Ж╨░", amount=400),
                _ing("╤А╨╕╤Б", category="╨║╤А╤Г╨┐╤Л", amount=200),
                _ing("╨╝╨╛╤А╨║╨╛╨▓╤М", category="╨╛╨▓╨╛╤Й╨╕", amount=100),
                _ing("╨╗╤Г╨║ ╤А╨╡╨┐╤З╨░╤В╤Л╨╣", category="╨╛╨▓╨╛╤Й╨╕", amount=80),
            ],
            steps=[
                _step(1, "╨Р╨╗╤М╤Д╨░ ╨┐╨╛╨┤╨│╨╛╤В╨╛╨▓╨║╨░: ╨┐╤А╨╛╨╝╨╛╨╣╤В╨╡ ╨║╤А╤Г╨┐╤Л ╨╕ ╨╛╨▓╨╛╤Й╨╕ ╨┐╨╡╤А╨╡╨┤ ╨▓╨░╤А╨║╨╛╨╣ ╨▒╨╗╤О╨┤╨░ ╨╛╨┤╨╕╨╜."),
                _step(2, "╨Р╨╗╤М╤Д╨░ ╨╢╨░╤А╨║╨░: ╨╛╨▒╨╢╨░╤А╤М╤В╨╡ ╨╗╤Г╨║ ╤Б ╨╝╨╛╤А╨║╨╛╨▓╤М╤О ╨╜╨░ ╤А╨░╤Б╤В╨╕╤В╨╡╨╗╤М╨╜╨╛╨╝ ╨╝╨░╤Б╨╗╨╡."),
                _step(3, "╨Р╨╗╤М╤Д╨░ ╤В╤Г╤И╨╡╨╜╨╕╨╡: ╨┤╨╛╨▒╨░╨▓╤М╤В╨╡ ╨╝╤П╤Б╨╛ ╨╕ ╤В╤Г╤И╨╕╤В╨╡ ╤Б╨╛╤А╨╛╨║ ╨╝╨╕╨╜╤Г╤В ╨┐╨╛╨┤ ╨║╤А╤Л╤И╨║╨╛╨╣."),
                _step(4, "╨Р╨╗╤М╤Д╨░ ╨┐╨╛╨┤╨░╤З╨░: ╨▓╤Л╨╗╨╛╨╢╨╕╤В╨╡ ╨╜╨░ ╤В╨░╤А╨╡╨╗╨║╤Г ╨╕ ╤Г╨║╤А╨░╤Б╤М╤В╨╡ ╨╖╨╡╨╗╨╡╨╜╤М╤О."),
            ],
        ),
        _valid_recipe(
            title="╨С╨╗╤О╨┤╨╛ ╨┤╨▓╨░",
            category="soup",
            meal_type="lunch",
            ingredients=[
                _ing("╤В╤А╨╡╤Б╨║╨░", category="╤А╤Л╨▒╨░", amount=300),
                _ing("╨║╨░╤А╤В╨╛╤Д╨╡╨╗╤М", category="╨╛╨▓╨╛╤Й╨╕", amount=200),
                _ing("╨╗╤Г╨║-╨┐╨╛╤А╨╡╨╣", category="╨╛╨▓╨╛╤Й╨╕", amount=100),
                _ing("╤Б╨╗╨╕╨▓╨║╨╕", category="╨╝╨╛╨╗╨╛╤З╨╜╤Л╨╡ ╨┐╤А╨╛╨┤╤Г╨║╤В╤Л", amount=150),
            ],
            steps=[
                _step(1, "╨С╨╡╤В╨░ ╨▒╤Г╨╗╤М╨╛╨╜: ╤Б╨▓╨░╤А╨╕╤В╨╡ ╨┐╤А╨╛╨╖╤А╨░╤З╨╜╤Л╨╣ ╨▒╤Г╨╗╤М╨╛╨╜ ╨╕╨╖ ╨║╤Г╤А╨╕╤Ж╤Л ╨╕ ╨║╨╛╤А╨╡╨╜╤М╤П."),
                _step(2, "╨С╨╡╤В╨░ ╨╛╨▓╨╛╤Й╨╕: ╨╜╨░╤А╨╡╨╢╤М╤В╨╡ ╨║╨░╨▒╨░╤З╨║╨╕ ╨╕ ╨║╨░╤А╤В╨╛╤Д╨╡╨╗╤М ╤В╨╛╨╜╨║╨╕╨╝╨╕ ╨╗╨╛╨╝╤В╨╕╨║╨░╨╝╨╕."),
                _step(3, "╨С╨╡╤В╨░ ╤Б╨╝╨╡╤И╨╕╨▓╨░╨╜╨╕╨╡: ╨┤╨╛╨▒╨░╨▓╤М╤В╨╡ ╨┐╨░╤Б╤В╤Г ╨╕ ╨┐╤А╨╛╨▓╨░╤А╨╕╤В╨╡ ╨┐╤П╤В╤М ╨╝╨╕╨╜╤Г╤В."),
                _step(4, "╨С╨╡╤В╨░ ╨┐╨╛╨┤╨░╤З╨░: ╨╖╨░╨┐╤А╨░╨▓╤М╤В╨╡ ╤Б╨╝╨╡╤В╨░╨╜╨╛╨╣ ╨╕ ╨┐╨╛╨┤╨░╨╣╤В╨╡ ╤Б ╤Е╨╗╨╡╨▒╨╛╨╝."),
            ],
        ),
    ]
    with inp.open("w", encoding="utf-8") as fh:
        for r in recipes:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    proc = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "--input",
            str(inp),
            "--report",
            str(report),
            "--min-score",
            "85",
            "--avg-score",
            "80",
            "--dry-run",
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    assert report.exists()
    text = report.read_text(encoding="utf-8")
    assert "Quality gate" in text
    assert "PASS" in text


def test_cli_returns_nonzero_on_fail(tmp_path):
    inp = tmp_path / "bad.jsonl"
    report = tmp_path / "report.md"
    bad = _valid_recipe(source_url="https://leak.example")
    inp.write_text(json.dumps(bad, ensure_ascii=False) + "\n", encoding="utf-8")
    proc = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "--input",
            str(inp),
            "--report",
            str(report),
            "--avg-score",
            "100",
            "--dry-run",
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 1
    assert "FAIL" in report.read_text(encoding="utf-8")


def test_main_ingredient_family_detects_chicken_fish_legumes():
    chicken = _valid_recipe(
        ingredients=[
            _ing("╨║╤Г╤А╨╕╨╜╨╛╨╡ ╤Д╨╕╨╗╨╡", category="╨╝╤П╤Б╨╛_╨┐╤В╨╕╤Ж╨░"),
            _ing("╨╝╨╛╤А╨║╨╛╨▓╤М"),
            _ing("╨╗╤Г╨║ ╤А╨╡╨┐╤З╨░╤В╤Л╨╣"),
            _ing("╤А╨╕╤Б", category="╨║╤А╤Г╨┐╤Л"),
        ]
    )
    fish = _valid_recipe(
        ingredients=[
            _ing("╤В╤А╨╡╤Б╨║╨░", category="╤А╤Л╨▒╨░"),
            _ing("╨║╨░╤А╤В╨╛╤Д╨╡╨╗╤М"),
            _ing("╨╗╤Г╨║-╨┐╨╛╤А╨╡╨╣"),
            _ing("╤Б╨╗╨╕╨▓╨║╨╕", category="╨╝╨╛╨╗╨╛╤З╨╜╤Л╨╡ ╨┐╤А╨╛╨┤╤Г╨║╤В╤Л"),
        ]
    )
    legumes = _valid_recipe(
        ingredients=[
            _ing("╤Д╨░╤Б╨╛╨╗╤М", category="╨▒╨╛╨▒╨╛╨▓╤Л╨╡"),
            _ing("╨╝╨╛╤А╨║╨╛╨▓╤М"),
            _ing("╨╗╤Г╨║ ╤А╨╡╨┐╤З╨░╤В╤Л╨╣"),
            _ing("╤В╨╛╨╝╨░╤В", category="╨╛╨▓╨╛╤Й╨╕"),
        ]
    )
    assert _main_ingredient_family(chicken) == "chicken"
    assert _main_ingredient_family(fish) == "fish"
    assert _main_ingredient_family(legumes) == "legumes_tofu"


def test_all_other_family_does_not_hard_fail():
    categories = ["main", "soup", "salad", "side", "main", "soup", "salad", "side", "main", "side"]
    recipes = [
        _valid_recipe(
            title=f"╨С╨╗╤О╨┤╨╛ {i}",
            category=categories[i],
            meal_type="lunch" if i < 8 else "dinner",
            ingredients=[
                _ing(f"╨┐╤А╨╛╨┤╤Г╨║╤В_{i}_a"),
                _ing(f"╨┐╤А╨╛╨┤╤Г╨║╤В_{i}_b"),
                _ing(f"╨┐╤А╨╛╨┤╤Г╨║╤В_{i}_c"),
                _ing(f"╨┐╤А╨╛╨┤╤Г╨║╤В_{i}_d"),
            ],
            steps=[
                _step(
                    1,
                    f"╨г╨╜╨╕╨║╨░╨╗╤М╨╜╨░╤П ╨┐╨╛╨┤╨│╨╛╤В╨╛╨▓╨║╨░ {i}a: ╨┐╤А╨╛╨╝╨╛╨╣╤В╨╡ ╨╕ ╨╜╨░╤А╨╡╨╢╤М╤В╨╡ ╨║╨╛╨╝╨┐╨╛╨╜╨╡╨╜╤В╤Л ╨┤╨╗╤П ╨▒╨╗╤О╨┤╨░ ╨╜╨╛╨╝╨╡╤А {i}.",
                ),
                _step(
                    2,
                    f"╨Ю╤Б╨╜╨╛╨▓╨╜╨░╤П ╤В╨╡╤Е╨╜╨╕╨║╨░ {i}b: ╨╕╤Б╨┐╨╛╨╗╤М╨╖╤Г╨╣╤В╨╡ ╤Б╨║╨╛╨▓╨╛╤А╨╛╨┤╤Г ╨╕╨╗╨╕ ╨║╨░╤Б╤В╤А╤О╨╗╤О ╨┤╨╗╤П ╨▒╨╗╤О╨┤╨░ {i}.",
                ),
                _step(
                    3,
                    f"╨б╨▒╨╛╤А╨║╨░ {i}c: ╤Б╨╛╨╡╨┤╨╕╨╜╨╕╤В╨╡ ╨║╨╛╨╝╨┐╨╛╨╜╨╡╨╜╤В╤Л ╨╕ ╨┤╨╛╨▓╨╡╨┤╨╕╤В╨╡ ╨▒╨╗╤О╨┤╨╛ {i} ╨┤╨╛ ╨│╨╛╤В╨╛╨▓╨╜╨╛╤Б╤В╨╕.",
                ),
                _step(4, f"╨Я╨╛╨┤╨░╤З╨░ {i}d: ╨╛╤Д╨╛╤А╨╝╨╕╤В╨╡ ╨▒╨╗╤О╨┤╨╛ {i} ╨╕ ╨┐╨╛╨┤╨░╨╣╤В╨╡ ╤Б╨╡╨╝╤М╨╡."),
            ],
        )
        for i in range(10)
    ]
    result = evaluate_recipe_gold_v3_quality_gate(recipes, min_score=85, avg_score=0)
    assert result["diversity"]["main_ingredient_families"] == {"other": 10}
    assert result["errors_by_code"].get("batch_main_ingredient_overconcentration", 0) == 0
    assert result["diversity"]["main_ingredient_overconcentration"] is False


def test_quality_gate_source_has_no_mojibake_markers():
    raw = QUALITY_GATE_SOURCE.read_text(encoding="utf-8")
    for bad in ("\u2558", "\u2564", "╤В╨Р╨д"):
        assert bad not in raw


def test_fail_on_warning_makes_warning_fail():
    recipes = [
        _valid_recipe(
            title=f"╨Ю╨▒╨╡╨┤ {i}",
            meal_type="lunch",
            category="main" if i % 2 else "side",
            ingredients=_veg_only_ings(f"warn{i}"),
        )
        for i in range(9)
    ] + [
        _valid_recipe(
            title="╨г╨╢╨╕╨╜",
            meal_type="dinner",
            category="main",
            ingredients=_veg_only_ings("warnd"),
        )
    ]
    without = evaluate_recipe_gold_v3_quality_gate(
        recipes, min_score=85, avg_score=0, fail_on_warning=False
    )
    with_flag = evaluate_recipe_gold_v3_quality_gate(
        recipes, min_score=85, avg_score=0, fail_on_warning=True
    )
    assert without["warnings_by_code"].get("meal_type_concentration_warning", 0) > 0
    assert with_flag["recommendation"] == "FAIL"
