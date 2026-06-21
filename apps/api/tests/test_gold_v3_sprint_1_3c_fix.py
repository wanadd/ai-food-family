from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
API_ROOT = ROOT / "apps" / "api"
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

CANDIDATE = ROOT / "data" / "recipe_v2" / "gold_recipes_30_repaired_candidate.jsonl"
BAD_TITLE_RE = re.compile(
    r"^\s*(high protein|pro high protein|pro weight loss|pro small portion|pre-workout|post-workout)\s*:",
    re.I,
)
SOURCE_MARKERS = ("Povarenok", "povarenok", "source_url", "original_url", "http")


def _load_script(name: str):
    path = ROOT / "backend" / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _records() -> list[dict]:
    return [
        json.loads(line)
        for line in CANDIDATE.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def test_repaired_candidate_has_exactly_30_records():
    assert len(_records()) == 30


def test_repaired_candidate_every_record_has_minimum_ingredients_and_steps():
    records = _records()
    assert all(len(record.get("ingredients") or []) >= 3 for record in records)
    assert all(len(record.get("steps") or []) >= 3 for record in records)


def test_repaired_candidate_titles_are_clean():
    for record in _records():
        title = str(record.get("title") or "")
        assert not BAD_TITLE_RE.search(title)
        assert "#" not in title
        assert "без свинины" not in title.lower()


def test_repaired_candidate_has_no_source_leakage():
    blob = CANDIDATE.read_text(encoding="utf-8")
    for marker in SOURCE_MARKERS:
        assert marker not in blob


def test_quality_gate_accepts_repaired_candidate_batch():
    mod = _load_script("quality_gate_gold_recipes_30_candidate")
    records, json_errors = mod.load_records()
    report = mod.evaluate(records, json_errors)
    assert report["record_count"] == 30
    assert report["hard_fail"] == 0
    assert report["valid_for_import"] >= 25


def test_quality_gate_catches_two_step_recipe():
    mod = _load_script("quality_gate_gold_recipes_30_candidate")
    recipe = _valid_recipe()
    recipe["steps"] = [{"text": "Первый шаг."}, {"text": "Второй шаг."}]
    ok, blockers = mod.validate_record(recipe, set())
    assert ok is False
    assert "steps_lt_3" in blockers


def test_quality_gate_catches_two_ingredient_recipe():
    mod = _load_script("quality_gate_gold_recipes_30_candidate")
    recipe = _valid_recipe()
    recipe["ingredients"] = recipe["ingredients"][:2]
    ok, blockers = mod.validate_record(recipe, set())
    assert ok is False
    assert "ingredients_lt_3" in blockers


def test_quality_gate_catches_pork_no_pork_contradiction():
    mod = _load_script("quality_gate_gold_recipes_30_candidate")
    recipe = _valid_recipe()
    recipe["title"] = "Свинина с картофелем"
    recipe["tags"] = ["no_pork"]
    recipe["ingredients"][0]["name"] = "свинина"
    ok, blockers = mod.validate_record(recipe, set())
    assert ok is False
    assert "no_pork_plus_pork" in blockers


def _valid_recipe() -> dict:
    return {
        "schema_version": "recipe_gold_v3",
        "source_type": "gold_v3_candidate",
        "meal_type": "dinner",
        "title": "Курица с рисом",
        "display_title": "Курица с рисом",
        "tags": ["gold_v3_candidate"],
        "ingredients": [
            {"name": "куриное филе", "amount": 200, "unit": "г", "shopping_category_slug": "meat_poultry"},
            {"name": "рис", "amount": 100, "unit": "г", "shopping_category_slug": "grains_pasta"},
            {"name": "морковь", "amount": 1, "unit": "шт", "shopping_category_slug": "vegetables_greens"},
        ],
        "steps": [
            {"text": "Подготовить ингредиенты."},
            {"text": "Приготовить курицу и рис."},
            {"text": "Подать блюдо тёплым."},
        ],
        "nutrition_per_serving": {"kcal": 350, "protein_g": 30, "fat_g": 10, "carbs_g": 35},
        "image_prompt": "Фото готового блюда ПланАм без текста.",
    }
