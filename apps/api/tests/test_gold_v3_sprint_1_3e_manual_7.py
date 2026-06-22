from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
DECISIONS = ROOT / "data" / "recipe_v2" / "gold_v3_manual_review_7_decisions.json"
EXPECTED_IDS = [
    2,
    227,
    228,
    229,
    230,
    231,
    232,
    233,
    234,
    235,
    236,
    237,
    238,
    239,
    240,
    241,
    242,
    243,
    244,
    245,
    246,
    247,
    248,
    249,
    250,
    251,
    252,
    253,
    254,
    255,
]
MANUAL_TITLES = [
    ("Творожная боул с фруктами", 228, "Творожная bowl с фруктами"),
    ("Говядина с брокколи", 242, "High protein: говядина с брокколи"),
    ("Индейка с овощами", 245, "Индейка с овощами без свинины"),
    ("Банан с арахисовой пастой", 251, "Pre-workout: банан с арахисовой пастой"),
    ("Куриная грудка и киноа", 253, "Pro high protein: куриная грудка и киноа"),
    ("Салат с индейкой", 254, "Pro weight loss: салат с индейкой"),
    ("Яйца с авокадо", 255, "Pro small portion: яйца с авокадо"),
]


def _load_script(name: str):
    path = ROOT / "backend" / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _decision_data() -> dict:
    return json.loads(DECISIONS.read_text(encoding="utf-8"))


def _candidate(title: str) -> dict:
    return {
        "title": title,
        "display_title": title,
        "normalized_title": title.lower(),
        "meal_type": "dinner",
        "category": "main",
        "tags": ["gold_v3_candidate"],
        "ingredients": [{"name": "основа"}, {"name": "овощи"}, {"name": "специи"}],
        "steps": [{"text": "Раз."}, {"text": "Два."}, {"text": "Три."}],
        "nutrition_per_serving": {"kcal": 350, "protein_g": 30, "fat_g": 10, "carbs_g": 35},
    }


def _item(index: int, candidate_title: str, db_id: int, db_title: str, decision: str) -> dict:
    return {
        "candidate_index": index,
        "candidate_title": candidate_title,
        "candidate_main_ingredients": ["основа", "овощи", "специи"],
        "candidate_meal_type": "dinner",
        "candidate_category": "main",
        "candidate_tags": ["gold_v3_candidate"],
        "decision": decision,
        "reason": "Same dish exists, but existing DB recipe appears weaker; upgrade is out of scope.",
        "duplicate_matches": [
            {
                "db_id": db_id,
                "db_title": db_title,
                "db_display_title": db_title,
                "db_normalized_title": db_title.lower(),
                "db_source_type": "legacy",
                "db_tags": [],
                "db_meal_type": "dinner",
                "db_category": "main",
                "db_has_images": False,
                "db_ingredient_count": 2,
                "db_step_count": 1,
                "db_nutrition_core_complete": False,
                "match_type": "exact_title" if decision != "manual_review" else "ingredient_overlap",
                "similarity_score": 1.0 if decision != "manual_review" else 0.86,
            }
        ],
    }


def _prod_like_duplicate_report() -> tuple[dict, list[dict]]:
    auto_ids = [recipe_id for recipe_id in EXPECTED_IDS if recipe_id not in {item[1] for item in MANUAL_TITLES}]
    items = []
    candidates = []
    for index, recipe_id in enumerate(auto_ids, start=1):
        title = f"Auto upgrade {recipe_id}"
        items.append(_item(index, title, recipe_id, title, "candidate_for_future_upgrade"))
        candidates.append(_candidate(title))
    for offset, (title, db_id, db_title) in enumerate(MANUAL_TITLES, start=len(auto_ids) + 1):
        items.append(_item(offset, title, db_id, db_title, "manual_review"))
        candidates.append(_candidate(title))
    return {
        "db_available": True,
        "duplicate_risk_count": 30,
        "items": items,
    }, candidates


def test_manual_decision_file_contains_exactly_7_decisions():
    assert len(_decision_data()["decisions"]) == 7


def test_all_manual_decisions_are_upgrade_existing_recipe():
    assert {row["decision"] for row in _decision_data()["decisions"]} == {"upgrade_existing_recipe"}


def test_all_manual_decisions_forbid_new_recipe_import():
    assert all(row["new_recipe_import_allowed"] is False for row in _decision_data()["decisions"])


def test_manual_decision_file_has_no_source_leakage():
    blob = DECISIONS.read_text(encoding="utf-8").lower()
    for marker in ("source_url", "original_url", "http", "povarenok", "поваренок"):
        assert marker not in blob


def test_planner_loads_manual_decision_file():
    mod = _load_script("plan_gold_v3_existing_recipe_upgrades")
    loaded, decisions, source = mod.load_manual_decisions(DECISIONS)
    assert loaded is True
    assert source == "data\\recipe_v2\\gold_v3_manual_review_7_decisions.json" or source == "data/recipe_v2/gold_v3_manual_review_7_decisions.json"
    assert len(decisions) == 7


def test_planner_converts_7_manual_review_cases_to_upgrade_actions():
    mod = _load_script("plan_gold_v3_existing_recipe_upgrades")
    duplicate_report, candidates = _prod_like_duplicate_report()
    report = mod.build_plan(
        duplicate_report,
        candidates,
        manual_decisions_path=DECISIONS,
        relation_snapshot={"relation_check_available": True, "future_apply_requires_pre_apply_backup": True},
        write_reports=False,
    )
    assert report["manual_decisions_loaded"] is True
    assert report["manual_decisions_applied"] == 7
    assert report["unresolved_manual_review"] == 0


def test_final_plan_has_30_upgrades_zero_manual_zero_imports():
    mod = _load_script("plan_gold_v3_existing_recipe_upgrades")
    duplicate_report, candidates = _prod_like_duplicate_report()
    report = mod.build_plan(
        duplicate_report,
        candidates,
        manual_decisions_path=DECISIONS,
        relation_snapshot={"relation_check_available": True, "future_apply_requires_pre_apply_backup": True},
        write_reports=False,
    )
    assert report["action_counts"]["upgrade_existing_recipe"] == 30
    assert report["action_counts"]["manual_review"] == 0
    assert report["action_counts"]["import_new_recipe"] == 0


def test_full_planned_id_set_has_30_existing_ids():
    mod = _load_script("plan_gold_v3_existing_recipe_upgrades")
    duplicate_report, candidates = _prod_like_duplicate_report()
    report = mod.build_plan(
        duplicate_report,
        candidates,
        manual_decisions_path=DECISIONS,
        relation_snapshot={"relation_check_available": True, "future_apply_requires_pre_apply_backup": True},
        write_reports=False,
    )
    assert report["planned_existing_recipe_ids"] == EXPECTED_IDS
    assert all(action["no_new_recipe_id"] is True for action in report["upgrade_actions"])


def test_planner_remains_read_only_and_implements_no_apply():
    mod = _load_script("plan_gold_v3_existing_recipe_upgrades")
    duplicate_report, candidates = _prod_like_duplicate_report()
    report = mod.build_plan(
        duplicate_report,
        candidates,
        manual_decisions_path=DECISIONS,
        relation_snapshot={"relation_check_available": True, "future_apply_requires_pre_apply_backup": True},
        write_reports=False,
    )
    assert report["read_only"] is True
    assert report["db_writes"] == 0
    assert report["future_apply_design"]["executable_apply_implemented"] is False
