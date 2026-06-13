"""Tests for Recipe Gold V3 importer dry-run (Stage R)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

API_ROOT = Path(__file__).resolve().parents[1]
ROOT = API_ROOT.parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.recipes.recipe_gold_v3_importer import (  # noqa: E402
    apply_import_gold_v3_batch,
    detect_existing_duplicates,
    is_gold_v3_import_recipe,
    load_gold_v3_jsonl,
    map_gold_v3_to_db_payload,
    normalize_recipe_title,
    plan_import_gold_v3_batch,
    get_mapping_summary,
)

CLI = ROOT / "backend" / "scripts" / "import_recipe_gold_v3_dry_run.py"


def _db_row(
    rid: int,
    title: str,
    *,
    gold_v3: bool = True,
    source_type: str | None = None,
) -> tuple:
    norm = normalize_recipe_title(title)
    tags = ["gold_v3", "schema:recipe_gold_v3"] if gold_v3 else ["legacy"]
    st = source_type if source_type is not None else ("import" if gold_v3 else "manual")
    return (rid, title, norm, tags, st)


class _FakeSession:
    def __init__(self, rows: list[tuple] | None = None):
        self.rows = rows or []
        self.rolled_back = False

    def add(self, obj):
        pass

    def flush(self):
        pass

    def commit(self):
        pass

    def rollback(self):
        self.rolled_back = True

    def execute(self, stmt):
        class R:
            def __init__(self, data):
                self._data = data

            def all(self):
                return list(self._data)

        return R(self.rows)


def _ing(name: str, *, category: str = "\u043e\u0432\u043e\u0449\u0438", amount: float = 100) -> dict:
    return {
        "name": name,
        "amount": amount,
        "unit": "\u0433",
        "display_amount": f"{int(amount)} \u0433",
        "category": category,
        "optional": False,
        "shopping_name": name,
    }


def _step(num: int, text: str) -> dict:
    return {"step_number": num, "text": text}


def _valid_recipe(**overrides) -> dict:
    base = {
        "schema_version": "recipe_gold_v3",
        "status": "gold",
        "source_type": "generated_original",
        "source_signal_ids": ["pov_sig_000001"],
        "originality": {
            "is_original_planam_recipe": True,
            "no_source_title_used": True,
            "no_source_steps_used": True,
            "no_direct_copy": True,
            "source_similarity_risk": "low",
        },
        "title": "\u041a\u0443\u0440\u0438\u043d\u043e\u0435 \u0440\u0430\u0433\u0443 \u0441 \u043e\u0432\u043e\u0449\u0430\u043c\u0438",
        "description": "\u0421\u044b\u0442\u043d\u043e\u0435 \u0434\u043e\u043c\u0430\u0448\u043d\u0435\u0435 \u0431\u043b\u044e\u0434\u043e.",
        "meal_type": "dinner",
        "category": "main",
        "cuisine_style": "\u0441\u0435\u043c\u0435\u0439\u043d\u0430\u044f",
        "servings": 4,
        "prep_time_min": 15,
        "cook_time_min": 30,
        "total_time_min": 45,
        "difficulty": "easy",
        "family_fit": "high",
        "ingredients": [
            _ing("\u043a\u0443\u0440\u0438\u043d\u043e\u0435 \u0444\u0438\u043b\u0435", category="\u043c\u044f\u0441\u043e_\u043f\u0442\u0438\u0446\u0430", amount=500),
            _ing("\u043a\u0430\u0440\u0442\u043e\u0444\u0435\u043b\u044c"),
            _ing("\u043c\u043e\u0440\u043a\u043e\u0432\u044c"),
            _ing("\u043b\u0443\u043a \u0440\u0435\u043f\u0447\u0430\u0442\u044b\u0439"),
        ],
        "steps": [
            _step(1, "\u041d\u0430\u0440\u0435\u0436\u044c\u0442\u0435 \u043a\u0443\u0440\u0438\u0446\u0443 \u0438 \u043e\u0432\u043e\u0449\u0438 \u043a\u0443\u0431\u0438\u043a\u0430\u043c\u0438 \u0434\u043b\u044f \u0440\u0430\u0432\u043d\u043e\u043c\u0435\u0440\u043d\u043e\u0433\u043e \u043f\u0440\u0438\u0433\u043e\u0442\u043e\u0432\u043b\u0435\u043d\u0438\u044f."),
            _step(2, "\u0420\u0430\u0437\u043e\u0433\u0440\u0435\u0439\u0442\u0435 \u0441\u043a\u043e\u0432\u043e\u0440\u043e\u0434\u0443 \u0441 \u043c\u0430\u0441\u043b\u043e\u043c \u0438 \u043e\u0431\u0436\u0430\u0440\u044c\u0442\u0435 \u043a\u0443\u0440\u0438\u0446\u0443 \u0434\u043e \u0437\u043e\u043b\u043e\u0442\u0438\u0441\u0442\u043e\u0439 \u043a\u043e\u0440\u043e\u0447\u043a\u0438."),
            _step(3, "\u0414\u043e\u0431\u0430\u0432\u044c\u0442\u0435 \u043e\u0432\u043e\u0449\u0438, \u043f\u0435\u0440\u0435\u043c\u0435\u0448\u0430\u0439\u0442\u0435 \u0438 \u0442\u0443\u0448\u0438\u0442\u0435 \u043f\u043e\u0434 \u043a\u0440\u044b\u0448\u043a\u043e\u0439 \u0434\u0432\u0430\u0434\u0446\u0430\u0442\u044c \u043c\u0438\u043d\u0443\u0442."),
            _step(4, "\u041f\u0435\u0440\u0435\u0434 \u043f\u043e\u0434\u0430\u0447\u0435\u0439 \u0434\u0430\u0439\u0442\u0435 \u0431\u043b\u044e\u0434\u0443 \u043d\u0430\u0441\u0442\u043e\u044f\u0442\u044c\u0441\u044f \u0438 \u043f\u043e\u0441\u044b\u043f\u044c\u0442\u0435 \u0437\u0435\u043b\u0435\u043d\u044c\u044e."),
        ],
        "nutrition_per_serving": {
            "kcal": 410,
            "protein_g": 30,
            "fat_g": 15,
            "carbs_g": 35,
            "fiber_g": 5,
            "salt_g": 1.2,
            "sugar_g": 3,
        },
        "restriction_keys": ["no_pork", "no_alcohol"],
        "allergen_keys": [],
        "diet_tags": ["balanced"],
        "shopping": {"aggregation_safe": True, "has_fractional_amounts": False, "rounding_notes": ""},
        "image_prompt_data": {
            "dish_visual_summary": "\u041a\u0443\u0440\u0438\u043d\u043e\u0435 \u0440\u0430\u0433\u0443",
            "serving_style": "PLANAM",
            "avoid_visuals": ["\u0442\u0435\u043a\u0441\u0442"],
        },
        "quality": {"score": 99, "flags": [], "warnings": []},
    }
    base.update(overrides)
    return base


def test_load_jsonl_valid(tmp_path):
    p = tmp_path / "in.jsonl"
    p.write_text(json.dumps(_valid_recipe(), ensure_ascii=False) + "\n", encoding="utf-8")
    rows = load_gold_v3_jsonl(p)
    assert len(rows) == 1
    assert rows[0]["line"] == 1


def test_invalid_jsonl_fails(tmp_path):
    p = tmp_path / "bad.jsonl"
    p.write_text("{not json\n", encoding="utf-8")
    with pytest.raises(ValueError, match="invalid JSON"):
        load_gold_v3_jsonl(p)


def test_normalize_title_works():
    assert normalize_recipe_title("  \u0421\u0423\u041f!!!  ") == "\u0441\u0443\u043f"
    assert normalize_recipe_title("\u0451\u0436\u0438\u043a") == normalize_recipe_title("\u0435\u0436\u0438\u043a")


def test_map_required_fields():
    payload = map_gold_v3_to_db_payload(_valid_recipe())
    assert payload["title"]
    assert payload["meal_type"] == "dinner"
    assert payload["category"] == "main"
    assert payload["source_type"] == "import"
    assert payload["schema_version"] == "recipe_gold_v3"
    assert len(payload["ingredient_rows_plan"]) == 4


def test_map_nutrition_fields():
    payload = map_gold_v3_to_db_payload(_valid_recipe())
    assert payload["calories_per_serving"] == 410.0
    assert payload["protein_g"] == 30.0
    assert payload["nutrition_kcal_per_serving"] == 410.0
    assert payload["nutrition_protein_per_serving"] == 30.0
    assert payload["nutrition_coverage_json"]["salt_g"] == 1.2
    assert not payload["_missing_nutrition_keys"]


def test_map_ingredients_fields():
    payload = map_gold_v3_to_db_payload(_valid_recipe())
    row = payload["ingredient_rows_plan"][0]
    assert row["shopping_name"]
    assert row["amount"]
    assert row["unit"] == "\u0433"
    assert not payload["_ingredient_issues"]


def test_missing_shopping_name_caught_before_postprocess():
    from app.recipes.recipe_gold_v3_importer import _map_ingredient

    ing = {
        "name": "\u043a\u0430\u0440\u0442\u043e\u0444\u0435\u043b\u044c",
        "amount": 100,
        "unit": "\u0433",
        "display_amount": "100 \u0433",
        "category": "\u043e\u0432\u043e\u0449\u0438",
        "optional": False,
        "shopping_name": "",
    }
    _, issues = _map_ingredient(ing, 0)
    assert any(i["code"] == "missing_shopping_name" for i in issues)


def test_postprocess_autofills_shopping_name_in_map():
    recipe = _valid_recipe(
        ingredients=[
            {
                "name": "\u043a\u0430\u0440\u0442\u043e\u0444\u0435\u043b\u044c",
                "amount": 100,
                "unit": "\u0433",
                "display_amount": "100 \u0433",
                "category": "\u043e\u0432\u043e\u0449\u0438",
                "optional": False,
                "shopping_name": "",
            },
            _ing("\u043c\u043e\u0440\u043a\u043e\u0432\u044c"),
            _ing("\u043b\u0443\u043a \u0440\u0435\u043f\u0447\u0430\u0442\u044b\u0439"),
            _ing("\u043f\u0435\u0440\u0435\u0446"),
        ]
    )
    payload = map_gold_v3_to_db_payload(recipe)
    assert payload["ingredient_rows_plan"][0]["shopping_name"] == "\u043a\u0430\u0440\u0442\u043e\u0444\u0435\u043b\u044c"


def test_duplicate_title_in_batch_fails():
    a = _valid_recipe(title="\u0421\u0443\u043f \u043b\u0435\u0442\u043d\u0438\u0439")
    b = _valid_recipe(title="\u0421\u0443\u043f \u043b\u0435\u0442\u043d\u0438\u0439!")
    result = plan_import_gold_v3_batch([a, b], dry_run=True, quality_gate_ok=True)
    assert result["errors_by_code"].get("duplicate_title_in_batch", 0) > 0
    assert result["ok"] is False


def test_plan_import_with_dry_run_false_is_read_only_plan():
    result = plan_import_gold_v3_batch([_valid_recipe()], dry_run=False, quality_gate_ok=True)
    assert result["would_create"] == 1
    assert result["dry_run"] is False


def test_apply_import_creates_recipe(monkeypatch):
    class FakeRecipe:
        _next_id = 100

        def __init__(self, **kwargs):
            self.id = FakeRecipe._next_id
            FakeRecipe._next_id += 1
            self.__dict__.update(kwargs)
            self.title = kwargs.get("title", "")

    monkeypatch.setattr("app.models.recipe.Recipe", FakeRecipe)
    monkeypatch.setattr(
        "app.services.recipe_storage.persist_recipe_structure",
        lambda *a, **k: None,
    )
    monkeypatch.setattr(
        "app.recipes.recipe_gold_v3_importer.collect_db_snapshot",
        lambda _s: {
            "recipes_total": 1,
            "recipe_ingredients_total": 4,
            "gold_v3_count": 1,
            "generated_original_count": 0,
            "max_recipe_id": 100,
        },
    )

    result = apply_import_gold_v3_batch(
        [_valid_recipe(title="\u041a\u043e\u0442\u043b\u0435\u0442\u044b \u0434\u043e\u043c\u0430\u0448\u043d\u0438\u0435")],
        session=_FakeSession(),
        quality_gate_ok=True,
    )
    assert result["ok"] is True
    assert result["created_count"] == 1


def test_apply_import_idempotent_skip_on_duplicate_title(monkeypatch):
    title = "\u0421\u0443\u043f \u0438\u0437 \u0431\u0440\u043e\u043a\u043a\u043e\u043b\u0438"
    existing = [_db_row(42, title)]

    monkeypatch.setattr(
        "app.recipes.recipe_gold_v3_importer.collect_db_snapshot",
        lambda _s: {
            "recipes_total": 1,
            "recipe_ingredients_total": 4,
            "gold_v3_count": 1,
            "generated_original_count": 0,
            "max_recipe_id": 42,
        },
    )

    result = apply_import_gold_v3_batch(
        [_valid_recipe(title=title)],
        session=_FakeSession(existing),
        quality_gate_ok=True,
    )
    assert result["created_count"] == 0
    assert result["skipped_count"] == 1
    assert result["ok"] is True
    assert result.get("idempotent_full_skip") is True


def test_apply_import_aborts_on_partial_db_duplicate(monkeypatch):
    """If some titles exist in DB and others do not, abort — no partial write."""
    title = "\u0421\u0443\u043f \u0438\u0437 \u0431\u0440\u043e\u043a\u043a\u043e\u043b\u0438"
    existing = [_db_row(42, title)]

    monkeypatch.setattr(
        "app.recipes.recipe_gold_v3_importer.collect_db_snapshot",
        lambda _s: {
            "recipes_total": 1,
            "recipe_ingredients_total": 0,
            "gold_v3_count": 1,
            "generated_original_count": 0,
            "max_recipe_id": 42,
        },
    )

    recipes = [
        _valid_recipe(title=title),
        _valid_recipe(title="\u041a\u043e\u0442\u043b\u0435\u0442\u044b \u0434\u043e\u043c\u0430\u0448\u043d\u0438\u0435"),
    ]
    result = apply_import_gold_v3_batch(recipes, session=_FakeSession(existing), quality_gate_ok=True)
    assert result["ok"] is False
    assert result["abort_reason"] == "import_plan_not_ok"
    assert result["created_count"] == 0


def test_dry_run_idempotent_full_skip_after_import():
    title = "\u0421\u0443\u043f \u0438\u0437 \u0431\u0440\u043e\u043a\u043a\u043e\u043b\u0438"
    session = _FakeSession([_db_row(256, title)])
    result = plan_import_gold_v3_batch(
        [_valid_recipe(title=title)],
        session=session,
        dry_run=True,
        quality_gate_ok=True,
    )
    assert result["would_create"] == 0
    assert result["would_skip"] == 1
    assert result["idempotent_full_skip"] is True
    assert result["ok"] is True
    assert "duplicate_title_in_db" not in result["errors_by_code"]
    assert result["warnings_by_code"].get("idempotent_duplicate_in_db") == 1


def test_dry_run_partial_db_duplicate_fails():
    title = "\u0421\u0443\u043f \u0438\u0437 \u0431\u0440\u043e\u043a\u043a\u043e\u043b\u0438"
    session = _FakeSession([_db_row(42, title)])
    recipes = [
        _valid_recipe(title=title),
        _valid_recipe(title="\u041a\u043e\u0442\u043b\u0435\u0442\u044b \u0434\u043e\u043c\u0430\u0448\u043d\u0438\u0435"),
    ]
    result = plan_import_gold_v3_batch(recipes, session=session, dry_run=True, quality_gate_ok=True)
    assert result["ok"] is False
    assert result["idempotent_full_skip"] is False
    assert result["would_create"] == 1


def test_dry_run_unrelated_db_duplicate_fails():
    title = "\u0421\u0443\u043f \u0438\u0437 \u0431\u0440\u043e\u043a\u043a\u043e\u043b\u0438"
    session = _FakeSession([_db_row(99, title, gold_v3=False, source_type="manual")])
    result = plan_import_gold_v3_batch(
        [_valid_recipe(title=title)],
        session=session,
        dry_run=True,
        quality_gate_ok=True,
    )
    assert result["ok"] is False
    assert result["errors_by_code"].get("duplicate_title_in_db_unrelated") == 1
    assert result["idempotent_full_skip"] is False


def test_is_gold_v3_import_recipe_helper():
    assert is_gold_v3_import_recipe(["gold_v3"], "manual") is True
    assert is_gold_v3_import_recipe([], "import") is True
    assert is_gold_v3_import_recipe([], "manual") is False


def test_dry_run_full_batch_idempotent_skip(monkeypatch):
    recipes = [
        _valid_recipe(title=f"\u041a\u0443\u0440\u0438\u043d\u043e\u0435 \u0440\u0430\u0433\u0443 \u0432\u0430\u0440\u0438\u0430\u043d\u0442 {i}")
        for i in range(10)
    ]
    rows = [
        _db_row(256 + i, recipes[i]["title"])
        for i in range(10)
    ]
    result = plan_import_gold_v3_batch(
        recipes,
        session=_FakeSession(rows),
        dry_run=True,
        quality_gate_ok=True,
    )
    assert result["would_create"] == 0
    assert result["would_skip"] == 10
    assert result["idempotent_full_skip"] is True
    assert result["ok"] is True


def test_apply_repeated_full_batch_idempotent(monkeypatch):
    recipes = [
        _valid_recipe(title=f"\u041a\u0443\u0440\u0438\u043d\u043e\u0435 \u0440\u0430\u0433\u0443 \u0432\u0430\u0440\u0438\u0430\u043d\u0442 {i}")
        for i in range(10)
    ]
    rows = [_db_row(256 + i, recipes[i]["title"]) for i in range(10)]
    monkeypatch.setattr(
        "app.recipes.recipe_gold_v3_importer.collect_db_snapshot",
        lambda _s: {
            "recipes_total": 263,
            "recipe_ingredients_total": 1652,
            "gold_v3_count": 10,
            "generated_original_count": 0,
            "max_recipe_id": 265,
        },
    )
    result = apply_import_gold_v3_batch(
        recipes,
        session=_FakeSession(rows),
        quality_gate_ok=True,
    )
    assert result["ok"] is True
    assert result["created_count"] == 0
    assert result["skipped_count"] == 10
    assert result.get("idempotent_full_skip") is True


def test_apply_import_rollback_on_exception(monkeypatch):
    class FakeRecipe:
        def __init__(self, **kwargs):
            self.id = 1
            self.__dict__.update(kwargs)

    class FakeSession:
        def __init__(self):
            self.rolled_back = False

        def add(self, obj):
            pass

        def flush(self):
            raise RuntimeError("db flush failed")

        def commit(self):
            pass

        def rollback(self):
            self.rolled_back = True

        def execute(self, stmt):
            class R:
                def all(self):
                    return []

            return R()

    monkeypatch.setattr("app.models.recipe.Recipe", FakeRecipe)
    monkeypatch.setattr(
        "app.recipes.recipe_gold_v3_importer.collect_db_snapshot",
        lambda _s: {"recipes_total": 0, "recipe_ingredients_total": 0, "gold_v3_count": 0,
                    "generated_original_count": 0, "max_recipe_id": 0},
    )
    session = _FakeSession()
    result = apply_import_gold_v3_batch(
        [_valid_recipe()],
        session=session,
        quality_gate_ok=True,
    )
    assert result["ok"] is False
    assert result["abort_reason"] == "db_write_failed"
    assert session.rolled_back is True


def test_nutrition_payload_maps_to_db_fields():
    payload = map_gold_v3_to_db_payload(_valid_recipe())
    assert payload["calories_per_serving"] == 410
    assert payload["protein_g"] == 30
    assert payload["nutrition_kcal_per_serving"] == 410
    assert payload["nutrition_coverage_json"]["salt_g"] == 1.2
    assert "salt_g" in payload.get("_nutrition_aliases", {}) or payload["nutrition_coverage_json"].get("salt_g")


def test_ingredient_rows_use_shopping_name_and_legacy_category():
    payload = map_gold_v3_to_db_payload(_valid_recipe())
    rows = payload["ingredient_rows_plan"]
    assert len(rows) >= 4
    assert rows[0]["name"] == rows[0]["shopping_name"]
    assert rows[0]["quantity"]
    assert rows[0]["unit"]
    assert rows[0]["category"]


def test_dry_run_plan_aborts_on_batch_duplicate():
    a = _valid_recipe(title="\u0421\u0443\u043f \u043b\u0435\u0442\u043d\u0438\u0439")
    b = _valid_recipe(title="\u0421\u0443\u043f \u043b\u0435\u0442\u043d\u0438\u0439!")
    result = plan_import_gold_v3_batch([a, b], dry_run=True, quality_gate_ok=True)
    assert result["ok"] is False
    assert result["errors_by_code"].get("duplicate_title_in_batch")


def test_dry_run_db_duplicate_fails_plan():
    payloads = [map_gold_v3_to_db_payload(_valid_recipe(title="\u0421\u0443\u043f"))]
    dupes = detect_existing_duplicates(None, payloads)
    assert dupes["db_check_available"] is False


def test_cli_dry_run_passes_with_expected_count_10(tmp_path):
    inp = tmp_path / "in.jsonl"
    report = tmp_path / "report.md"
    quality = tmp_path / "quality.md"
    quality.write_text("Quality gate: **`PASS`**\n", encoding="utf-8")
    lines = [
        json.dumps(
            _valid_recipe(title=f"\u041a\u0443\u0440\u0438\u043d\u043e\u0435 \u0440\u0430\u0433\u0443 \u0432\u0430\u0440\u0438\u0430\u043d\u0442 {i}"),
            ensure_ascii=False,
        )
        for i in range(10)
    ]
    inp.write_text("\n".join(lines) + "\n", encoding="utf-8")
    proc = subprocess.run(
        [
            sys.executable, str(CLI),
            "--input", str(inp),
            "--quality-report", str(quality),
            "--report", str(report),
            "--dry-run", "--expected-count", "10",
        ],
        cwd=str(ROOT), capture_output=True, text=True, check=False,
    )
    assert proc.returncode == 0, proc.stderr


def test_detect_duplicates_without_session():
    payloads = [
        map_gold_v3_to_db_payload(_valid_recipe(title="A")),
        map_gold_v3_to_db_payload(_valid_recipe(title="B")),
    ]
    dupes = detect_existing_duplicates(None, payloads)
    assert dupes["db_check_available"] is False


def test_stage_f1_fixture_dry_run_pass():
    result = plan_import_gold_v3_batch([_valid_recipe()], dry_run=True, quality_gate_ok=True)
    assert result["ok"] is True
    assert result["would_create"] == 1
    assert result["would_skip"] == 0


def test_ui_nutrition_alias_mapping():
    summary = get_mapping_summary()
    assert "calories_per_serving" in summary["legacy_nutrition_keys"]
    assert "salt_g" in summary["nutrition_aliases"]


def test_cli_refuses_non_dry_run_without_allow_write(tmp_path):
    inp = tmp_path / "in.jsonl"
    report = tmp_path / "report.md"
    quality = tmp_path / "quality.md"
    quality.write_text("Quality gate: **`PASS`**\n", encoding="utf-8")
    inp.write_text(json.dumps(_valid_recipe(), ensure_ascii=False) + "\n", encoding="utf-8")
    proc = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "--input",
            str(inp),
            "--quality-report",
            str(quality),
            "--report",
            str(report),
            "--no-dry-run",
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 1


def test_cli_writes_report(tmp_path):
    inp = tmp_path / "in.jsonl"
    report = tmp_path / "report.md"
    quality = tmp_path / "quality.md"
    quality.write_text("Quality gate: **`PASS`**\n", encoding="utf-8")
    inp.write_text(json.dumps(_valid_recipe(), ensure_ascii=False) + "\n", encoding="utf-8")
    proc = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "--input",
            str(inp),
            "--quality-report",
            str(quality),
            "--report",
            str(report),
            "--dry-run",
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    text = report.read_text(encoding="utf-8")
    assert "Importer Dry-Run Report" in text
    assert "PASS" in text


def test_cli_fails_if_quality_report_not_pass(tmp_path):
    inp = tmp_path / "in.jsonl"
    report = tmp_path / "report.md"
    quality = tmp_path / "quality.md"
    quality.write_text("Quality gate: **`FAIL`**\n", encoding="utf-8")
    inp.write_text(json.dumps(_valid_recipe(), ensure_ascii=False) + "\n", encoding="utf-8")
    proc = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "--input",
            str(inp),
            "--quality-report",
            str(quality),
            "--report",
            str(report),
            "--dry-run",
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 1


def test_cli_passes_with_quality_report_pass(tmp_path):
    inp = tmp_path / "in.jsonl"
    report = tmp_path / "report.md"
    quality = tmp_path / "quality.md"
    quality.write_text("Quality gate: **`PASS`**\n", encoding="utf-8")
    inp.write_text(json.dumps(_valid_recipe(), ensure_ascii=False) + "\n", encoding="utf-8")
    proc = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "--input",
            str(inp),
            "--quality-report",
            str(quality),
            "--report",
            str(report),
            "--dry-run",
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0


def _cli_run(tmp_path, *, extra_args: list[str]) -> subprocess.CompletedProcess:
    inp = tmp_path / "in.jsonl"
    report = tmp_path / "report.md"
    quality = tmp_path / "quality.md"
    quality.write_text("Quality gate: **`PASS`**\n", encoding="utf-8")
    inp.write_text(json.dumps(_valid_recipe(), ensure_ascii=False) + "\n", encoding="utf-8")
    return subprocess.run(
        [
            sys.executable,
            str(CLI),
            "--input",
            str(inp),
            "--quality-report",
            str(quality),
            "--report",
            str(report),
            *extra_args,
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )


def test_cli_dry_run_passes_when_expected_count_matches(tmp_path):
    proc = _cli_run(tmp_path, extra_args=["--dry-run", "--expected-count", "1"])
    assert proc.returncode == 0, proc.stderr
    text = (tmp_path / "report.md").read_text(encoding="utf-8")
    assert "Expected count: `1`" in text
    assert "Actual count: `1`" in text


def test_cli_dry_run_fails_when_expected_count_mismatch(tmp_path):
    proc = _cli_run(tmp_path, extra_args=["--dry-run", "--expected-count", "10"])
    assert proc.returncode == 1
    assert "expected_count_mismatch" in proc.stderr
    assert "expected_count_mismatch" in (tmp_path / "report.md").read_text(encoding="utf-8")


def test_cli_apply_fails_when_expected_count_missing(tmp_path):
    proc = _cli_run(tmp_path, extra_args=["--apply", "--allow-write"])
    assert proc.returncode == 1
    assert "expected_count_required_for_apply" in proc.stderr


def test_cli_apply_fails_when_expected_count_mismatch_before_write(tmp_path):
    proc = _cli_run(tmp_path, extra_args=["--apply", "--allow-write", "--expected-count", "10"])
    assert proc.returncode == 1
    assert "expected_count_mismatch" in proc.stderr
