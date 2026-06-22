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
    create = _load_script("create_gold_v3_upgrade_backup_artifacts")
    return create.create_backup(_fixture_data(), tmp_path)


def _candidates() -> list[dict]:
    records = []
    for index, recipe_id in enumerate(EXPECTED_IDS, start=1):
        records.append(
            {
                "candidate_index": index,
                "title": f"Gold Recipe {recipe_id}",
                "display_title": f"Gold Recipe {recipe_id}",
                "normalized_title": f"gold recipe {recipe_id}",
                "meal_type": "dinner",
                "category": "main",
                "tags": ["gold_v3"],
                "ingredients": [{"name": "A"}, {"name": "B"}, {"name": "C"}],
                "steps": [{"text": "One"}, {"text": "Two"}, {"text": "Three"}],
                "nutrition_per_serving": {"kcal": 300, "protein_g": 20, "fat_g": 10, "carbs_g": 30},
            }
        )
    return records


def _db_state(drift: bool = False) -> dict:
    recipes_by_id = {}
    for recipe_id in EXPECTED_IDS:
        title = f"Recipe {recipe_id}"
        if drift and recipe_id == EXPECTED_IDS[0]:
            title = "Changed Recipe"
        recipes_by_id[recipe_id] = {
            "id": recipe_id,
            "title": title,
            "display_title": f"Recipe {recipe_id}",
            "normalized_title": f"recipe {recipe_id}",
            "meal_type": "dinner",
            "category": "main",
            "source_type": "legacy",
            "has_images": False,
            "ingredient_count": 1,
            "step_count": 1,
        }
    return {
        "db_available": True,
        "recipes_total": 263,
        "current_max_id": 265,
        "planned_recipe_ids": EXPECTED_IDS,
        "recipes_rows_for_planned_ids": 30,
        "existing_ids_found": EXPECTED_IDS,
        "missing_planned_ids": [],
        "recipes_by_id": recipes_by_id,
        "recipe_ingredients_count": 30,
        "recipe_steps_count": 30,
        "ingredient_counts_by_recipe_id": {recipe_id: 1 for recipe_id in EXPECTED_IDS},
        "step_counts_by_recipe_id": {recipe_id: 1 for recipe_id in EXPECTED_IDS},
        "relation_safety": {
            "relation_check_available": True,
            "relation_tables": {
                "recipe_explanations": {"rows": 1, "policy": "preserve_untouched", "backup_required": True},
                "recipe_favorites": {"rows": 0, "policy": "preserve_untouched", "backup_required": False},
            },
            "recipe_explanations_preserve_only": True,
            "recipe_explanations_hits": 1,
            "favorite_hits": False,
            "history_hits": False,
            "menu_or_planned_meal_hits": False,
            "shopping_hits": False,
            "relation_policy": "preserve_untouched",
        },
    }


def _report(tmp_path: Path, *, drift: bool = False) -> dict:
    mod = _load_script("dry_run_gold_v3_controlled_upgrade_apply")
    return mod.build_report(
        backup_path=_create_backup(tmp_path),
        db_state=_db_state(drift=drift),
        candidates=_candidates(),
        write_reports=False,
    )


def test_script_refuses_apply():
    mod = _load_script("dry_run_gold_v3_controlled_upgrade_apply")
    assert mod.main(["--apply"]) == 2


def test_backup_path_is_required_for_db_backed_dry_run():
    mod = _load_script("dry_run_gold_v3_controlled_upgrade_apply")
    report = mod.build_report(backup_path=None, db_state=_db_state(), candidates=_candidates(), write_reports=False)
    assert "backup_path_missing" in report["future_apply_blockers"]


def test_script_reads_manifest_json(tmp_path):
    report = _report(tmp_path)
    assert report["backup"]["manifest_parsed"] is True


def test_script_reads_rollback_manifest_json(tmp_path):
    report = _report(tmp_path)
    assert report["backup"]["rollback_manifest_parsed"] is True


def test_script_verifies_30_recipe_ids(tmp_path):
    report = _report(tmp_path)
    assert report["backup"]["recipe_ids"] == EXPECTED_IDS
    assert report["backup"]["recipe_ids_ok"] is True


def test_script_verifies_backup_recipe_count(tmp_path):
    assert _report(tmp_path)["backup"]["recipes_count"] == 30


def test_script_verifies_ingredient_and_step_backup_counts_are_non_empty(tmp_path):
    report = _report(tmp_path)
    assert report["backup"]["recipe_ingredients_count"] > 0
    assert report["backup"]["recipe_steps_count"] > 0


def test_script_blocks_if_backup_missing(tmp_path):
    mod = _load_script("dry_run_gold_v3_controlled_upgrade_apply")
    missing = tmp_path / "missing"
    report = mod.build_report(backup_path=missing, db_state=_db_state(), candidates=_candidates(), write_reports=False)
    assert "backup_missing" in report["future_apply_blockers"]


def test_script_blocks_if_rollback_manifest_missing(tmp_path):
    backup_dir = _create_backup(tmp_path)
    (backup_dir / "rollback_manifest.json").unlink()
    mod = _load_script("dry_run_gold_v3_controlled_upgrade_apply")
    report = mod.build_report(backup_path=backup_dir, db_state=_db_state(), candidates=_candidates(), write_reports=False)
    assert "rollback_manifest_missing_or_invalid" in report["future_apply_blockers"]


def test_script_blocks_if_drift_detected(tmp_path):
    report = _report(tmp_path, drift=True)
    assert report["drift_detected"] is True
    assert "drift_detected" in report["future_apply_blockers"]


def test_script_produces_exactly_30_operation_cards(tmp_path):
    assert _report(tmp_path)["operation_card_count"] == 30


def test_every_operation_preserves_existing_recipe_id(tmp_path):
    report = _report(tmp_path)
    assert [card["recipe_id"] for card in report["operation_cards"]] == EXPECTED_IDS
    assert all("id" in card["preserve"] for card in report["operation_cards"])


def test_every_operation_has_no_writes_executed_now(tmp_path):
    assert all(card["db_writes_executed_now"] is False for card in _report(tmp_path)["operation_cards"])


def test_import_new_recipe_is_always_zero(tmp_path):
    assert _report(tmp_path)["import_new_recipe"] == 0


def test_no_simulated_insert_ids(tmp_path):
    assert _report(tmp_path)["simulated_insert_ids"] == []


def test_relation_policy_is_preserve_only(tmp_path):
    report = _report(tmp_path)
    assert report["relation_safety"]["relation_policy"] == "preserve_untouched"
    assert all(card["relation_policy"] == "preserve_untouched" for card in report["operation_cards"])


def test_future_apply_gate_exists(tmp_path):
    assert _report(tmp_path)["future_apply_gate"]["allowed_only_if"]


def test_real_apply_available_false(tmp_path):
    assert _report(tmp_path)["real_apply_available"] is False


def test_apply_command_supported_false(tmp_path):
    assert _report(tmp_path)["apply_command_supported"] is False


def test_no_source_leakage_in_public_report_metadata(tmp_path):
    blob = json.dumps(_report(tmp_path), ensure_ascii=False).lower()
    for marker in ("source_url", "original_url", "http", "povarenok", "поваренок"):
        assert marker not in blob

