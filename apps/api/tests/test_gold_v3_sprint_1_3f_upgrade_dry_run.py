from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
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


def _load_script(name: str):
    path = ROOT / "backend" / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _plan_report() -> dict:
    actions = [
        {
            "candidate_index": index,
            "candidate_title": f"Recipe {recipe_id}",
            "existing_recipe_id": recipe_id,
            "existing_title": f"Recipe {recipe_id}",
            "proposed_action": "upgrade_existing_recipe",
            "no_new_recipe_id": True,
        }
        for index, recipe_id in enumerate(EXPECTED_IDS, start=1)
    ]
    return {
        "action_counts": {
            "upgrade_existing_recipe": 30,
            "manual_review": 0,
            "do_not_upgrade": 0,
            "import_new_recipe": 0,
        },
        "planned_existing_recipe_ids": EXPECTED_IDS,
        "upgrade_actions": actions,
    }


def _db_state(available: bool = True) -> dict:
    if not available:
        return {"db_available": False, "reason": "no db"}
    return {
        "db_available": True,
        "recipes_total": 263,
        "current_max_id": 265,
        "existing_ids_found": EXPECTED_IDS,
        "missing_planned_ids": [],
        "recipes_by_id": {
            recipe_id: {
                "current_title": f"Recipe {recipe_id}",
                "hero_image_url": None,
                "image_url": None,
                "thumbnail_url": None,
                "ingredient_rows_before": 2,
                "step_rows_before": 1,
            }
            for recipe_id in EXPECTED_IDS
        },
        "relation_safety": {
            "relation_check_available": True,
            "tables_checked": ["recipe_ingredients", "recipe_steps"],
            "references_by_recipe_id": {},
            "recipe_favorites_hits": False,
            "recipe_history_hits": False,
            "menu_or_planned_meal_hits": False,
            "shopping_hits": False,
        },
    }


def _report(db_available: bool = True) -> dict:
    mod = _load_script("dry_run_gold_v3_existing_recipe_upgrades")
    return mod.run_dry_run(plan_report=_plan_report(), db_state=_db_state(db_available), write_reports=False)


def test_dry_run_script_refuses_apply():
    mod = _load_script("dry_run_gold_v3_existing_recipe_upgrades")
    assert mod.main(["--apply"]) == 2


def test_dry_run_contains_exactly_30_planned_upgrades():
    assert _report()["planned_upgrades"] == 30


def test_dry_run_has_no_import_new_recipe():
    assert _report()["import_new_recipe"] == 0


def test_dry_run_has_no_new_ids_or_simulated_insert_ids():
    report = _report()
    assert report["no_new_ids"] is True
    assert report["simulated_insert_ids"] == []


def test_all_planned_ids_are_preserved_existing_ids():
    report = _report()
    assert all(card["existing_recipe_id"] in EXPECTED_IDS for card in report["upgrade_cards"])
    assert all("id" in card["preserve"] for card in report["upgrade_cards"])


def test_planned_id_set_equals_expected_set():
    assert _report()["planned_existing_recipe_ids"] == EXPECTED_IDS


def test_no_source_leakage_in_report():
    blob = json.dumps(_report(), ensure_ascii=False).lower()
    for marker in ("source_url", "original_url", "http", "povarenok", "поваренок"):
        assert marker not in blob


def test_image_policy_is_preserve_only_no_generation():
    assert all("no new image generation" in card["image_policy"] for card in _report()["upgrade_cards"])


def test_future_apply_blocked_if_db_unavailable():
    report = _report(db_available=False)
    assert report["db_available"] is False
    assert "db_unavailable" in report["future_apply_blockers"]


def test_future_apply_blocked_if_backup_is_missing():
    report = _report()
    assert report["backup_design"]["future_apply_blocked_without_backup"] is True
    assert "backup_missing" in report["future_apply_blockers"]


def test_dry_run_performs_no_db_writes():
    report = _report()
    assert report["read_only"] is True
    assert report["db_writes"] == 0
    assert report["apply"] is False


def test_report_includes_backup_design():
    assert _report()["backup_design"]["required_backup"]


def test_report_includes_rollback_design():
    assert _report()["rollback_design"]["required_capabilities"]


def test_report_includes_transaction_design():
    report = _report()
    assert report["transaction_design"]["report_only"] is True
    assert report["transaction_design"]["executable_apply_implemented"] is False


def test_count_child_rows_uses_sqlalchemy_text_without_name_error():
    mod = _load_script("dry_run_gold_v3_existing_recipe_upgrades")

    class FakeInspector:
        def get_table_names(self):
            return ["recipe_steps"]

        def get_columns(self, _table_name):
            return [{"name": "recipe_id"}]

    class FakeResult:
        def mappings(self):
            return self

        def all(self):
            return [{"recipe_id": 2, "count": 3}]

    class FakeConn:
        def execute(self, statement, params):
            assert "recipe_steps" in str(statement)
            assert params == {"ids": [2]}
            return FakeResult()

    assert mod.count_child_rows(FakeConn(), FakeInspector(), "recipe_steps", [2]) == {2: 3}
