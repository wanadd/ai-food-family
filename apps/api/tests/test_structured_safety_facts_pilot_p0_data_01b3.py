from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

API_DIR = Path(__file__).resolve().parents[1]
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

from app.nutrition.allergen_ontology import AllergenFact, decide_celiac_gluten_free
from app.nutrition.medical_safety import evaluate_medical_safety
from app.services.nutrition.authoritative_food_nutrient_pilot import facts_by_nutrient
from app.services.nutrition.structured_safety_facts_pilot import (
    SOURCE_STRATEGY,
    classify_pilot_food,
    ingredient_safety_record,
    product_label_future_contract,
    simulate_structured_safety,
    structured_facts_for_food,
)


def _recipe(**kwargs):
    return SimpleNamespace(
        ingredients=kwargs.get("ingredients", []),
        allergen_facts=kwargs.get("allergen_facts", []),
        gluten_free_status=kwargs.get("gluten_free_status"),
        gluten_free_provenance_status=kwargs.get("gluten_free_provenance_status"),
        medical_safety_facts_json=kwargs.get("medical_safety_facts_json"),
    )


def test_peanut_identity_produces_contains_only_from_accepted_mapping():
    facts = structured_facts_for_food("peanut")

    assert len(facts) == 1
    assert facts[0].concept_id == "peanut"
    assert facts[0].relation_type == "contains"
    assert facts[0].verification_status == "curated_reviewed"
    assert structured_facts_for_food("unknown_peanut_candidate") == ()


def test_milk_allergen_distinct_from_lactose_intolerance():
    facts = structured_facts_for_food("milk")

    assert [fact.concept_id for fact in facts] == ["milk_protein"]
    assert all(fact.concept_id != "lactose_intolerance" for fact in facts)


def test_peanut_remains_distinct_from_tree_nut():
    facts = structured_facts_for_food("peanut")

    assert {fact.concept_id for fact in facts} == {"peanut"}
    assert "tree_nut" not in {fact.concept_id for fact in facts}


def test_fish_crustacean_mollusc_remain_distinct():
    assert {fact.concept_id for fact in structured_facts_for_food("cod")} == {"fish"}
    assert {fact.concept_id for fact in structured_facts_for_food("shrimp")} == {"crustacean"}
    assert structured_facts_for_food("mollusc_generic") == ()


def test_wheat_gluten_relationship_is_typed():
    record = ingredient_safety_record({"id": 1, "recipe_id": 1, "name": "мука пшеничная"})

    assert record["canonical_food_key"] == "wheat_flour"
    assert record["gluten_facts"][0]["concept_id"] == "wheat"
    assert record["gluten_facts"][0]["relation_type"] == "contains"


def test_generic_oats_do_not_become_verified_gf():
    record = ingredient_safety_record({"id": 1, "recipe_id": 1, "name": "хлопья овсяные"})

    assert record["canonical_food_key"] == "oat_flakes"
    assert record["verified_gf_product"] is False
    assert record["allergen_facts"] == []


def test_naturally_gf_food_does_not_become_verified_gf_product():
    record = ingredient_safety_record({"id": 1, "recipe_id": 1, "name": "рис"})

    assert record["naturally_gf_candidate"] is True
    assert record["verified_gf_product"] is False


def test_generic_packaged_composite_without_composition_remains_unresolved():
    record = ingredient_safety_record({"id": 1, "recipe_id": 1, "name": "соус"})

    assert record["pilot_classification"] == "NEEDS_COMPOSITION"
    assert record["unresolved"] is True


def test_unknown_ingredient_prevents_false_recipe_safe_inference():
    result = simulate_structured_safety(
        [{"id": 1, "recipe_id": 1, "name": "неизвестный продукт"}]
    )

    assert result["recipe_allergen_records"][0]["safe_claim_generated"] is False
    assert result["recipe_allergen_records"][0]["complete_relevant_identity_coverage"] is False


def test_positive_ingredient_relation_propagates_to_recipe_dry_run():
    result = simulate_structured_safety(
        [{"id": 1, "recipe_id": 1, "name": "яйцо куриное"}]
    )

    recipe = result["recipe_allergen_records"][0]
    assert "egg" in recipe["aggregated_positive_relations"]
    assert recipe["safe_claim_generated"] is False


def test_absence_of_positive_facts_does_not_generate_negative_facts():
    result = simulate_structured_safety([{"id": 1, "recipe_id": 1, "name": "рис"}])

    assert result["ingredient_records"][0]["allergen_facts"] == []
    assert result["recipe_allergen_records"][0]["aggregated_positive_relations"] == {}


def test_may_contain_remains_distinct_from_contains():
    fact = AllergenFact("peanut", "may_contain", "product_label")

    assert fact.relation_type == "may_contain"
    assert fact.relation_type != "contains"


def test_cross_contact_remains_distinct():
    fact = AllergenFact("wheat", "cross_contact", "product_label")

    assert fact.relation_type == "cross_contact"
    assert fact.relation_type != "contains"


def test_keyword_only_evidence_is_not_verified():
    record = ingredient_safety_record({"id": 1, "recipe_id": 1, "name": "орехи"})

    assert record["pilot_classification"] in {"AMBIGUOUS_IDENTITY", "REVIEW_REQUIRED"}
    assert record["allergen_facts"] == []


def test_tag_only_gf_is_not_verified():
    result = simulate_structured_safety(
        [{"id": 1, "recipe_id": 1, "name": "рис"}],
        recipe_tags={1: ["gluten_free"]},
    )

    assert result["recipe_celiac_records"][0]["verified_gf"] is False
    assert result["recipe_celiac_records"][0]["legacy_tag_status"] == "TAG_UNVERIFIED"


def test_legacy_conflict_is_surfaced():
    result = simulate_structured_safety(
        [{"id": 1, "recipe_id": 1, "name": "мука пшеничная"}],
        recipe_tags={1: ["gluten_free"]},
    )

    assert result["metrics"]["legacy_conflicts"] == 1
    assert result["legacy_comparisons"][0]["comparison"] == "CONFLICTS"


def test_provenance_retained():
    fact = structured_facts_for_food("chicken_egg")[0].to_record()

    assert fact["source_id"] == "SRC-PLANAM-SAFETY-POLICY"
    assert fact["source_role"] == "PRIMARY"
    assert fact["source_record_locator"]


def test_review_required_source_cannot_produce_verified_claim():
    strategy = SOURCE_STRATEGY["clinical_review_required"]

    assert strategy["verification_status"] == "REVIEW_REQUIRED"
    assert not structured_facts_for_food("clinical_food_allergy_review_only")


def test_no_nutrient_behavior_regresses():
    assert facts_by_nutrient("rice")["energy_kcal"].basis_amount == 100.0


def test_no_medical_behavior_regresses():
    decisions = evaluate_medical_safety(
        _recipe(),
        SimpleNamespace(
            typed_medical_context=[
                {
                    "condition_id": "phenylketonuria_pah",
                    "origin": "clinician_recorded",
                    "provenance_status": "clinician_recorded",
                    "specialist_plan_present": True,
                    "structured_context": {"phenylalanine_target": {"value": 300, "unit": "mg/day"}},
                }
            ]
        ),
    )

    assert any(decision.decision_class == "UNKNOWN" for decision in decisions)


def test_product_label_future_contract_is_design_only():
    contract = product_label_future_contract()

    assert "gtin_or_barcode" in contract
    assert "verification_status" in contract
