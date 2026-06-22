from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
EXPECTED_IDS = [2, 227, 228, 229, 230, 231, 232, 233, 234, 235, 236, 237, 238, 239, 240, 241, 242, 243, 244, 245, 246, 247, 248, 249, 250, 251, 252, 253, 254, 255]


def _load_script(name: str):
    path = ROOT / "backend" / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _fixture_data() -> dict:
    recipes = [
        {
            "id": recipe_id,
            "title": f"Recipe {recipe_id}",
            "display_title": f"Recipe {recipe_id}",
            "normalized_title": f"recipe {recipe_id}",
            "description": "",
            "source_type": "legacy",
            "meal_type": "dinner",
            "category": "main",
            "tags": [],
            "calories_per_serving": 300,
            "protein_g": 20,
            "fat_g": 10,
            "carbs_g": 30,
            "hero_image_url": None,
            "image_url": None,
            "thumbnail_url": None,
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
        }
        for recipe_id in EXPECTED_IDS
    ]
    ingredients = [
        {"id": index, "recipe_id": recipe_id, "name": "Ingredient", "amount": 1, "unit": "шт"}
        for index, recipe_id in enumerate(EXPECTED_IDS, start=1)
    ]
    steps = [
        {"id": index, "recipe_id": recipe_id, "step_number": 1, "text": "Step"}
        for index, recipe_id in enumerate(EXPECTED_IDS, start=1)
    ]
    return {
        "recipe_ids": EXPECTED_IDS,
        "recipes": recipes,
        "recipe_ingredients": ingredients,
        "recipe_steps": steps,
        "relation_tables": {
            "recipe_explanations": {
                "exists": True,
                "recipe_id_column": True,
                "rows": 1,
                "policy": "preserve_only_no_delete_no_update",
                "backup_required": True,
            },
            "recipe_favorites": {
                "exists": True,
                "recipe_id_column": True,
                "rows": 0,
                "policy": "preserve_only_no_delete_no_update",
                "backup_required": False,
            },
        },
        "relation_rows": {"recipe_explanations": [{"id": 1, "recipe_id": 2, "explanation": "safe"}]},
    }


def _create_backup(tmp_path: Path) -> Path:
    mod = _load_script("create_gold_v3_upgrade_backup_artifacts")
    return mod.create_backup(_fixture_data(), tmp_path)


def test_backup_artifact_script_defaults_to_dry_run():
    mod = _load_script("create_gold_v3_upgrade_backup_artifacts")
    args = mod.parse_args([])
    assert args.create_backup is False


def test_backup_artifact_script_refuses_apply():
    mod = _load_script("create_gold_v3_upgrade_backup_artifacts")
    assert mod.main(["--apply"]) == 2


def test_backup_artifact_script_can_create_temp_backup_dir(tmp_path):
    backup_dir = _create_backup(tmp_path)
    assert backup_dir.exists()


def test_manifest_and_rollback_manifest_are_created(tmp_path):
    backup_dir = _create_backup(tmp_path)
    assert (backup_dir / "manifest.json").exists()
    assert (backup_dir / "rollback_manifest.json").exists()


def test_recipes_jsonl_count_and_planned_ids(tmp_path):
    backup_dir = _create_backup(tmp_path)
    rows = [
        json.loads(line)
        for line in (backup_dir / "recipes.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(rows) == 30
    assert sorted(row["id"] for row in rows) == EXPECTED_IDS


def test_core_backup_files_exist(tmp_path):
    backup_dir = _create_backup(tmp_path)
    assert (backup_dir / "recipe_ingredients.jsonl").exists()
    assert (backup_dir / "recipe_steps.jsonl").exists()
    assert (backup_dir / "relation_tables").exists()


def test_verify_script_passes_on_valid_temp_backup(tmp_path):
    backup_dir = _create_backup(tmp_path)
    mod = _load_script("verify_gold_v3_upgrade_backup_artifacts")
    report = mod.verify(backup_dir, write_reports=False)
    assert report["ok"] is True


def test_verify_script_fails_on_missing_required_files(tmp_path):
    backup_dir = _create_backup(tmp_path)
    (backup_dir / "recipe_steps.jsonl").unlink()
    mod = _load_script("verify_gold_v3_upgrade_backup_artifacts")
    report = mod.verify(backup_dir, write_reports=False)
    assert report["ok"] is False
    assert "recipe_steps.jsonl_missing" in report["blockers"]


def test_rollback_dry_run_with_backup_dir_clears_backup_and_manifest_missing(tmp_path):
    backup_dir = _create_backup(tmp_path)
    mod = _load_script("dry_run_gold_v3_upgrade_rollback")
    report = mod.build_report(
        future_backup_path=backup_dir,
        db_state={"db_available": True, "relation_check_available": True},
        write_reports=False,
    )
    assert report["backup_missing"] is False
    assert report["manifest_missing"] is False


def test_rollback_dry_run_with_backup_dir_writes_1_3h_report_names(tmp_path, monkeypatch):
    backup_dir = _create_backup(tmp_path)
    mod = _load_script("dry_run_gold_v3_upgrade_rollback")
    monkeypatch.setattr(mod, "REPORT_WITH_BACKUP_JSON", tmp_path / "rollback_1_3h.json")
    monkeypatch.setattr(mod, "REPORT_WITH_BACKUP_MD", tmp_path / "rollback_1_3h.md")
    mod.build_report(
        future_backup_path=backup_dir,
        db_state={"db_available": True, "relation_check_available": True},
        write_reports=True,
    )
    assert (tmp_path / "rollback_1_3h.json").exists()
    assert (tmp_path / "rollback_1_3h.md").exists()


def test_rollback_dry_run_remains_no_write(tmp_path):
    backup_dir = _create_backup(tmp_path)
    mod = _load_script("dry_run_gold_v3_upgrade_rollback")
    report = mod.build_report(
        future_backup_path=backup_dir,
        db_state={"db_available": True, "relation_check_available": True},
        write_reports=False,
    )
    assert report["read_only"] is True
    assert report["db_writes"] == 0


def test_upgrade_apply_allowed_false_in_rollback_manifest(tmp_path):
    backup_dir = _create_backup(tmp_path)
    data = json.loads((backup_dir / "rollback_manifest.json").read_text(encoding="utf-8"))
    assert data["upgrade_apply_allowed"] is False


def test_no_reports_or_backups_are_staged_for_commit_in_tests():
    output = subprocess.check_output(["git", "diff", "--cached", "--name-only"], cwd=ROOT, text=True)
    assert "reports/" not in output
    assert "backups/" not in output


def test_no_public_report_metadata_leaks_source_markers(tmp_path):
    create = _load_script("create_gold_v3_upgrade_backup_artifacts")
    verify = _load_script("verify_gold_v3_upgrade_backup_artifacts")
    backup_dir = _create_backup(tmp_path)
    blob = json.dumps(
        {
            "public": create.public_report(_fixture_data(), "dry_run"),
            "verify": verify.verify(backup_dir, write_reports=False),
        },
        ensure_ascii=False,
    ).lower()
    for marker in ("source_url", "original_url", "http", "povarenok", "поваренок"):
        assert marker not in blob
