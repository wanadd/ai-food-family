from __future__ import annotations

import sys
from pathlib import Path

import pytest

API_DIR = Path(__file__).resolve().parents[1]
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

from app.services.nutrition.authoritative_food_nutrient_pilot import (
    AUTHORITATIVE_FOOD_MATCHES,
    MACRO_NUTRIENTS,
    convert_quantity_to_fact_basis,
    facts_by_nutrient,
    has_complete_macro_facts,
    ingredient_pilot_record,
    nutrient_facts_for_food,
    resolve_authoritative_food_match,
    simulate_recipe_computability,
    validate_no_safety_fact_generation,
)
from app.services.nutrition.food_identity_foundation import dry_run_food_match
from app.services.nutrition.recipe_nutrition_provenance import FoodMatch


def test_authoritative_food_exact_match_retains_external_id():
    match = dry_run_food_match("рис")
    external = resolve_authoritative_food_match(match)

    assert external is not None
    assert external.external_food_id == 2512381
    assert external.to_food_match("рис").source_record_locator == "fdc:2512381"


def test_ambiguous_source_match_rejected():
    match = dry_run_food_match("сыр")

    assert match.status == "ambiguous"
    assert resolve_authoritative_food_match(match) is None


def test_raw_cooked_mismatch_rejected():
    cooked = FoodMatch(
        normalized_ingredient_name="рис",
        original_ingredient_text="рис вареный",
        status="matched",
        canonical_food_key="rice",
        source_id="SRC-PLANAM-FOOD-IDENTITY-CURATED",
        source_record_locator="test:rice:cooked",
        source_food_name="рис",
        food_state="cooked",
        match_method="EXACT_CANONICAL",
        match_confidence="EXACT",
    )

    assert resolve_authoritative_food_match(cooked) is None


def test_nutrient_per_100g_basis_source_and_external_id_retained():
    fact = facts_by_nutrient("rice")["energy_kcal"]

    assert fact.basis_amount == 100.0
    assert fact.basis_unit == "g"
    assert fact.source_id == "SRC-USDA-FDC"
    assert fact.fdc_id == 2512381
    assert fact.source_record_locator == "fdc:2512381"
    assert fact.food_state == "raw"


def test_missing_nutrient_remains_missing_and_never_zero():
    facts = facts_by_nutrient("salt")

    assert "energy_kcal" not in facts
    assert not has_complete_macro_facts("salt")
    assert facts["sodium_mg"].value == 38700.0


def test_nutrient_unit_retained():
    facts = facts_by_nutrient("chicken_egg")

    assert facts["energy_kcal"].unit == "kcal"
    assert facts["phenylalanine_mg"].unit == "mg"


def test_food_state_retained():
    fact = facts_by_nutrient("chicken_fillet")["protein_g"]

    assert fact.food_state == "raw"


def test_quantity_conversion_uses_only_valid_mass_conversion():
    converted = convert_quantity_to_fact_basis("0.5", "кг")

    assert converted["basis_conversion_status"] == "MASS_CONVERTED"
    assert converted["grams"] == 500


def test_count_without_evidence_remains_unresolved():
    converted = convert_quantity_to_fact_basis("1", "шт")

    assert converted["basis_conversion_status"] == "UNRESOLVED_WITHOUT_MASS"
    assert converted["grams"] is None


def test_household_measure_without_evidence_remains_unresolved():
    converted = convert_quantity_to_fact_basis("1", "ст.л.")

    assert converted["basis_conversion_status"] == "UNRESOLVED_WITHOUT_MASS"
    assert converted["grams"] is None


def test_partially_covered_recipe_is_not_fully_authoritative():
    result = simulate_recipe_computability(
        [
            {"id": 1, "recipe_id": 10, "name": "рис", "quantity": "100", "unit": "г"},
            {"id": 2, "recipe_id": 10, "name": "сыр", "quantity": "50", "unit": "г"},
        ]
    )

    recipe = result["recipe_records"][0]
    assert recipe["has_authoritative_contribution"] is True
    assert recipe["fully_authoritative_macro_computable"] is False


def test_fully_covered_recipe_requires_all_required_ingredients():
    result = simulate_recipe_computability(
        [
            {"id": 1, "recipe_id": 11, "name": "рис", "quantity": "100", "unit": "г"},
            {"id": 2, "recipe_id": 11, "name": "куриное филе", "quantity": "200", "unit": "г"},
        ]
    )

    recipe = result["recipe_records"][0]
    assert recipe["fully_authoritative_macro_computable"] is True


def test_phenylalanine_is_not_derived_from_protein():
    chicken = facts_by_nutrient("chicken_fillet")
    egg = facts_by_nutrient("chicken_egg")

    assert "phenylalanine_mg" not in chicken
    assert egg["phenylalanine_mg"].value == 660.0


def test_no_allergen_gf_or_medical_facts_generated():
    result = simulate_recipe_computability(
        [{"id": 1, "recipe_id": 12, "name": "яйцо куриное", "quantity": "50", "unit": "г"}]
    )

    assert validate_no_safety_fact_generation(result["ingredient_records"]) is True
    assert all("allergen" not in row for row in result["ingredient_records"])
    assert all("gluten" not in row for row in result["ingredient_records"])
    assert all("medical" not in row for row in result["ingredient_records"])


def test_no_production_mutation_path_introduced():
    facts = nutrient_facts_for_food("rice")

    assert facts
    assert all(fact.provenance_status == "external_verified" for fact in facts)
    assert all(fact.source_data_type == "Foundation" for fact in facts)
    assert set(AUTHORITATIVE_FOOD_MATCHES) >= {"rice", "chicken_fillet", "chicken_egg"}


@pytest.mark.parametrize("nutrient", MACRO_NUTRIENTS)
def test_complete_macro_foods_have_required_macro_nutrients(nutrient: str):
    assert facts_by_nutrient("rice")[nutrient].value is not None
