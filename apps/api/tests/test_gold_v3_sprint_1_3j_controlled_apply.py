from __future__ import annotations

import importlib.util
import json
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
            "hero_image_url": f"/recipe-images/{recipe_id}/hero.webp",
            "image_url": f"/recipe-images/{recipe_id}/card_800.webp",
            "thumbnail_url": f"/recipe-images/{recipe_id}/thumb_400.webp",
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
            }
        },
        "relation_rows": {"recipe_explanations": [{"id": 1, "recipe_id": 2, "explanation": "safe"}]},
    }


def _create_backup(tmp_path: Path) -> Path:
    create = _load_script("create_gold_v3_upgrade_backup_artifacts")
    return create.create_backup(_fixture_data(), tmp_path)


def test_create_backup_allocates_unique_directory_for_rapid_calls(tmp_path):
    first = _create_backup(tmp_path)
    second = _create_backup(tmp_path)

    assert first != second
    assert first.exists()
    assert second.exists()


def _candidates() -> list[dict]:
    return [
        {
            "candidate_index": index,
            "title": f"Gold Recipe {recipe_id}",
            "display_title": f"Gold Recipe {recipe_id}",
            "normalized_title": f"gold recipe {recipe_id}",
            "description": "",
            "meal_type": "dinner",
            "category": "main",
            "difficulty": "easy",
            "servings": 2,
            "cook_time_minutes": 20,
            "prep_time_minutes": 5,
            "diet_tags": [],
            "tags": ["gold_v3_candidate"],
            "ingredients": [
                {"name": "A", "display_name": "A", "amount": 1, "unit": "шт", "shopping_category_slug": "other"},
                {"name": "B", "display_name": "B", "amount": 2, "unit": "г", "shopping_category_slug": "other"},
                {"name": "C", "display_name": "C", "amount": 3, "unit": "мл", "shopping_category_slug": "other"},
            ],
            "steps": [{"step_number": 1, "text": "One"}, {"step_number": 2, "text": "Two"}, {"step_number": 3, "text": "Three"}],
            "nutrition_per_serving": {"kcal": 300, "protein_g": 20, "fat_g": 10, "carbs_g": 30, "fiber_g": 3},
        }
        for index, recipe_id in enumerate(EXPECTED_IDS, start=1)
    ]


def _db_state(*, drift: bool = False, relation_ok: bool = True) -> dict:
    recipes_by_id = {}
    for recipe_id in EXPECTED_IDS:
        title = f"Recipe {recipe_id}"
        if drift and recipe_id == 2:
            title = "Changed Recipe"
        recipes_by_id[recipe_id] = {
            "id": recipe_id,
            "title": title,
            "display_title": f"Recipe {recipe_id}",
            "normalized_title": f"recipe {recipe_id}",
            "meal_type": "dinner",
            "category": "main",
            "source_type": "legacy",
            "has_images": True,
            "hero_image_url": f"/recipe-images/{recipe_id}/hero.webp",
            "image_url": f"/recipe-images/{recipe_id}/card_800.webp",
            "thumbnail_url": f"/recipe-images/{recipe_id}/thumb_400.webp",
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
        "relation_safety": {
            "relation_check_available": relation_ok,
            "relation_tables": {"recipe_explanations": {"rows": 1, "policy": "preserve_untouched"}},
            "recipe_explanations_preserve_only": relation_ok,
            "recipe_explanations_hits": 1,
            "favorite_hits": False,
            "history_hits": False,
            "menu_or_planned_meal_hits": True,
            "shopping_hits": False,
            "relation_policy": "preserve_untouched" if relation_ok else "unknown",
        },
    }


def _report(tmp_path: Path, **kwargs):
    mod = _load_script("apply_gold_v3_controlled_recipe_upgrades")
    backup_path = kwargs.pop("backup_path", None)
    if backup_path is None:
        backup_path = _create_backup(tmp_path)
    return mod.build_report(
        backup_path=backup_path,
        db_state=kwargs.pop("db_state", _db_state()),
        candidates=kwargs.pop("candidates", _candidates()),
        env=kwargs.pop("env", {}),
        write_reports=False,
        **kwargs,
    )


def test_default_mode_is_dry_run():
    mod = _load_script("apply_gold_v3_controlled_recipe_upgrades")
    args = mod.parse_args([])
    assert args.apply is False


def test_apply_without_backup_path_is_refused():
    mod = _load_script("apply_gold_v3_controlled_recipe_upgrades")
    assert mod.main(["--apply"]) == 2


def test_apply_without_env_var_is_refused(tmp_path):
    report = _report(tmp_path)
    assert "apply_env_var_missing" in report["safety_guards"]["guard_blockers"]


def test_apply_without_confirm_plan_id_is_refused(tmp_path):
    report = _report(tmp_path, env={"PLANAM_ALLOW_GOLD_V3_UPGRADE_APPLY": "YES"})
    assert "confirm_plan_id_missing" in report["safety_guards"]["guard_blockers"]


def test_apply_with_wrong_confirm_plan_id_is_refused(tmp_path):
    report = _report(
        tmp_path,
        confirm_plan_id="wrong",
        env={"PLANAM_ALLOW_GOLD_V3_UPGRADE_APPLY": "YES"},
    )
    assert "confirm_plan_id_mismatch" in report["safety_guards"]["guard_blockers"]


def test_dry_run_produces_plan_id(tmp_path):
    assert _report(tmp_path)["plan_id"].startswith("gold-v3-upgrade-")


def test_dry_run_produces_30_operation_cards(tmp_path):
    assert _report(tmp_path)["operation_card_count"] == 30


def test_planned_ids_match_expected_set(tmp_path):
    assert _report(tmp_path)["planned_recipe_ids"] == EXPECTED_IDS


def test_no_import_new_recipe(tmp_path):
    assert _report(tmp_path)["import_new_recipe"] == 0


def test_no_simulated_insert_ids(tmp_path):
    assert _report(tmp_path)["simulated_insert_ids"] == []


def test_drift_blocks_apply(tmp_path):
    report = _report(tmp_path, db_state=_db_state(drift=True))
    assert "drift_detected" in report["safety_guards"]["guard_blockers"]


def test_backup_missing_blocks_apply(tmp_path):
    report = _report(tmp_path, backup_path=tmp_path / "missing")
    assert "backup_missing" in report["safety_guards"]["guard_blockers"]


def test_rollback_manifest_missing_blocks_apply(tmp_path):
    backup_dir = _create_backup(tmp_path)
    (backup_dir / "rollback_manifest.json").unlink()
    report = _report(tmp_path, backup_path=backup_dir)
    assert "rollback_manifest_missing" in report["safety_guards"]["guard_blockers"]


def test_relation_safety_failure_blocks_apply(tmp_path):
    report = _report(tmp_path, db_state=_db_state(relation_ok=False))
    assert "relation_safety_failed" in report["safety_guards"]["guard_blockers"]


def test_dry_run_has_db_writes_zero(tmp_path):
    assert _report(tmp_path)["db_writes"] == 0


def test_apply_code_is_transactional_in_mocks(tmp_path):
    mod = _load_script("apply_gold_v3_controlled_recipe_upgrades")

    class FakeInspector:
        def get_columns(self, table_name):
            columns = {
                "recipes": [
                    "title",
                    "display_title",
                    "normalized_title",
                    "description",
                    "meal_type",
                    "category",
                    "difficulty",
                    "cooking_time_minutes",
                    "prep_time_minutes",
                    "servings",
                    "calories_per_serving",
                    "protein_g",
                    "fat_g",
                    "carbs_g",
                    "fiber_g",
                    "source_type",
                    "source_url",
                    "is_active",
                    "diets",
                    "tags",
                    "ingredients",
                    "steps",
                    "hero_image_url",
                    "image_url",
                    "thumbnail_url",
                ],
                "recipe_ingredients": ["recipe_id", "name", "quantity", "unit", "category", "is_optional", "quantity_text"],
                "recipe_steps": ["recipe_id", "step_number", "text"],
            }
            return [{"name": name} for name in columns[table_name]]

    class FakeConn:
        def __init__(self):
            self.statements = []

        def execute(self, statement, params=None):
            self.statements.append((str(statement), params or {}))

    conn = FakeConn()
    controlled = _report(tmp_path)
    result = mod.apply_transaction(
        conn=conn,
        text=lambda sql: sql,
        inspector=FakeInspector(),
        candidates=_candidates(),
        controlled_report=controlled,
    )
    assert any("pg_advisory_xact_lock" in statement for statement, _params in conn.statements)
    assert result["recipes_updated"] == 30
    assert result["recipe_ids_preserved"] == EXPECTED_IDS


def test_recipe_ids_are_preserved(tmp_path):
    assert [card["recipe_id"] for card in _report(tmp_path)["operation_cards"]] == EXPECTED_IDS


def test_image_urls_are_preserve_only():
    mod = _load_script("apply_gold_v3_controlled_recipe_upgrades")
    payload = mod.candidate_payload(_candidates()[0], {"hero_image_url": "/old/hero.webp", "image_url": "/old/card.webp"})
    assert payload["hero_image_url"] == "/old/hero.webp"
    assert payload["image_url"] == "/old/card.webp"


def test_relation_tables_are_preserve_only(tmp_path):
    report = _report(tmp_path)
    assert "recipe_explanations" in report["apply_preview"]["preserve"]
    assert report["relation_safety_passed"] is True


def test_no_source_leakage_in_public_report_metadata(tmp_path):
    blob = json.dumps(_report(tmp_path), ensure_ascii=False).lower()
    for marker in ("source_url", "original_url", "http", "povarenok", "поваренок"):
        assert marker not in blob


def test_result_report_distinguishes_dry_run_from_apply(tmp_path):
    dry = _report(tmp_path)
    apply_report = _report(tmp_path, apply=True)
    assert dry["mode"] == "dry_run"
    assert apply_report["mode"] == "apply"
    assert apply_report["apply_executed"] is False

