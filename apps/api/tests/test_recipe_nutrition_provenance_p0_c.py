from __future__ import annotations

from datetime import datetime, timezone
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

API_DIR = Path(__file__).resolve().parents[1]
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

from app.services.nutrition.food_composition_registry import (
    FOOD_COMPOSITION_SOURCE_REGISTRY,
)
from app.services.nutrition.recipe_nutrition_provenance import (
    FoodMatch,
    FoodNutrientFact,
    choose_preferred_fact_group,
    resolve_servings_with_provenance,
    summarize_provenance,
)
from app.services.recipes.mapper import canonical_macro_display, nutrition_summary


def _fact(
    food: str,
    nutrient: str,
    value: float | None,
    *,
    source_id: str = "SRC-RU-FIC-FOODCOMP",
    locator: str = "fic:2024:food=apple:state=raw",
    version: str = "FIC reference edition 2024",
    state: str = "raw",
    status: str = "external_verified",
    data_type: str | None = None,
    fdc_id: int | None = None,
) -> FoodNutrientFact:
    return FoodNutrientFact(
        canonical_food_key=food,
        nutrient_key=nutrient,
        value=value,
        unit="kcal" if nutrient == "energy_kcal" else "g",
        basis_amount=100.0,
        basis_unit="g",
        source_id=source_id,
        source_record_locator=locator,
        source_version=version,
        source_data_type=data_type,
        fdc_id=fdc_id,
        food_state=state,
        provenance_status=status,
        source_food_name=food,
        match_method="exact_curated_mapping",
        match_confidence="strong",
        retrieved_or_imported_at=datetime(2026, 9, 9, tzinfo=timezone.utc),
    )


def test_source_registry_distinguishes_fic_fdc_sr_legacy_and_planam_internal():
    assert FOOD_COMPOSITION_SOURCE_REGISTRY["SRC-RU-FIC-FOODCOMP"]["role"] == "PRIMARY_RU"
    assert FOOD_COMPOSITION_SOURCE_REGISTRY["SRC-USDA-FDC"]["role"] == (
        "INTERNATIONAL_FALLBACK_REFERENCE"
    )
    assert FOOD_COMPOSITION_SOURCE_REGISTRY["SRC-USDA-SR-LEGACY"]["role"] == (
        "OBSOLETE_FOR_PRIMARY"
    )
    assert FOOD_COMPOSITION_SOURCE_REGISTRY["SRC-PLANAM-V1-NUTRITION-FACTS"]["role"] == (
        "INTERNAL_LEGACY_UNSOURCED"
    )


def test_external_verified_requires_source_locator_and_version():
    with pytest.raises(ValueError):
        _fact("apple", "energy_kcal", 52, locator="")
    with pytest.raises(ValueError):
        _fact("apple", "energy_kcal", 52, version="")


def test_planam_internal_constant_cannot_claim_external_verified():
    with pytest.raises(ValueError):
        _fact(
            "курица",
            "energy_kcal",
            190,
            source_id="SRC-PLANAM-V1-NUTRITION-FACTS",
            locator="nutrition_data.py:курица",
            version="planam_v1",
            status="external_verified",
        )
    fact = _fact(
        "курица",
        "energy_kcal",
        190,
        source_id="SRC-PLANAM-V1-NUTRITION-FACTS",
        locator="nutrition_data.py:курица",
        version="planam_v1",
        status="internal_legacy_unsourced",
    )
    assert fact.provenance_status == "internal_legacy_unsourced"


def test_fic_fixture_uses_locator_not_fabricated_external_id():
    fact = _fact("яблоко", "energy_kcal", 52)
    record = fact.to_record()
    assert record["source_id"] == "SRC-RU-FIC-FOODCOMP"
    assert record["source_record_locator"] == "fic:2024:food=apple:state=raw"
    assert record["source_record_id_or_locator"] == record["source_record_locator"]
    assert record["food_state"] == "raw"


def test_fdc_fixture_preserves_fdc_id_and_data_type():
    fact = _fact(
        "chicken_breast",
        "protein_g",
        23.6,
        source_id="SRC-USDA-FDC",
        locator="fdc:2646170",
        version="FoodData Central Foundation 04/2026",
        data_type="Foundation",
        fdc_id=2646170,
    )
    record = fact.to_record()
    assert record["fdc_id"] == 2646170
    assert record["source_data_type"] == "Foundation"


def test_sr_legacy_is_obsolete_and_not_preferred_primary():
    current = [_fact("rice", "energy_kcal", 130, source_id="SRC-USDA-FDC",
                     locator="fdc:1102047", version="FoodData Central FNDDS 10/2024",
                     data_type="FNDDS", fdc_id=1102047, state="cooked")]
    legacy = [_fact("rice", "energy_kcal", 129, source_id="SRC-USDA-SR-LEGACY",
                    locator="sr-legacy:20045", version="SR Legacy 04/2018",
                    data_type="SR Legacy", state="cooked")]
    assert legacy[0].obsolete_for_primary is True
    assert choose_preferred_fact_group([legacy, current]) is current


def test_food_match_candidate_or_ambiguous_is_not_verified_match():
    with pytest.raises(ValueError):
        FoodMatch(
            normalized_ingredient_name="яблоко",
            original_ingredient_text="яблоко",
            status="matched",
            canonical_food_key="яблоко",
            source_id="SRC-RU-FIC-FOODCOMP",
            source_record_locator="fic:2024:food=apple",
            source_food_name="яблоко",
            match_method="candidate_only",
            match_confidence="weak",
        )
    ambiguous = FoodMatch(
        normalized_ingredient_name="перец",
        original_ingredient_text="перец",
        status="ambiguous",
        review_reason="raw_name_matches_multiple_foods",
    )
    assert ambiguous.status == "ambiguous"


def test_raw_and_cooked_state_remain_distinct():
    raw = _fact("rice", "energy_kcal", 360, state="raw", locator="fic:rice:raw")
    cooked = _fact("rice", "energy_kcal", 130, state="cooked", locator="fic:rice:cooked")
    assert raw.food_state == "raw"
    assert cooked.food_state == "cooked"
    assert raw.source_record_locator != cooked.source_record_locator


def test_missing_fact_is_unavailable_not_zero():
    fact = _fact(
        "unknown",
        "energy_kcal",
        None,
        locator="unavailable:unknown",
        version="none",
        status="unavailable",
    )
    assert fact.value is None
    assert fact.contribution_for_grams(100) is None


def test_mixed_source_recipe_provenance_cannot_claim_fully_external_verified():
    serving = resolve_servings_with_provenance(2, "dinner", "main")
    records = [
        {"match": {"status": "matched"}, "facts": [_fact("яблоко", "energy_kcal", 52).to_record()]},
        {
            "match": {"status": "matched"},
            "facts": [
                _fact(
                    "chicken_breast",
                    "energy_kcal",
                    113,
                    source_id="SRC-USDA-FDC",
                    locator="fdc:2646170",
                    version="FoodData Central Foundation 04/2026",
                    data_type="Foundation",
                    fdc_id=2646170,
                ).to_record()
            ],
        },
        {
            "match": {"status": "matched"},
            "facts": [
                _fact(
                    "картофель",
                    "energy_kcal",
                    77,
                    source_id="SRC-PLANAM-V1-NUTRITION-FACTS",
                    locator="nutrition_data.py:картофель",
                    version="planam_v1",
                    status="internal_legacy_unsourced",
                ).to_record()
            ],
        },
    ]
    summary = summarize_provenance(
        records,
        method="fixture_macro_sum_v1",
        serving_resolution=serving,
    )
    assert summary["nutrition_source_kind"] == "mixed"
    assert summary["needs_review"] is True
    assert {r["source_id"] for r in summary["nutrition_source_records"]} == {
        "SRC-RU-FIC-FOODCOMP",
        "SRC-USDA-FDC",
        "SRC-PLANAM-V1-NUTRITION-FACTS",
    }


def test_legacy_serving_fallback_is_not_canonical_verified_per_serving():
    resolved = resolve_servings_with_provenance(None, "snack", "")
    assert resolved.servings == 1.0
    assert resolved.source == "legacy_unsourced_serving_estimate"
    assert resolved.canonical_per_serving is False


def test_recipe_mapper_selects_provenance_complete_new_fields_as_canonical_display():
    recipe = SimpleNamespace(
        calories_per_serving=999.0,
        protein_g=1.0,
        fat_g=2.0,
        carbs_g=3.0,
        nutrition_confidence="estimated",
        nutrition_calculated_at=None,
        nutrition_kcal_total=600.0,
        nutrition_protein_total=30.0,
        nutrition_fat_total=20.0,
        nutrition_carbs_total=80.0,
        nutrition_kcal_per_serving=300.0,
        nutrition_protein_per_serving=15.0,
        nutrition_fat_per_serving=10.0,
        nutrition_carbs_per_serving=40.0,
        nutrition_servings=2.0,
        nutrition_serving_size_text="1 порция",
        nutrition_source="fixture",
        nutrition_source_kind="external_verified",
        nutrition_provenance_json={"nutrition_source_kind": "external_verified"},
        nutrition_needs_review=False,
        nutrition_review_reason=None,
    )
    assert canonical_macro_display(recipe) == {
        "kcal": 300.0,
        "protein": 15.0,
        "fat": 10.0,
        "carbs": 40.0,
        "status": "external_verified",
    }
    assert nutrition_summary(recipe).source_kind == "external_verified"


def test_recipe_mapper_legacy_fallback_stays_explicit():
    recipe = SimpleNamespace(
        calories_per_serving=250.0,
        protein_g=10.0,
        fat_g=8.0,
        carbs_g=30.0,
        nutrition_confidence=None,
        nutrition_calculated_at=None,
    )
    assert canonical_macro_display(recipe)["status"] == "legacy_recipe_macro_fields"
