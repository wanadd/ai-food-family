from __future__ import annotations

import copy
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


def _manifest_data() -> dict:
    validator = _load_script("validate_gold_v3_nutrition_correction_manifest")
    return validator.load_manifest(validator.DEFAULT_MANIFEST)


def _write_manifest(tmp_path: Path, data: dict) -> Path:
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _valid_existing(apply_mod) -> dict[int, dict]:
    return {rid: {"id": rid, **{field: None for field in apply_mod.TARGET_FIELDS}} for rid in apply_mod.EXPECTED_IDS}


def _patch_db(monkeypatch, apply_mod, *, missing_fields: set[str] | None = None, existing: dict[int, dict] | None = None):
    class DummyConnect:
        def __enter__(self):
            return object()

        def __exit__(self, *_args):
            return False

    class DummyEngine:
        dialect = type("Dialect", (), {"name": "postgresql"})()

        def connect(self):
            return DummyConnect()

    fields = set(apply_mod.TARGET_FIELDS)
    fields -= missing_fields or set()
    monkeypatch.setattr(apply_mod, "engine_for", lambda *_args, **_kwargs: DummyEngine())
    monkeypatch.setattr(apply_mod, "existing_columns", lambda _engine: fields)
    monkeypatch.setattr(apply_mod, "fetch_existing", lambda _conn, _ids: existing if existing is not None else _valid_existing(apply_mod))


def test_manifest_rejects_missing_id():
    validator = _load_script("validate_gold_v3_nutrition_correction_manifest")
    data = _manifest_data()
    data["recipes"] = [item for item in data["recipes"] if item["recipe_id"] != 265]
    result = validator.validate_manifest(data)
    assert not result["ok"]
    assert "missing_ids:[265]" in result["blockers"]


def test_manifest_rejects_extra_id():
    validator = _load_script("validate_gold_v3_nutrition_correction_manifest")
    data = _manifest_data()
    extra = copy.deepcopy(data["recipes"][0])
    extra["recipe_id"] = 999
    data["recipes"].append(extra)
    result = validator.validate_manifest(data)
    assert not result["ok"]
    assert "extra_ids:[999]" in result["blockers"]


def test_manifest_rejects_duplicate_id():
    validator = _load_script("validate_gold_v3_nutrition_correction_manifest")
    data = _manifest_data()
    data["recipes"].append(copy.deepcopy(data["recipes"][0]))
    result = validator.validate_manifest(data)
    assert not result["ok"]
    assert any(blocker.startswith("duplicate_ids:") for blocker in result["blockers"])


def test_manifest_rejects_zero_kcal():
    validator = _load_script("validate_gold_v3_nutrition_correction_manifest")
    data = _manifest_data()
    data["recipes"][0]["nutrition_per_serving"]["kcal"] = 0
    result = validator.validate_manifest(data)
    assert not result["ok"]
    assert any("kcal_not_positive" in blocker for blocker in result["blockers"])


def test_manifest_rejects_impossible_macro_kcal_mismatch():
    validator = _load_script("validate_gold_v3_nutrition_correction_manifest")
    data = _manifest_data()
    data["recipes"][0]["nutrition_per_serving"]["kcal"] = 900
    result = validator.validate_manifest(data)
    assert not result["ok"]
    assert any("macro_kcal_mismatch" in blocker for blocker in result["blockers"])


def test_manifest_blocks_dry_grain_without_yield_note():
    validator = _load_script("validate_gold_v3_nutrition_correction_manifest")
    data = _manifest_data()
    grain = next(item for item in data["recipes"] if "Гречка" in item["display_title"])
    grain["yield_notes"] = ""
    result = validator.validate_manifest(data)
    assert not result["ok"]
    assert any("dry_grain_without_yield_note" in blocker for blocker in result["blockers"])


def test_apply_script_dry_run_does_not_mutate_db(tmp_path, monkeypatch):
    apply_mod = _load_script("apply_gold_v3_nutrition_corrections")
    _patch_db(monkeypatch, apply_mod)
    called = {"apply": False}
    monkeypatch.setattr(apply_mod, "apply_updates", lambda *_args, **_kwargs: called.update(apply=True))
    report = apply_mod.build_report(apply_mod.DEFAULT_MANIFEST)
    assert report["apply_executed"] is False
    assert report["db_writes"] == 0
    assert called["apply"] is False


def test_apply_script_refuses_apply_without_env_guard(monkeypatch):
    apply_mod = _load_script("apply_gold_v3_nutrition_corrections")
    _patch_db(monkeypatch, apply_mod)
    data = apply_mod.load_manifest(apply_mod.DEFAULT_MANIFEST)
    plan_id = apply_mod.plan_id_for(data)
    monkeypatch.delenv(apply_mod.ENV_GUARD, raising=False)
    report = apply_mod.build_report(apply_mod.DEFAULT_MANIFEST, apply=True, confirm_plan_id=plan_id)
    assert "env_guard_missing" in report["guard_blockers"]
    assert report["apply_executed"] is False


def test_apply_script_refuses_apply_without_confirm_plan_id(monkeypatch):
    apply_mod = _load_script("apply_gold_v3_nutrition_corrections")
    _patch_db(monkeypatch, apply_mod)
    monkeypatch.setenv(apply_mod.ENV_GUARD, "YES")
    report = apply_mod.build_report(apply_mod.DEFAULT_MANIFEST, apply=True)
    assert "confirm_plan_id_mismatch" in report["guard_blockers"]
    assert report["apply_executed"] is False


def test_apply_script_refuses_unknown_db_fields(monkeypatch):
    apply_mod = _load_script("apply_gold_v3_nutrition_corrections")
    _patch_db(monkeypatch, apply_mod, missing_fields={"nutrition_coverage_json"})
    report = apply_mod.build_report(apply_mod.DEFAULT_MANIFEST)
    assert any(blocker.startswith("missing_db_fields:") for blocker in report["guard_blockers"])
    assert "unknown_or_missing_db_fields" in report["unsafe_operations"]


def test_apply_script_updates_only_allowed_nutrition_fields():
    apply_mod = _load_script("apply_gold_v3_nutrition_corrections")
    data = apply_mod.load_manifest(apply_mod.DEFAULT_MANIFEST)
    values = apply_mod.values_for_recipe(data["recipes"][0])
    assert set(values) == set(apply_mod.TARGET_FIELDS)
    forbidden = {"title", "display_title", "description", "ingredients", "steps", "image_url", "tags", "diets"}
    assert set(values).isdisjoint(forbidden)


def test_rollback_manifest_contains_previous_values(tmp_path, monkeypatch):
    apply_mod = _load_script("apply_gold_v3_nutrition_corrections")
    data = apply_mod.load_manifest(apply_mod.DEFAULT_MANIFEST)
    existing = _valid_existing(apply_mod)
    desired = {int(item["recipe_id"]): apply_mod.values_for_recipe(item) for item in data["recipes"]}

    class FakeResult:
        rowcount = 1

    class FakeConn:
        def execute(self, _statement, _params):
            return FakeResult()

    class FakeBegin:
        def __enter__(self):
            return FakeConn()

        def __exit__(self, *_args):
            return False

    class FakeEngine:
        dialect = type("Dialect", (), {"name": "postgresql"})()

        def begin(self):
            return FakeBegin()

    monkeypatch.setattr(apply_mod, "ROOT", tmp_path)
    result = apply_mod.apply_updates(FakeEngine(), data, existing, desired, "plan", apply_mod.TARGET_FIELDS)
    rollback_path = Path(result["rollback_manifest_path"])
    rollback = json.loads(rollback_path.read_text(encoding="utf-8"))
    assert rollback["recipes"][0]["previous"]["calories_per_serving"] is None
    assert rollback["recipes"][0]["new"]["calories_per_serving"] > 0


def test_plan_id_stable_for_same_manifest():
    apply_mod = _load_script("apply_gold_v3_nutrition_corrections")
    data = apply_mod.load_manifest(apply_mod.DEFAULT_MANIFEST)
    assert apply_mod.plan_id_for(data) == apply_mod.plan_id_for(copy.deepcopy(data))


def test_plan_id_changes_if_nutrition_values_change():
    apply_mod = _load_script("apply_gold_v3_nutrition_corrections")
    data = apply_mod.load_manifest(apply_mod.DEFAULT_MANIFEST)
    changed = copy.deepcopy(data)
    changed["recipes"][0]["nutrition_per_serving"]["kcal"] += 1
    assert apply_mod.plan_id_for(data) != apply_mod.plan_id_for(changed)


def test_nutrition_audit_can_use_manifest_as_supplemental_basis():
    audit = _load_script("audit_gold_v3_nutrition_realism")
    manifest_item = {
        "nutrition_basis": "estimated_cooked_per_serving",
        "serving_weight_g": 320,
        "yield_notes": "dry grain cooked yield adjusted",
    }
    item = audit.evaluate_nutrition_realism(
        {
            "id": 235,
            "title": "Гречка с индейкой",
            "display_title": "Гречка с индейкой",
            "description": "",
            "meal_type": "lunch",
            "category": "main",
            "servings": 2,
            "calories_per_serving": 410,
            "protein_g": 35,
            "fat_g": 10,
            "carbs_g": 45,
            "nutrition_coverage_json": None,
            "nutrition_serving_size_text": None,
            "serving_size_amount": None,
            "yield_type": None,
        },
        [{"name": "гречка"}, {"name": "индейка"}, {"name": "морковь"}],
        [{"text": "Отварите гречку."}, {"text": "Приготовьте индейку."}, {"text": "Соедините."}],
        manifest_item,
    )
    assert "db_no_portion_basis_manifest_available" in item["flags"]
    assert "db_dry_grain_yield_unknown_manifest_available" in item["flags"]
    assert item["manifest_basis_available"] is True
