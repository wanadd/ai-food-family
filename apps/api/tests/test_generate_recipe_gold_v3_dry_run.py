"""Tests for Gold V3 dry-run generator and postprocess (Stage F.1)."""

from __future__ import annotations

import asyncio
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

ROOT = Path(__file__).resolve().parents[3]
API_ROOT = ROOT / "apps" / "api"
SCRIPT = ROOT / "backend" / "scripts" / "generate_recipe_gold_v3_dry_run.py"
SIGNALS = ROOT / "exports" / "povarenok_culinary_signals_v3_100.jsonl"

if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.recipes.recipe_gold_v3_postprocess import postprocess_generated_recipe  # noqa: E402
from app.recipes.recipe_gold_v3_validation import ValidationIssue, ValidationResult  # noqa: E402


def _load_mod():
    spec = importlib.util.spec_from_file_location("generate_recipe_gold_v3_dry_run", SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["generate_recipe_gold_v3_dry_run"] = mod
    spec.loader.exec_module(mod)
    return mod


mod = _load_mod()


def _base_recipe(**overrides) -> dict:
    recipe = {
        "title": "Куриный суп",
        "category": "soup",
        "meal_type": "lunch",
        "ingredients": [
            {
                "name": "куриное филе",
                "amount": 300,
                "unit": "г",
                "display_amount": "300 г",
                "category": "мясо_птица",
                "optional": False,
                "shopping_name": "куриное филе",
            }
        ],
        "nutrition_per_serving": {"kcal": 300, "protein_g": 25, "fat_g": 10, "carbs_g": 20},
        "restriction_keys": ["vegan", "no_pork"],
        "diet_tags": ["vegan"],
    }
    recipe.update(overrides)
    return recipe


def test_reads_signals():
    signals = mod.load_jsonl(SIGNALS)
    assert len(signals) >= 10


def test_skips_avoid_when_enough_signals():
    signals = mod.load_jsonl(SIGNALS)
    selected = mod.select_diverse_signals(signals, 10, prefer_non_avoid=True)
    assert len(selected) == 10
    assert all(not s.get("avoid_for_planam") for s in selected)


def test_selects_diverse_signals():
    signals = mod.load_jsonl(SIGNALS)
    selected = mod.select_diverse_signals(signals, 5)
    families = {s.get("dish_family") for s in selected}
    assert len(families) >= 2


def test_no_api_recipe_passes_validator():
    signals = mod.load_jsonl(SIGNALS)
    good = [s for s in signals if not s.get("avoid_for_planam")][:1]
    recipe = mod.build_no_api_recipe(good[0], 1)
    recipe = postprocess_generated_recipe(mod.enrich_recipe_metadata(recipe, good[0]))
    from app.recipes.recipe_gold_v3_validation import validate_recipe_gold_v3

    assert not mod.originality_post_check(recipe)
    result = validate_recipe_gold_v3(recipe)
    assert result.ok, [e.code for e in result.errors]
    assert result.score >= 85


def test_originality_post_check_rejects_forbidden_fields():
    recipe = mod.build_no_api_recipe({"signal_id": "x", "dish_family": "суп"}, 1)
    recipe["source_url"] = "https://example.com"
    assert mod.originality_post_check(recipe)


def test_cost_guard_blocks_low_budget():
    ok, est = mod.check_cost_guard(limit=10, retry_invalid=1, max_cost_usd=0.01)
    assert not ok
    assert est > 0.01


def test_cost_guard_model_specific_estimate():
    ok_mini, est_mini = mod.check_cost_guard(
        limit=10, retry_invalid=2, max_cost_usd=1.50, model="gpt-4o-mini"
    )
    assert ok_mini
    assert est_mini == 1.5
    ok_strong, est_strong = mod.check_cost_guard(
        limit=10, retry_invalid=2, max_cost_usd=3.00, model="gpt-4.1"
    )
    assert ok_strong
    assert est_strong == 3.0


def test_estimated_cost_per_request_for_models():
    assert mod.estimated_cost_per_request("gpt-4o-mini") == 0.05
    assert mod.estimated_cost_per_request("gpt-4.1") == 0.10


def test_postprocess_normalizes_unit_sht_dot():
    recipe = _base_recipe(
        ingredients=[
            {
                "name": "яйцо",
                "amount": 2,
                "unit": "шт.",
                "display_amount": "",
                "category": "яйца",
                "shopping_name": "",
            }
        ]
    )
    out = postprocess_generated_recipe(recipe)
    assert out["ingredients"][0]["unit"] == "шт"
    assert out["ingredients"][0]["shopping_name"]
    assert out["ingredients"][0]["display_amount"]


def test_postprocess_normalizes_st_lozhka():
    recipe = _base_recipe(
        ingredients=[
            {
                "name": "соль",
                "amount": 1,
                "unit": "ст. л.",
                "display_amount": "1 ст. л.",
                "category": "специи",
                "shopping_name": "соль",
            }
        ]
    )
    out = postprocess_generated_recipe(recipe)
    assert out["ingredients"][0]["unit"] == "ст.л."


def test_postprocess_normalizes_category_myaso_ptitsy():
    recipe = _base_recipe(
        ingredients=[
            {
                "name": "куриное филе",
                "amount": 300,
                "unit": "г",
                "display_amount": "300 г",
                "category": "мясо птицы",
                "shopping_name": "куриное филе",
            }
        ]
    )
    out = postprocess_generated_recipe(recipe)
    assert out["ingredients"][0]["category"] == "мясо_птица"


def test_postprocess_fills_missing_shopping_name():
    recipe = _base_recipe(
        ingredients=[
            {
                "name": "куриное филе",
                "amount": 300,
                "unit": "г",
                "display_amount": "300 г",
                "category": "мясо_птица",
                "shopping_name": "",
            }
        ]
    )
    out = postprocess_generated_recipe(recipe)
    assert out["ingredients"][0]["shopping_name"] == "куриное филе"


def test_postprocess_fills_fiber_salt_sugar():
    recipe = _base_recipe(
        nutrition_per_serving={"kcal": 300, "protein_g": 25, "fat_g": 10, "carbs_g": 20}
    )
    out = postprocess_generated_recipe(recipe)
    n = out["nutrition_per_serving"]
    assert n["fiber_g"] is not None
    assert n["salt_g"] is not None
    assert n["sugar_g"] is not None


def test_postprocess_removes_vegan_from_chicken_recipe():
    out = postprocess_generated_recipe(_base_recipe())
    assert "vegan" not in out["restriction_keys"]


def test_postprocess_removes_no_milk_from_dairy_recipe():
    recipe = _base_recipe(
        ingredients=[
            {
                "name": "молоко",
                "amount": 200,
                "unit": "мл",
                "display_amount": "200 мл",
                "category": "молочные продукты",
                "shopping_name": "молоко",
            }
        ],
        restriction_keys=["lactose_free", "no_milk", "vegan"],
    )
    out = postprocess_generated_recipe(recipe)
    assert "lactose_free" not in out["restriction_keys"]
    assert "no_milk" not in out["restriction_keys"]
    assert "vegan" not in out["restriction_keys"]


def test_needs_quality_retry_for_low_score():
    result = ValidationResult(ok=True, errors=[], warnings=[], score=78)
    assert mod.needs_quality_retry(result, 85)
    assert not mod.needs_quality_retry(result, 70)


def test_validator_feedback_includes_score_warning():
    result = ValidationResult(
        ok=True,
        errors=[],
        warnings=[
            ValidationIssue(
                code="missing_fiber",
                severity="warning",
                message="fiber missing",
                path="nutrition_per_serving.fiber_g",
            )
        ],
        score=82,
    )
    feedback = mod.validator_feedback_from_result(result, retry_below_score=85)
    codes = {f["code"] for f in feedback}
    assert "missing_fiber" in codes
    assert "score_below_threshold" in codes
    assert "85" in next(f["message"] for f in feedback if f["code"] == "score_below_threshold")


def test_cli_accepts_retry_below_score():
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--help"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0
    assert "--retry-below-score" in proc.stdout


def test_report_includes_retry_below_score(tmp_path):
    out = tmp_path / "out.jsonl"
    report = tmp_path / "report.md"
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--signals",
            str(SIGNALS),
            "--output",
            str(out),
            "--report",
            str(report),
            "--limit",
            "2",
            "--dry-run",
            "--no-api",
            "--retry-below-score",
            "85",
            "--max-cost-usd",
            "0.01",
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    text = report.read_text(encoding="utf-8")
    assert "Retry below score" in text
    assert "85" in text
    assert "Low-score retries" in text


def test_generate_one_retries_on_low_score(monkeypatch):
    scores = iter([78, 92])
    stats = mod.GenerationStats()

    def fake_validate(_recipe):
        return ValidationResult(ok=True, errors=[], warnings=[], score=next(scores))

    monkeypatch.setattr(mod, "validate_recipe_gold_v3", fake_validate)

    signal = {
        "signal_id": "pov_sig_test",
        "dish_family": "суп",
        "meal_type_hints": ["lunch"],
        "category_hints": ["soup"],
        "avoid_for_planam": False,
    }

    async def run():
        return await mod.generate_one(
            signal,
            seq=1,
            no_api=True,
            temperature=0.7,
            model=None,
            retry_invalid=1,
            retry_below_score=85,
            stats=stats,
        )

    recipe = asyncio.run(run())
    assert recipe is not None
    assert stats.low_score_retries == 1
    assert stats.retries_used == 1
    assert stats.valid == 1
    assert recipe["quality"]["score"] == 92


def test_dry_run_no_api_cli(tmp_path):
    out = tmp_path / "out.jsonl"
    report = tmp_path / "report.md"
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--signals",
            str(SIGNALS),
            "--output",
            str(out),
            "--report",
            str(report),
            "--limit",
            "3",
            "--dry-run",
            "--no-api",
            "--max-cost-usd",
            "0.01",
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    assert out.exists()
    lines = [json.loads(l) for l in out.read_text(encoding="utf-8").splitlines() if l.strip()]
    assert len(lines) == 3
    assert report.exists()
    assert "source_url" not in out.read_text(encoding="utf-8")
