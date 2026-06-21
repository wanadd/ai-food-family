from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
CANDIDATE = ROOT / "data" / "recipe_v2" / "gold_recipes_30_repaired_candidate.jsonl"


def _load_script(name: str):
    path = ROOT / "backend" / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _records() -> list[dict]:
    return [json.loads(line) for line in CANDIDATE.read_text(encoding="utf-8").splitlines() if line.strip()]


def _valid_recipe() -> dict:
    return {
        "schema_version": "recipe_gold_v3",
        "source_type": "gold_v3_candidate",
        "title": "Курица с рисом",
        "display_title": "Курица с рисом",
        "normalized_title": "курица с рисом",
        "meal_type": "dinner",
        "category": "main",
        "tags": ["gold_v3_candidate"],
        "hero_image_url": None,
        "image_url": None,
        "thumbnail_url": None,
        "ingredients": [
            {"name": "куриное филе", "amount": 200, "unit": "г", "shopping_category_slug": "meat"},
            {"name": "рис", "amount": 100, "unit": "г", "shopping_category_slug": "grains"},
            {"name": "морковь", "amount": 1, "unit": "шт", "shopping_category_slug": "vegetables"},
        ],
        "steps": [{"text": "Раз."}, {"text": "Два."}, {"text": "Три."}],
        "nutrition_per_serving": {"kcal": 350, "protein_g": 30, "fat_g": 10, "carbs_g": 35},
        "image_prompt": "Фото готового блюда.",
    }


def test_dry_run_importer_reads_30_records():
    mod = _load_script("import_gold_v3_repaired_30_dry_run")
    records, errors = mod.load_jsonl(CANDIDATE)
    assert errors == []
    assert len(records) == 30


def test_dry_run_importer_refuses_apply():
    mod = _load_script("import_gold_v3_repaired_30_dry_run")
    assert mod.main(["--apply"]) == 2


def test_dry_run_importer_does_not_mutate_db_session(tmp_path):
    mod = _load_script("import_gold_v3_repaired_30_dry_run")
    report = mod.run_dry_run(
        CANDIDATE,
        tmp_path / "dry_run.md",
        tmp_path / "dry_run.json",
        db_snapshot={
            "db_available": True,
            "recipes_total": 265,
            "current_max_id": 265,
            "simulated_ids": mod.simulated_ids(265, 30),
            "duplicate_title_matches": [],
            "duplicate_normalized_matches": [],
            "duplicate_close_matches": [],
        },
    )
    assert report["apply"] is False
    assert report["db_writes"] == 0


def test_duplicate_detection_works_on_synthetic_db_title_set():
    mod = _load_script("import_gold_v3_repaired_30_dry_run")
    record = _valid_recipe()
    risks = mod.find_duplicate_risks([record], [{"id": 1, "title": "Курица с рисом", "normalized_title": "курица с рисом"}])
    assert risks["duplicate_title_matches"]
    assert risks["duplicate_normalized_matches"]


def test_simulated_id_allocation_starts_after_max_id():
    mod = _load_script("import_gold_v3_repaired_30_dry_run")
    assert mod.simulated_ids(265, 3) == [266, 267, 268]


def test_fixed_pilot_ids_256_265_are_not_reused():
    mod = _load_script("import_gold_v3_repaired_30_dry_run")
    report = mod.evaluate_file_contract(_records(), [])
    assert report["fixed_id_conflicts"] == []


def test_ui_contract_rejects_source_leakage():
    mod = _load_script("audit_gold_v3_repaired_30_ui_contract")
    recipe = _valid_recipe()
    recipe["source_url"] = "https://povarenok.example/recipe"
    report = mod.evaluate_ui_contract([recipe], [])
    assert report["passed"] is False
    assert report["items"][0]["blockers"] == ["source_leakage"]


def test_menu_shopping_dry_run_catches_no_pork_pork_contradiction():
    mod = _load_script("audit_gold_v3_repaired_30_menu_shopping_dry_run")
    recipe = _valid_recipe()
    recipe["title"] = "Свинина с картофелем"
    recipe["tags"] = ["no_pork"]
    recipe["ingredients"][0]["name"] = "свинина"
    report = mod.evaluate_menu_shopping([recipe], [])
    assert report["passed"] is False
    assert "no_pork_plus_pork" in report["items"][0]["blockers"]


def test_menu_shopping_confirms_all_repaired_records_extractable():
    mod = _load_script("audit_gold_v3_repaired_30_menu_shopping_dry_run")
    report = mod.evaluate_menu_shopping(_records(), [])
    assert report["records"] == 30
    assert report["shopping_missing"] == []


def test_dry_run_report_contains_required_fields(tmp_path):
    mod = _load_script("import_gold_v3_repaired_30_dry_run")
    report = mod.run_dry_run(
        CANDIDATE,
        tmp_path / "dry_run.md",
        tmp_path / "dry_run.json",
        db_snapshot={
            "db_available": True,
            "recipes_total": 265,
            "current_max_id": 265,
            "simulated_ids": mod.simulated_ids(265, 30),
            "duplicate_title_matches": [],
            "duplicate_normalized_matches": [],
            "duplicate_close_matches": [],
        },
    )
    assert report["quality_gate"]["valid_for_import"] == 30
    assert report["quality_gate"]["hard_fail"] == 0
    assert report["simulated_ids"] == list(range(266, 296))
    assert report["blocked"] is False
    assert report["apply"] is False
