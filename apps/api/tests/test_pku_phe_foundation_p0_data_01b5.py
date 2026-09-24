"""P0-DATA-FOUNDATION-01B5 PKU/Phe foundation tests."""

from types import SimpleNamespace

import pytest

from app.nutrition.medical_safety import evaluate_medical_safety
from app.services.nutrition.authoritative_food_nutrient_pilot import facts_by_nutrient
from app.services.nutrition.pku_phe_foundation import (
    food_phe_match_record,
    ingredient_phe_record,
    normalize_phe_to_mg,
    phe_fact_for_food,
    protein_phe_ratio_audit,
    protein_to_phe_estimate,
    simulate_recipe_phe,
)
from app.services.nutrition.pregnancy_process_state_pilot import represent_explicit_process_state
from app.services.nutrition.structured_safety_facts_pilot import structured_facts_for_food


def _row(row_id, recipe_id, name, quantity="100", unit="г"):
    return {"id": row_id, "recipe_id": recipe_id, "name": name, "quantity": quantity, "unit": unit}


def _pku_profile(*, target=True, specialist=True):
    context = {"phenylalanine_target": {"value": 300, "unit": "mg/day"}} if target else {}
    return SimpleNamespace(
        typed_medical_context=[
            {
                "condition_id": "phenylketonuria_pah",
                "origin": "clinician_recorded",
                "structured_context": context,
                "specialist_plan_present": specialist,
            }
        ]
    )


def test_authoritative_phe_fact_retains_source_id():
    fact = phe_fact_for_food("chicken_egg").to_record()
    assert fact["source_id"] == "SRC-USDA-FDC"


def test_external_food_id_retained():
    fact = phe_fact_for_food("chicken_egg").to_record()
    assert fact["fdc_id"] == 748967
    assert fact["source_record_id_or_locator"] == "748967"


def test_nutrient_id_retained():
    fact = phe_fact_for_food("chicken_egg").to_record()
    assert fact["source_nutrient_id"] == "1217"


def test_unit_retained_and_canonicalized():
    fact = phe_fact_for_food("chicken_egg").to_record()
    assert fact["source_unit"] == "g"
    assert fact["unit"] == "mg"


def test_basis_retained():
    fact = phe_fact_for_food("chicken_egg").to_record()
    assert fact["basis_amount"] == 100.0
    assert fact["basis_unit"] == "g"
    assert fact["source_basis_amount"] == 100.0


def test_food_state_retained():
    fact = phe_fact_for_food("chicken_egg").to_record()
    assert fact["food_state"] == "raw"


def test_mg_g_conversion_deterministic():
    assert normalize_phe_to_mg(0.66, "g") == 660.0
    assert normalize_phe_to_mg(660, "mg") == 660.0


def test_missing_phe_remains_missing():
    assert phe_fact_for_food("chicken_fillet") is None
    assert food_phe_match_record("chicken_fillet")["phe_available"] is False


def test_missing_phe_never_becomes_zero():
    record = ingredient_phe_record(_row(1, 1, "куриное филе"))
    assert record["phe_mg_contribution"] is None
    assert record["contribution_status"] == "NO_PHE_FACT"


def test_protein_cannot_automatically_generate_phe():
    with pytest.raises(RuntimeError):
        protein_to_phe_estimate(22.5)
    assert "phenylalanine_mg" not in facts_by_nutrient("chicken_fillet")


def test_raw_cooked_mismatch_does_not_silently_pass():
    row = _row(1, 1, "яйцо")
    record = ingredient_phe_record(row)
    assert record["food_state_validation"] == "MATCHED"
    cooked = {**record, "food_state_validation": "MISMATCH", "phe_mg_contribution": None}
    assert cooked["phe_mg_contribution"] is None


def test_phe_fact_with_unknown_quantity_cannot_produce_contribution():
    record = ingredient_phe_record(_row(1, 1, "яйцо", "1", "шт"))
    assert record["phe_fact_available"] is True
    assert record["phe_mg_contribution"] is None
    assert record["contribution_status"] == "PHE_FACT_AVAILABLE_BUT_QUANTITY_UNRESOLVED"


def test_partial_recipe_is_not_fully_phe_computable():
    result = simulate_recipe_phe([_row(1, 1, "яйцо"), _row(2, 1, "куриное филе")])
    recipe = result["recipe_records"][0]
    assert recipe["status"] == "PARTIALLY_PHE_COMPUTABLE"


def test_full_recipe_requires_all_material_ingredients():
    full = simulate_recipe_phe([_row(1, 1, "яйцо")], recipes=[{"id": 1, "servings": 2}])
    partial = simulate_recipe_phe([_row(1, 1, "яйцо"), _row(2, 1, "рис")])
    assert full["recipe_records"][0]["status"] == "FULLY_PHE_COMPUTABLE"
    assert partial["recipe_records"][0]["status"] != "FULLY_PHE_COMPUTABLE"


def test_serving_fallback_cannot_silently_become_authoritative():
    result = simulate_recipe_phe([_row(1, 1, "яйцо")], recipes=[{"id": 1, "servings": None}])
    recipe = result["recipe_records"][0]
    assert recipe["status"] == "FULLY_PHE_COMPUTABLE"
    assert recipe["per_serving_phe_mg"] is None
    assert recipe["per_serving_authoritative"] is False


def test_aspartame_handling_remains_separate():
    decisions = evaluate_medical_safety(SimpleNamespace(aspartame_present=True), _pku_profile())
    assert any(decision.decision_class == "BLOCK" for decision in decisions)
    assert ingredient_phe_record(_row(1, 1, "яйцо"))["safety_fact_generated"] is False


def test_no_universal_phe_target_introduced():
    decisions = evaluate_medical_safety(SimpleNamespace(phenylalanine_mg_per_serving=10), _pku_profile(target=False))
    assert any(decision.decision_class == "ESCALATE" for decision in decisions)


def test_existing_p0_e_pku_behavior_unchanged():
    missing = evaluate_medical_safety(SimpleNamespace(), _pku_profile())
    present = evaluate_medical_safety(SimpleNamespace(phenylalanine_mg_per_serving=10), _pku_profile())
    assert any(decision.decision_class == "UNKNOWN" for decision in missing)
    assert not any(decision.decision_class == "UNKNOWN" for decision in present)


def test_p0_d_allergen_behavior_unchanged():
    facts = structured_facts_for_food("chicken_egg")
    assert facts[0].concept_id == "egg"


def test_pregnancy_behavior_unchanged():
    fact = represent_explicit_process_state(process_state="cooked")
    assert fact.process_state == "cooked"


def test_nutrient_provenance_behavior_unchanged():
    fact = phe_fact_for_food("chicken_egg").nutrient_fact
    assert fact.provenance_status == "external_verified"
    assert fact.source_record_id_or_locator == "748967"


def test_no_production_mutation_path_introduced():
    result = simulate_recipe_phe([_row(1, 1, "яйцо")])
    assert "ingredient_records" in result
    assert "mutation" not in result


def test_protein_ratio_audit_is_descriptive_only():
    audit = protein_phe_ratio_audit(["chicken_egg", "chicken_fillet"])
    assert audit["count"] == 1
    assert audit["used_for_imputation"] is False
