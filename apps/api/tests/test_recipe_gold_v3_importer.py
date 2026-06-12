"""Tests for Recipe Gold V3 importer dry-run (Stage R)."""

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

from app.recipes.recipe_gold_v3_importer import (  # noqa: E402
    detect_existing_duplicates,
    load_gold_v3_jsonl,
    map_gold_v3_to_db_payload,
    normalize_recipe_title,
    plan_import_gold_v3_batch,
    get_mapping_summary,
)

CLI = ROOT / "backend" / "scripts" / "import_recipe_gold_v3_dry_run.py"


def _ing(name: str, *, category: str = "\u043e\u0432\u043e\u0449\u0438", amount: float = 100) -> dict:
    return {
        "name": name,
        "amount": amount,
        "unit": "\u0433",
        "display_amount": f"{int(amount)} \u0433",
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
        "title": "\u041a\u0443\u0440\u0438\u043d\u043e\u0435 \u0440\u0430\u0433\u0443 \u0441 \u043e\u0432\u043e\u0449\u0430\u043c\u0438",
        "description": "\u0421\u044b\u0442\u043d\u043e\u0435 \u0434\u043e\u043c\u0430\u0448\u043d\u0435\u0435 \u0431\u043b\u044e\u0434\u043e.",
        "meal_type": "dinner",
        "category": "main",
        "cuisine_style": "\u0441\u0435\u043c\u0435\u0439\u043d\u0430\u044f",
        "servings": 4,
        "prep_time_min": 15,
        "cook_time_min": 30,
        "total_time_min": 45,
        "difficulty": "easy",
        "family_fit": "high",
        "ingredients": [
            _ing("\u043a\u0443\u0440\u0438\u043d\u043e\u0435 \u0444\u0438\u043b\u0435", category="\u043c\u044f\u0441\u043e_\u043f\u0442\u0438\u0446\u0430", amount=500),
            _ing("\u043a\u0430\u0440\u0442\u043e\u0444\u0435\u043b\u044c"),
            _ing("\u043c\u043e\u0440\u043a\u043e\u0432\u044c"),
            _ing("\u043b\u0443\u043a \u0440\u0435\u043f\u0447\u0430\u0442\u044b\u0439"),
        ],
        "steps": [
            _step(1, "\u041d\u0430\u0440\u0435\u0436\u044c\u0442\u0435 \u043a\u0443\u0440\u0438\u0446\u0443 \u0438 \u043e\u0432\u043e\u0449\u0438 \u043a\u0443\u0431\u0438\u043a\u0430\u043c\u0438 \u0434\u043b\u044f \u0440\u0430\u0432\u043d\u043e\u043c\u0435\u0440\u043d\u043e\u0433\u043e \u043f\u0440\u0438\u0433\u043e\u0442\u043e\u0432\u043b\u0435\u043d\u0438\u044f."),
            _step(2, "\u0420\u0430\u0437\u043e\u0433\u0440\u0435\u0439\u0442\u0435 \u0441\u043a\u043e\u0432\u043e\u0440\u043e\u0434\u0443 \u0441 \u043c\u0430\u0441\u043b\u043e\u043c \u0438 \u043e\u0431\u0436\u0430\u0440\u044c\u0442\u0435 \u043a\u0443\u0440\u0438\u0446\u0443 \u0434\u043e \u0437\u043e\u043b\u043e\u0442\u0438\u0441\u0442\u043e\u0439 \u043a\u043e\u0440\u043e\u0447\u043a\u0438."),
            _step(3, "\u0414\u043e\u0431\u0430\u0432\u044c\u0442\u0435 \u043e\u0432\u043e\u0449\u0438, \u043f\u0435\u0440\u0435\u043c\u0435\u0448\u0430\u0439\u0442\u0435 \u0438 \u0442\u0443\u0448\u0438\u0442\u0435 \u043f\u043e\u0434 \u043a\u0440\u044b\u0448\u043a\u043e\u0439 \u0434\u0432\u0430\u0434\u0446\u0430\u0442\u044c \u043c\u0438\u043d\u0443\u0442."),
            _step(4, "\u041f\u0435\u0440\u0435\u0434 \u043f\u043e\u0434\u0430\u0447\u0435\u0439 \u0434\u0430\u0439\u0442\u0435 \u0431\u043b\u044e\u0434\u0443 \u043d\u0430\u0441\u0442\u043e\u044f\u0442\u044c\u0441\u044f \u0438 \u043f\u043e\u0441\u044b\u043f\u044c\u0442\u0435 \u0437\u0435\u043b\u0435\u043d\u044c\u044e."),
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
            "dish_visual_summary": "\u041a\u0443\u0440\u0438\u043d\u043e\u0435 \u0440\u0430\u0433\u0443",
            "serving_style": "PLANAM",
            "avoid_visuals": ["\u0442\u0435\u043a\u0441\u0442"],
        },
        "quality": {"score": 99, "flags": [], "warnings": []},
    }
    base.update(overrides)
    return base


def test_load_jsonl_valid(tmp_path):
    p = tmp_path / "in.jsonl"
    p.write_text(json.dumps(_valid_recipe(), ensure_ascii=False) + "\n", encoding="utf-8")
    rows = load_gold_v3_jsonl(p)
    assert len(rows) == 1
    assert rows[0]["line"] == 1


def test_invalid_jsonl_fails(tmp_path):
    p = tmp_path / "bad.jsonl"
    p.write_text("{not json\n", encoding="utf-8")
    with pytest.raises(ValueError, match="invalid JSON"):
        load_gold_v3_jsonl(p)


def test_normalize_title_works():
    assert normalize_recipe_title("  \u0421\u0423\u041f!!!  ") == "\u0441\u0443\u043f"
    assert normalize_recipe_title("\u0451\u0436\u0438\u043a") == normalize_recipe_title("\u0435\u0436\u0438\u043a")


def test_map_required_fields():
    payload = map_gold_v3_to_db_payload(_valid_recipe())
    assert payload["title"]
    assert payload["meal_type"] == "dinner"
    assert payload["category"] == "main"
    assert payload["source_type"] == "import"
    assert payload["schema_version"] == "recipe_gold_v3"
    assert len(payload["ingredient_rows_plan"]) == 4


def test_map_nutrition_fields():
    payload = map_gold_v3_to_db_payload(_valid_recipe())
    assert payload["calories_per_serving"] == 410.0
    assert payload["protein_g"] == 30.0
    assert payload["nutrition_kcal_per_serving"] == 410.0
    assert payload["nutrition_protein_per_serving"] == 30.0
    assert payload["nutrition_coverage_json"]["salt_g"] == 1.2
    assert not payload["_missing_nutrition_keys"]


def test_map_ingredients_fields():
    payload = map_gold_v3_to_db_payload(_valid_recipe())
    row = payload["ingredient_rows_plan"][0]
    assert row["shopping_name"]
    assert row["amount"]
    assert row["unit"] == "\u0433"
    assert not payload["_ingredient_issues"]


def test_missing_shopping_name_caught_before_postprocess():
    from app.recipes.recipe_gold_v3_importer import _map_ingredient

    ing = {
        "name": "\u043a\u0430\u0440\u0442\u043e\u0444\u0435\u043b\u044c",
        "amount": 100,
        "unit": "\u0433",
        "display_amount": "100 \u0433",
        "category": "\u043e\u0432\u043e\u0449\u0438",
        "optional": False,
        "shopping_name": "",
    }
    _, issues = _map_ingredient(ing, 0)
    assert any(i["code"] == "missing_shopping_name" for i in issues)


def test_postprocess_autofills_shopping_name_in_map():
    recipe = _valid_recipe(
        ingredients=[
            {
                "name": "\u043a\u0430\u0440\u0442\u043e\u0444\u0435\u043b\u044c",
                "amount": 100,
                "unit": "\u0433",
                "display_amount": "100 \u0433",
                "category": "\u043e\u0432\u043e\u0449\u0438",
                "optional": False,
                "shopping_name": "",
            },
            _ing("\u043c\u043e\u0440\u043a\u043e\u0432\u044c"),
            _ing("\u043b\u0443\u043a \u0440\u0435\u043f\u0447\u0430\u0442\u044b\u0439"),
            _ing("\u043f\u0435\u0440\u0435\u0446"),
        ]
    )
    payload = map_gold_v3_to_db_payload(recipe)
    assert payload["ingredient_rows_plan"][0]["shopping_name"] == "\u043a\u0430\u0440\u0442\u043e\u0444\u0435\u043b\u044c"


def test_duplicate_title_in_batch_fails():
    a = _valid_recipe(title="\u0421\u0443\u043f \u043b\u0435\u0442\u043d\u0438\u0439")
    b = _valid_recipe(title="\u0421\u0443\u043f \u043b\u0435\u0442\u043d\u0438\u0439!")
    result = plan_import_gold_v3_batch([a, b], dry_run=True, quality_gate_ok=True)
    assert result["errors_by_code"].get("duplicate_title_in_batch", 0) > 0
    assert result["ok"] is False


def test_dry_run_cannot_write_db():
    with pytest.raises(RuntimeError, match="db_write_attempted"):
        plan_import_gold_v3_batch([_valid_recipe()], dry_run=False)


def test_detect_duplicates_without_session():
    payloads = [
        map_gold_v3_to_db_payload(_valid_recipe(title="A")),
        map_gold_v3_to_db_payload(_valid_recipe(title="B")),
    ]
    dupes = detect_existing_duplicates(None, payloads)
    assert dupes["db_check_available"] is False


def test_stage_f1_fixture_dry_run_pass():
    result = plan_import_gold_v3_batch([_valid_recipe()], dry_run=True, quality_gate_ok=True)
    assert result["ok"] is True
    assert result["would_create"] == 1
    assert result["would_skip"] == 0


def test_ui_nutrition_alias_mapping():
    summary = get_mapping_summary()
    assert "calories_per_serving" in summary["legacy_nutrition_keys"]
    assert "salt_g" in summary["nutrition_aliases"]


def test_cli_refuses_non_dry_run_without_allow_write(tmp_path):
    inp = tmp_path / "in.jsonl"
    report = tmp_path / "report.md"
    quality = tmp_path / "quality.md"
    quality.write_text("Quality gate: **`PASS`**\n", encoding="utf-8")
    inp.write_text(json.dumps(_valid_recipe(), ensure_ascii=False) + "\n", encoding="utf-8")
    proc = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "--input",
            str(inp),
            "--quality-report",
            str(quality),
            "--report",
            str(report),
            "--no-dry-run",
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 1


def test_cli_writes_report(tmp_path):
    inp = tmp_path / "in.jsonl"
    report = tmp_path / "report.md"
    quality = tmp_path / "quality.md"
    quality.write_text("Quality gate: **`PASS`**\n", encoding="utf-8")
    inp.write_text(json.dumps(_valid_recipe(), ensure_ascii=False) + "\n", encoding="utf-8")
    proc = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "--input",
            str(inp),
            "--quality-report",
            str(quality),
            "--report",
            str(report),
            "--dry-run",
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    text = report.read_text(encoding="utf-8")
    assert "Importer Dry-Run Report" in text
    assert "PASS" in text


def test_cli_fails_if_quality_report_not_pass(tmp_path):
    inp = tmp_path / "in.jsonl"
    report = tmp_path / "report.md"
    quality = tmp_path / "quality.md"
    quality.write_text("Quality gate: **`FAIL`**\n", encoding="utf-8")
    inp.write_text(json.dumps(_valid_recipe(), ensure_ascii=False) + "\n", encoding="utf-8")
    proc = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "--input",
            str(inp),
            "--quality-report",
            str(quality),
            "--report",
            str(report),
            "--dry-run",
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 1


def test_cli_passes_with_quality_report_pass(tmp_path):
    inp = tmp_path / "in.jsonl"
    report = tmp_path / "report.md"
    quality = tmp_path / "quality.md"
    quality.write_text("Quality gate: **`PASS`**\n", encoding="utf-8")
    inp.write_text(json.dumps(_valid_recipe(), ensure_ascii=False) + "\n", encoding="utf-8")
    proc = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "--input",
            str(inp),
            "--quality-report",
            str(quality),
            "--report",
            str(report),
            "--dry-run",
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0
