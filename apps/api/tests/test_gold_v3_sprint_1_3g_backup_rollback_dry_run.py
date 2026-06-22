from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
MANIFEST_SCHEMA = ROOT / "data" / "recipe_v2" / "gold_v3_upgrade_backup_manifest_schema.json"


def _load_script(name: str):
    path = ROOT / "backend" / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _backup_db_state() -> dict:
    return {
        "db_available": True,
        "recipes_total": 263,
        "current_max_id": 265,
        "planned_recipe_ids": list(range(1, 31)),
        "recipe_ids_found": list(range(1, 31)),
        "missing_recipe_ids": [],
        "recipes": {
            "table_exists": True,
            "columns_detected": ["id", "title"],
            "backup_fields": ["id", "title"],
            "row_count": 30,
            "backup_required": True,
        },
        "child_tables": {
            "recipe_ingredients": {
                "table_exists": True,
                "columns_detected": ["recipe_id", "name"],
                "row_count_total": 120,
                "row_count_by_recipe_id": {"2": 5},
                "backup_required": True,
            },
            "recipe_steps": {
                "table_exists": True,
                "columns_detected": ["recipe_id", "text"],
                "row_count_total": 70,
                "row_count_by_recipe_id": {"2": 3},
                "backup_required": True,
            },
        },
        "relation_tables": {
            "recipe_favorites": {
                "table_exists": True,
                "recipe_id_column_detected": True,
                "hits_by_recipe_id": {},
                "backup_required": False,
                "mutation_policy": "preserve untouched; no delete; no update",
            }
        },
    }


def test_backup_dry_run_refuses_apply():
    mod = _load_script("dry_run_gold_v3_upgrade_backup")
    assert mod.main(["--apply"]) == 2


def test_rollback_dry_run_refuses_apply():
    mod = _load_script("dry_run_gold_v3_upgrade_rollback")
    assert mod.main(["--apply"]) == 2


def test_backup_dry_run_includes_exactly_30_planned_recipe_ids():
    mod = _load_script("dry_run_gold_v3_upgrade_backup")
    report = mod.build_report(db_state=_backup_db_state(), write_reports=False)
    assert report["planned_recipe_id_count"] == 30


def test_backup_dry_run_includes_core_tables():
    mod = _load_script("dry_run_gold_v3_upgrade_backup")
    report = mod.build_report(db_state=_backup_db_state(), write_reports=False)
    assert report["db"]["recipes"]["backup_required"] is True
    assert report["db"]["child_tables"]["recipe_ingredients"]["backup_required"] is True
    assert report["db"]["child_tables"]["recipe_steps"]["backup_required"] is True


def test_backup_dry_run_includes_relation_safety_section():
    mod = _load_script("dry_run_gold_v3_upgrade_backup")
    report = mod.build_report(db_state=_backup_db_state(), write_reports=False)
    assert "recipe_favorites" in report["db"]["relation_tables"]
    assert report["db"]["relation_tables"]["recipe_favorites"]["mutation_policy"] == "preserve untouched; no delete; no update"


def test_backup_manifest_schema_contains_no_real_prod_data():
    data = json.loads(MANIFEST_SCHEMA.read_text(encoding="utf-8"))
    assert data["recipe_ids"] == []
    assert data["tables"]["recipes"]["row_count"] == 0
    assert data["relation_tables"] == {}
    assert data["image_files"] == {}


def test_backup_manifest_schema_requires_rollback_manifest():
    data = json.loads(MANIFEST_SCHEMA.read_text(encoding="utf-8"))
    assert data["rollback_manifest"]["required"] is True
    assert data["rollback_manifest"]["format"] == "json"


def test_backup_dry_run_does_not_create_real_backup_artifacts():
    mod = _load_script("dry_run_gold_v3_upgrade_backup")
    report = mod.build_report(db_state=_backup_db_state(), write_reports=False)
    assert report["backup_path_design"]["created_in_this_sprint"] is False


def test_rollback_dry_run_includes_restore_recipe_fields_by_id():
    mod = _load_script("dry_run_gold_v3_upgrade_rollback")
    report = mod.build_report(db_state={"db_available": True, "relation_check_available": True}, write_reports=False)
    assert "restore recipes fields by ID" in report["planned_rollback_operations"]


def test_rollback_dry_run_includes_replace_ingredient_rows_back():
    mod = _load_script("dry_run_gold_v3_upgrade_rollback")
    report = mod.build_report(db_state={"db_available": True, "relation_check_available": True}, write_reports=False)
    assert "delete current ingredient rows for planned IDs" in report["planned_rollback_operations"]
    assert "restore old ingredient rows" in report["planned_rollback_operations"]


def test_rollback_dry_run_includes_replace_step_rows_back():
    mod = _load_script("dry_run_gold_v3_upgrade_rollback")
    report = mod.build_report(db_state={"db_available": True, "relation_check_available": True}, write_reports=False)
    assert "delete current step rows for planned IDs" in report["planned_rollback_operations"]
    assert "restore old step rows" in report["planned_rollback_operations"]


def test_rollback_dry_run_preserves_relation_tables_untouched():
    mod = _load_script("dry_run_gold_v3_upgrade_rollback")
    report = mod.build_report(db_state={"db_available": True, "relation_check_available": True}, write_reports=False)
    assert "preserve relation tables untouched" in report["planned_rollback_operations"]


def test_rollback_dry_run_blocks_when_backup_is_missing():
    mod = _load_script("dry_run_gold_v3_upgrade_rollback")
    report = mod.build_report(db_state={"db_available": True, "relation_check_available": True}, write_reports=False)
    assert report["backup_missing"] is True
    assert "backup_missing" in report["blockers"]


def test_no_source_leakage_in_backup_and_rollback_reports():
    backup = _load_script("dry_run_gold_v3_upgrade_backup")
    rollback = _load_script("dry_run_gold_v3_upgrade_rollback")
    blob = json.dumps(
        {
            "backup": backup.build_report(db_state=_backup_db_state(), write_reports=False),
            "rollback": rollback.build_report(db_state={"db_available": True, "relation_check_available": True}, write_reports=False),
        },
        ensure_ascii=False,
    ).lower()
    for marker in ("source_url", "original_url", "http", "povarenok", "поваренок"):
        assert marker not in blob


def test_backup_report_sanitizes_source_columns():
    backup = _load_script("dry_run_gold_v3_upgrade_backup")
    assert backup.public_columns(["id", "title", "source_url", "original_url"]) == ["id", "title"]


def test_scripts_are_read_only_and_perform_no_db_writes():
    backup = _load_script("dry_run_gold_v3_upgrade_backup")
    rollback = _load_script("dry_run_gold_v3_upgrade_rollback")
    backup_report = backup.build_report(db_state=_backup_db_state(), write_reports=False)
    rollback_report = rollback.build_report(db_state={"db_available": True, "relation_check_available": True}, write_reports=False)
    assert backup_report["read_only"] is True
    assert backup_report["db_writes"] == 0
    assert rollback_report["read_only"] is True
    assert rollback_report["db_writes"] == 0
