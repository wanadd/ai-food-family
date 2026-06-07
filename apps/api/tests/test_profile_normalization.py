"""Tests for profile normalization (dedupe, trim, member nutrition)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

API_ROOT = Path(__file__).resolve().parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.schemas.nutrition_profile import NutritionProfileData  # noqa: E402
from app.services.normalization import profile  # noqa: E402


def test_normalize_string_list_dedup_and_trim():
    result = profile.normalize_string_list([" Молоко ", "молоко", "", "Орехи", "орехи"])
    assert result == ["Молоко", "Орехи"]


def test_normalize_string_list_handles_none_and_str():
    assert profile.normalize_string_list(None) == []
    assert profile.normalize_string_list("глютен") == ["глютен"]


def test_clean_text_trims():
    assert profile.clean_text("  hi  ") == "hi"
    assert profile.clean_text(None) == ""


def test_normalize_profile_dict_cleans_lists_and_text():
    out = profile.normalize_profile_dict(
        {
            "allergies": ["орехи", "Орехи", ""],
            "diets": ["веган", "веган"],
            "favorite_foods": "  паста ",
            "unknown": 42,
        }
    )
    assert out["allergies"] == ["орехи"]
    assert out["diets"] == ["веган"]
    assert out["favorite_foods"] == "паста"
    assert out["unknown"] == 42


def test_normalize_member_nutrition_empty():
    assert profile.normalize_member_nutrition(None) == {}
    assert profile.normalize_member_nutrition({}) == {}


def test_normalize_profile_payload_pydantic():
    payload = NutritionProfileData(
        allergies=["орехи", "Орехи", " "],
        diets=["кето", "кето"],
        favorite_foods="  рис  ",
        medical_restrictions=" нет ",
    )
    cleaned = profile.normalize_profile_payload(payload)
    assert cleaned.allergies == ["орехи"]
    assert cleaned.diets == ["кето"]
    assert cleaned.favorite_foods == "рис"
    assert cleaned.medical_restrictions == "нет"
    # original payload must not be mutated (model_copy used)
    assert payload.allergies == ["орехи", "Орехи", " "]
