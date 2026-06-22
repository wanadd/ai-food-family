from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

from psycopg2.extensions import adapt
from psycopg2.extras import Json


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
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
        }
        for recipe_id in EXPECTED_IDS
    ]
    return {
        "recipe_ids": EXPECTED_IDS,
        "recipes": recipes,
        "recipe_ingredients": [{"id": i, "recipe_id": rid, "name": "Ingredient"} for i, rid in enumerate(EXPECTED_IDS, 1)],
        "recipe_steps": [{"id": i, "recipe_id": rid, "step_number": 1, "text": "Step"} for i, rid in enumerate(EXPECTED_IDS, 1)],
        "relation_tables": {},
        "relation_rows": {},
    }


def _create_backup(tmp_path: Path) -> Path:
    create = _load_script("create_gold_v3_upgrade_backup_artifacts")
    return create.create_backup(_fixture_data(), tmp_path)


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
            "diet_tags": ["vegetarian"],
            "tags": ["gold_v3_candidate"],
            "ingredients": [
                {"name": "A", "display_name": "A", "display_amount": "1 шт", "amount": 1, "unit": "шт"},
                {"name": "B", "display_name": "B", "display_amount": "2 г", "amount": 2, "unit": "г"},
                {"name": "C", "display_name": "C", "display_amount": "3 мл", "amount": 3, "unit": "мл"},
            ],
            "steps": [{"step_number": 1, "text": "One"}, {"step_number": 2, "text": "Two"}, {"step_number": 3, "text": "Three"}],
            "nutrition_per_serving": {"kcal": 300, "protein_g": 20, "fat_g": 10, "carbs_g": 30, "fiber_g": 3},
        }
        for index, recipe_id in enumerate(EXPECTED_IDS, start=1)
    ]


def _db_state(*, drift: bool = False) -> dict:
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
            "relation_check_available": True,
            "relation_policy": "preserve_untouched",
            "recipe_explanations_preserve_only": True,
            "recipe_explanations_hits": 0,
            "favorite_hits": False,
            "history_hits": False,
            "menu_or_planned_meal_hits": False,
            "shopping_hits": False,
        },
    }


def _report(tmp_path: Path, *, drift: bool = False, backup_path: Path | None = None) -> dict:
    mod = _load_script("apply_gold_v3_controlled_recipe_upgrades")
    return mod.build_report(
        backup_path=backup_path or _create_backup(tmp_path),
        db_state=_db_state(drift=drift),
        candidates=_candidates(),
        write_reports=False,
    )


def test_apply_write_payload_with_nested_dict_serializes_safely():
    mod = _load_script("apply_gold_v3_controlled_recipe_upgrades")
    payload = mod.serialize_payload_for_table(
        "recipes",
        {"nutrition_coverage_json": {"fiber_g": 3, "salt_g": None}, "title": "Title"},
    )
    assert isinstance(payload["nutrition_coverage_json"], Json)
    assert adapt(payload["nutrition_coverage_json"]).getquoted()
    assert payload["title"] == "Title"


def test_apply_write_payload_with_list_tags_serializes_safely():
    mod = _load_script("apply_gold_v3_controlled_recipe_upgrades")
    payload = mod.serialize_payload_for_table("recipes", {"tags": ["gold_v3"], "diets": ["vegetarian"]})
    assert isinstance(payload["tags"], Json)
    assert isinstance(payload["diets"], Json)
    assert adapt(payload["tags"]).getquoted()


def test_execute_update_sends_jsonb_wrapped_params():
    mod = _load_script("apply_gold_v3_controlled_recipe_upgrades")

    class FakeConn:
        params = None

        def execute(self, _statement, params):
            self.params = params

    conn = FakeConn()
    mod.execute_update(
        conn,
        lambda sql: sql,
        "recipes",
        {"tags": ["gold_v3"], "nutrition_coverage_json": {"fiber_g": 3}, "title": "Title"},
        "id",
        2,
    )
    assert isinstance(conn.params["tags"], Json)
    assert isinstance(conn.params["nutrition_coverage_json"], Json)
    assert conn.params["title"] == "Title"


def test_transaction_rolls_back_on_injected_failure_after_serialization(tmp_path, monkeypatch):
    mod = _load_script("apply_gold_v3_controlled_recipe_upgrades")
    clean = _report(tmp_path)
    clean["safety_guards"]["guard_blockers"] = []
    clean["confirm_plan_id"] = clean["plan_id"]

    class FakeBegin:
        exited_with_error = False

        def __enter__(self):
            return object()

        def __exit__(self, exc_type, _exc, _tb):
            self.exited_with_error = exc_type is not None
            return False

    begin = FakeBegin()

    class FakeEngine:
        def begin(self):
            return begin

    monkeypatch.setattr(mod, "build_report", lambda **_kwargs: clean)
    monkeypatch.setattr(mod, "inspect_db_state", lambda *_args, **_kwargs: _db_state())
    monkeypatch.setattr(mod, "apply_transaction", lambda **_kwargs: (_ for _ in ()).throw(RuntimeError("injected failure")))
    monkeypatch.setattr(mod, "verify_post_apply", lambda *_args, **_kwargs: {"ok": True})
    monkeypatch.setattr(mod, "write_report", lambda *_args, **_kwargs: None)

    import sqlalchemy

    monkeypatch.setattr(sqlalchemy, "create_engine", lambda *_args, **_kwargs: FakeEngine())
    monkeypatch.setattr(sqlalchemy, "inspect", lambda _conn: object())
    result = mod.execute_apply(backup_path=_create_backup(tmp_path), confirm_plan_id=clean["plan_id"], candidates=_candidates())
    assert result["apply_executed"] is False
    assert result["db_writes"] == 0
    assert result["apply_failed"] is True
    assert begin.exited_with_error is True


def test_dry_run_still_has_no_writes(tmp_path):
    report = _report(tmp_path)
    assert report["apply_executed"] is False
    assert report["db_writes"] == 0


def test_guard_behavior_unchanged(tmp_path):
    report = _report(tmp_path, drift=True)
    blockers = report["safety_guards"]["guard_blockers"]
    assert "drift_detected" in blockers
    assert "confirm_plan_id_missing" in blockers
    assert "apply_env_var_missing" in blockers
    assert report["operation_card_count"] == 30
    assert report["import_new_recipe"] == 0
    assert report["simulated_insert_ids"] == []


def test_plan_id_remains_deterministic_for_same_input(tmp_path):
    backup_path = _create_backup(tmp_path)
    left = _report(tmp_path, backup_path=backup_path)
    right = _report(tmp_path, backup_path=backup_path)
    assert left["plan_id"] == right["plan_id"]


def test_no_str_dict_output_is_persisted_in_json_fields():
    mod = _load_script("apply_gold_v3_controlled_recipe_upgrades")
    payload = mod.serialize_payload_for_table("recipes", {"nutrition_coverage_json": {"fiber_g": 3}})
    quoted = adapt(payload["nutrition_coverage_json"]).getquoted().decode("utf-8")
    assert "{'fiber_g': 3}" not in quoted
    assert '"fiber_g"' in quoted
