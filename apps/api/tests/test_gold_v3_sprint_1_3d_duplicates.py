from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
CANDIDATE = ROOT / "data" / "recipe_v2" / "gold_recipes_30_repaired_candidate.jsonl"


def _load_script(name: str):
    path = ROOT / "backend" / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _recipe(title: str = "Курица с рисом") -> dict:
    return {
        "title": title,
        "display_title": title,
        "normalized_title": title.lower(),
        "meal_type": "dinner",
        "category": "main",
        "tags": ["gold_v3_candidate"],
        "ingredients": [
            {"name": "куриное филе"},
            {"name": "рис"},
            {"name": "морковь"},
            {"name": "оливковое масло"},
        ],
        "steps": [{"text": "Раз."}, {"text": "Два."}, {"text": "Три."}],
        "nutrition_per_serving": {"kcal": 350, "protein_g": 30, "fat_g": 10, "carbs_g": 35},
    }


def _existing(**overrides):
    mod = _load_script("audit_gold_v3_repaired_30_duplicates")
    recipe = mod.ExistingRecipe(
        id=1,
        title="Курица с рисом",
        display_title="Курица с рисом",
        normalized_title="курица с рисом",
        source_type="seed",
        tags=[],
        meal_type="dinner",
        category="main",
        has_images=True,
        ingredient_count=4,
        step_count=3,
        nutrition_core_complete=True,
        ingredient_names=["куриное филе", "рис", "морковь", "оливковое масло"],
    )
    for key, value in overrides.items():
        setattr(recipe, key, value)
    return recipe


def test_exact_title_match_becomes_skip_exact_duplicate():
    mod = _load_script("audit_gold_v3_repaired_30_duplicates")
    report = mod.audit([_recipe()], [_existing()], write_reports=False)
    assert report["items"][0]["decision"] == "skip_exact_duplicate"


def test_exact_normalized_title_match_becomes_skip_exact_duplicate():
    mod = _load_script("audit_gold_v3_repaired_30_duplicates")
    existing = _existing(title="КУРИЦА  С  РИСОМ", normalized_title="курица с рисом")
    report = mod.audit([_recipe("Курица с рисом")], [existing], write_reports=False)
    assert report["items"][0]["decision"] == "skip_exact_duplicate"


def test_same_title_existing_legacy_weaker_becomes_future_upgrade():
    mod = _load_script("audit_gold_v3_repaired_30_duplicates")
    existing = _existing(source_type="legacy", has_images=False, ingredient_count=2, step_count=1, nutrition_core_complete=False)
    report = mod.audit([_recipe()], [existing], write_reports=False)
    assert report["items"][0]["decision"] == "candidate_for_future_upgrade"


def test_similar_title_different_protein_can_be_rename_candidate():
    mod = _load_script("audit_gold_v3_repaired_30_duplicates")
    candidate = _recipe("Индейка с рисом")
    existing = _existing(title="Курица с рисом", normalized_title="курица с рисом")
    report = mod.audit([candidate], [existing], write_reports=False)
    assert report["items"][0]["decision"] == "rename_and_import_candidate"
    assert report["items"][0]["proposed_title"]


def test_no_match_becomes_safe_to_import():
    mod = _load_script("audit_gold_v3_repaired_30_duplicates")
    report = mod.audit([_recipe("Гречка с грибами")], [], write_reports=False)
    assert report["items"][0]["decision"] == "safe_to_import"


def test_ambiguous_similarity_becomes_manual_review():
    mod = _load_script("audit_gold_v3_repaired_30_duplicates")
    candidate = _recipe("Курица с киноа")
    existing = _existing(title="Курица с булгуром", normalized_title="курица с булгуром")
    report = mod.audit([candidate], [existing], write_reports=False)
    assert report["items"][0]["decision"] == "manual_review"


def test_duplicate_resolution_report_includes_all_30_candidates():
    mod = _load_script("audit_gold_v3_repaired_30_duplicates")
    records = mod.load_candidates(CANDIDATE)
    report = mod.audit(records, [], write_reports=False)
    assert report["total_candidates"] == 30
    assert len(report["items"]) == 30
    assert all(item["decision"] in mod.DECISIONS for item in report["items"])


def test_script_is_read_only_and_performs_no_db_writes():
    mod = _load_script("audit_gold_v3_repaired_30_duplicates")
    report = mod.audit([_recipe()], [_existing()], write_reports=False)
    assert report["read_only"] is True
    assert "db_writes" not in report


def test_plan_file_contains_no_source_leakage(tmp_path, monkeypatch):
    mod = _load_script("audit_gold_v3_repaired_30_duplicates")
    monkeypatch.setattr(mod, "PLAN_JSON", tmp_path / "plan.json")
    report = mod.audit([_recipe()], [], write_reports=False)
    report["db_available"] = True
    report["blocked_for_apply"] = False
    mod.maybe_write_plan(report)
    blob = (tmp_path / "plan.json").read_text(encoding="utf-8").lower()
    for marker in ("source_url", "original_url", "http", "povarenok", "поваренок"):
        assert marker not in blob


def test_blocked_report_does_not_write_optional_plan(tmp_path, monkeypatch):
    mod = _load_script("audit_gold_v3_repaired_30_duplicates")
    monkeypatch.setattr(mod, "PLAN_JSON", tmp_path / "plan.json")
    report = mod.audit([_recipe()], [_existing()], write_reports=False)
    report["blocked_for_apply"] = True
    mod.maybe_write_plan(report)
    assert not (tmp_path / "plan.json").exists()
