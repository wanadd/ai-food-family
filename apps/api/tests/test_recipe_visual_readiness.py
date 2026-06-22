from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


def _load_audit():
    path = ROOT / "backend" / "scripts" / "audit_recipe_visual_readiness.py"
    spec = importlib.util.spec_from_file_location("audit_recipe_visual_readiness", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_image_fields_detects_broken_refs():
    audit = _load_audit()
    result = audit.image_fields(
        {
            "hero_image_url": "undefined",
            "image_url": "/recipe-images/2/hero.webp",
            "thumbnail_url": None,
        }
    )
    assert "hero_image_url" in result["broken_fields"]
    assert result["any_present"] is True


def test_image_fields_safe_placeholder_when_no_urls():
    audit = _load_audit()
    result = audit.image_fields({"hero_image_url": None, "image_url": "", "thumbnail_url": None})
    assert result["safe_placeholder_ok"] is True
    assert result["any_present"] is False


def test_evaluate_recipe_pilot_requires_all_three_images():
    audit = _load_audit()
    row = {
        "id": 256,
        "title": "Test",
        "display_title": "Test",
        "description": "Desc",
        "hero_image_url": "/recipe-images/256/hero.webp",
        "image_url": None,
        "thumbnail_url": None,
    }
    payload = {
        "title": "Test",
        "description": "Desc",
        "ingredients": [{"name": "A", "amount": "1 шт"}],
        "steps": ["Step"],
        "calories_per_serving": 300,
        "protein_g": 10,
        "fat_g": 5,
        "carbs_g": 40,
    }
    item = audit.evaluate_recipe(row, payload, cohort="pilot", check_public=False)
    assert "pilot_images_incomplete" in item["blockers"]


def test_evaluate_recipe_upgraded_missing_images_is_warning_not_blocker():
    audit = _load_audit()
    row = {
        "id": 2,
        "title": "Омлет",
        "display_title": "Омлет",
        "description": "Описание",
        "hero_image_url": None,
        "image_url": None,
        "thumbnail_url": None,
    }
    payload = {
        "title": "Омлет",
        "description": "Описание",
        "ingredients": [{"name": "Яйца", "amount": "3 шт"}],
        "steps": ["Шаг 1", "Шаг 2", "Шаг 3"],
        "calories_per_serving": 300,
        "protein_g": 10,
        "fat_g": 5,
        "carbs_g": 40,
    }
    item = audit.evaluate_recipe(row, payload, cohort="upgraded")
    assert "missing_images" in item["warnings"]
    assert "pilot_images_incomplete" not in item["blockers"]
    assert item["ok"] is True


def test_evaluate_recipe_blocks_source_leakage():
    audit = _load_audit()
    row = {
        "id": 2,
        "title": "Test",
        "display_title": "Test",
        "description": "povarenok leak",
        "hero_image_url": None,
        "image_url": None,
        "thumbnail_url": None,
    }
    payload = {
        "title": "Test",
        "description": "povarenok leak",
        "ingredients": [{"name": "A", "amount": "1 шт"}],
        "steps": ["Step"],
        "calories_per_serving": 1,
        "protein_g": 1,
        "fat_g": 1,
        "carbs_g": 1,
    }
    item = audit.evaluate_recipe(row, payload, cohort="upgraded")
    assert any(b.startswith("source_leakage") for b in item["blockers"])


def test_summarize_counts():
    audit = _load_audit()
    items = [
        {
            "images": {"any_present": True, "safe_placeholder_ok": False},
            "blockers": [],
            "warnings": [],
        },
        {
            "images": {"any_present": False, "safe_placeholder_ok": True},
            "blockers": [],
            "warnings": ["missing_images"],
        },
    ]
    summary = audit.summarize(items)
    assert summary["recipes_checked"] == 2
    assert summary["with_images"] == 1
    assert summary["missing_images"] == 1
    assert summary["passed"] is True
