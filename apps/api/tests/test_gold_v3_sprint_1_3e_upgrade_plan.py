from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


def _load_script(name: str):
    path = ROOT / "backend" / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _candidate(title: str = "Курица с рисом") -> dict:
    return {
        "title": title,
        "display_title": title,
        "normalized_title": title.lower(),
        "meal_type": "dinner",
        "category": "main",
        "tags": ["gold_v3_candidate"],
        "ingredients": [{"name": "курица"}, {"name": "рис"}, {"name": "морковь"}],
        "steps": [{"text": "Раз."}, {"text": "Два."}, {"text": "Три."}],
        "nutrition_per_serving": {"kcal": 350, "protein_g": 30, "fat_g": 10, "carbs_g": 35},
    }


def _duplicate_report(decision: str = "candidate_for_future_upgrade") -> dict:
    return {
        "db_available": True,
        "duplicate_risk_count": 1,
        "items": [
            {
                "candidate_index": 1,
                "candidate_title": "Курица с рисом",
                "candidate_main_ingredients": ["курица", "рис", "морковь"],
                "candidate_meal_type": "dinner",
                "candidate_category": "main",
                "candidate_tags": ["gold_v3_candidate"],
                "decision": decision,
                "reason": "Same dish exists, but existing DB recipe appears weaker; upgrade is out of scope.",
                "duplicate_matches": [
                    {
                        "db_id": 123,
                        "db_title": "Курица с рисом",
                        "db_display_title": "Курица с рисом",
                        "db_normalized_title": "курица с рисом",
                        "db_source_type": "legacy",
                        "db_tags": [],
                        "db_meal_type": "dinner",
                        "db_category": "main",
                        "db_has_images": True,
                        "db_ingredient_count": 2,
                        "db_step_count": 1,
                        "db_nutrition_core_complete": False,
                        "match_type": "exact_title",
                        "similarity_score": 1.0,
                    }
                ],
            }
        ],
    }


def test_upgrade_planner_classifies_exact_same_dish_as_upgrade_existing_recipe():
    mod = _load_script("plan_gold_v3_existing_recipe_upgrades")
    report = mod.build_plan(_duplicate_report(), [_candidate()], write_reports=False)
    assert report["action_counts"]["upgrade_existing_recipe"] == 1
    assert report["upgrade_actions"][0]["proposed_action"] == "upgrade_existing_recipe"


def test_upgrade_plan_preserves_existing_recipe_id():
    mod = _load_script("plan_gold_v3_existing_recipe_upgrades")
    report = mod.build_plan(_duplicate_report(), [_candidate()], write_reports=False)
    assert report["upgrade_actions"][0]["existing_recipe_id"] == 123
    assert "id" in report["upgrade_actions"][0]["fields_to_preserve"]


def test_upgrade_plan_does_not_create_simulated_new_ids():
    mod = _load_script("plan_gold_v3_existing_recipe_upgrades")
    report = mod.build_plan(_duplicate_report(), [_candidate()], write_reports=False)
    assert report["upgrade_actions"][0]["no_new_recipe_id"] is True
    assert "simulated_ids" not in json.dumps(report)


def test_manual_review_candidates_remain_blocked():
    mod = _load_script("plan_gold_v3_existing_recipe_upgrades")
    report = mod.build_plan(_duplicate_report("manual_review"), [_candidate()], write_reports=False)
    assert report["action_counts"]["manual_review"] == 1
    assert report["future_apply_blocked"] is True


def test_plan_contains_no_source_leakage(tmp_path, monkeypatch):
    mod = _load_script("plan_gold_v3_existing_recipe_upgrades")
    monkeypatch.setattr(mod, "PLAN_JSON", tmp_path / "plan.json")
    report = mod.build_plan(_duplicate_report(), [_candidate()], write_reports=False)
    mod.write_commit_safe_plan(report)
    blob = (tmp_path / "plan.json").read_text(encoding="utf-8").lower()
    for marker in ("source_url", "original_url", "http", "povarenok", "поваренок"):
        assert marker not in blob


def test_future_apply_blocked_when_manual_review_exists():
    mod = _load_script("plan_gold_v3_existing_recipe_upgrades")
    report = mod.build_plan(_duplicate_report("manual_review"), [_candidate()], write_reports=False)
    assert "manual_review_remaining" in report["future_apply_blockers"]


def test_relation_safety_section_exists_when_tables_unavailable():
    mod = _load_script("plan_gold_v3_existing_recipe_upgrades")
    relation = {"relation_check_available": False, "reason": "no db", "future_apply_requires_pre_apply_backup": True}
    report = mod.build_plan(_duplicate_report(), [_candidate()], relation_snapshot=relation, write_reports=False)
    assert report["relation_safety"]["relation_check_available"] is False


def test_script_is_read_only_and_performs_no_db_writes():
    mod = _load_script("plan_gold_v3_existing_recipe_upgrades")
    report = mod.build_plan(_duplicate_report(), [_candidate()], write_reports=False)
    assert report["read_only"] is True
    assert report["db_writes"] == 0


def test_future_apply_design_is_report_only_not_executable():
    mod = _load_script("plan_gold_v3_existing_recipe_upgrades")
    report = mod.build_plan(_duplicate_report(), [_candidate()], write_reports=False)
    assert report["future_apply_design"]["report_only"] is True
    assert report["future_apply_design"]["executable_apply_implemented"] is False
