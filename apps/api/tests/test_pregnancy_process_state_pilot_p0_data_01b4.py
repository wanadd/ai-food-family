"""P0-DATA-FOUNDATION-01B4 pregnancy process-state pilot tests."""

from types import SimpleNamespace

from app.nutrition.medical_safety import evaluate_medical_safety
from app.services.nutrition.authoritative_food_nutrient_pilot import facts_by_nutrient
from app.services.nutrition.pregnancy_process_state_pilot import (
    extract_process_state_facts,
    legacy_or_ai_fact_for_review,
    represent_explicit_process_state,
    simulate_pregnancy_process_state,
)
from app.services.nutrition.structured_safety_facts_pilot import structured_facts_for_food


def _ingredient(row_id, recipe_id, name):
    return {"id": row_id, "recipe_id": recipe_id, "name": name}


def _step(recipe_id, step_number, text):
    return {"recipe_id": recipe_id, "step_number": step_number, "text": text}


def _pregnancy_profile():
    return SimpleNamespace(typed_medical_context=[{"condition_id": "pregnancy", "origin": "user_declared"}])


def test_explicit_raw_state_can_be_represented():
    fact = represent_explicit_process_state(process_state="raw", step_text="Подайте яйцо сырым.")
    assert fact.process_state == "raw"
    assert fact.state_dimension == "raw_undercooked_status"


def test_explicit_cooked_state_can_be_represented():
    fact = represent_explicit_process_state(process_state="cooked", step_text="Отварите яйцо вкрутую.")
    assert fact.process_state == "cooked"
    assert fact.accepted is True


def test_raw_undercooked_and_cooked_are_distinct():
    states = {
        represent_explicit_process_state(process_state="raw").process_state,
        represent_explicit_process_state(process_state="undercooked").process_state,
        represent_explicit_process_state(process_state="cooked").process_state,
    }
    assert states == {"raw", "undercooked", "cooked"}


def test_pasteurized_and_unpasteurized_are_distinct():
    pasteurized = represent_explicit_process_state(process_state="pasteurized", ingredient_name="молоко")
    unpasteurized = represent_explicit_process_state(process_state="unpasteurized", ingredient_name="молоко")
    assert pasteurized.process_state == "pasteurized"
    assert unpasteurized.process_state == "unpasteurized"
    assert pasteurized.state_dimension == "pasteurization_status"


def test_missing_pasteurization_remains_unknown():
    result = simulate_pregnancy_process_state(
        [{"id": 1, "title": "Каша"}],
        [_ingredient(1, 1, "молоко")],
        [_step(1, 1, "Смешайте молоко с крупой.")],
    )
    row = result["pregnancy_relevant_rows"][0]
    assert row["unknown_reason"] == "PASTEURIZATION_UNKNOWN"
    assert result["metrics"]["pasteurization_unknown"] == 1


def test_egg_identity_alone_does_not_imply_raw():
    result = simulate_pregnancy_process_state(
        [{"id": 1, "title": "Яйцо"}],
        [_ingredient(1, 1, "яйцо")],
        [],
    )
    assert result["metrics"]["verified_process_state_facts"] == 0
    assert result["pregnancy_relevant_rows"][0]["unknown_reason"] == "COOKING_COMPLETENESS_UNKNOWN"


def test_milk_identity_alone_does_not_imply_pasteurized():
    result = simulate_pregnancy_process_state(
        [{"id": 1, "title": "Молоко"}],
        [_ingredient(1, 1, "молоко")],
        [],
    )
    assert result["metrics"]["pasteurization_known"] == 0
    assert result["pregnancy_relevant_rows"][0]["sufficient_process_state"] is False


def test_fish_identity_alone_does_not_imply_raw():
    result = simulate_pregnancy_process_state(
        [{"id": 1, "title": "Рыба"}],
        [_ingredient(1, 1, "треска")],
        [],
    )
    assert result["metrics"]["heat_treatment_known"] == 0
    assert result["pregnancy_relevant_rows"][0]["unknown_reason"] == "COOKING_COMPLETENESS_UNKNOWN"


def test_recipe_level_cooking_verb_does_not_cook_every_ingredient():
    result = extract_process_state_facts(
        [_ingredient(1, 1, "яйцо"), _ingredient(2, 1, "молоко")],
        [_step(1, 1, "Приготовьте по классическому рецепту.")],
    )
    assert not [fact for fact in result["fact_objects"] if fact.accepted]
    assert result["fact_objects"][0].linkage_status == "RECIPE_LEVEL_PROCESS"


def test_explicit_ingredient_step_linkage_works():
    result = extract_process_state_facts(
        [_ingredient(1, 1, "яйцо")],
        [_step(1, 1, "Отварите яйцо вкрутую, остудите и очистите.")],
    )
    accepted = [fact for fact in result["fact_objects"] if fact.accepted]
    assert len(accepted) == 1
    assert accepted[0].ingredient_name == "яйцо"
    assert accepted[0].process_state == "cooked"


def test_ambiguous_linkage_remains_unresolved():
    result = extract_process_state_facts(
        [_ingredient(1, 1, "яйцо"), _ingredient(2, 1, "молоко")],
        [_step(1, 1, "Запекайте в духовке около 30 минут.")],
    )
    assert not [fact for fact in result["fact_objects"] if fact.accepted]
    assert result["fact_objects"][0].linkage_status == "AMBIGUOUS_LINK"


def test_legacy_keyword_alone_cannot_create_verified_fact():
    fact = legacy_or_ai_fact_for_review(origin="LEGACY_TEXT_SIGNAL")
    assert fact.accepted is False
    assert fact.verification_status == "review_required"


def test_ai_derived_state_alone_cannot_create_verified_fact():
    fact = legacy_or_ai_fact_for_review(origin="AI_DERIVED")
    assert fact.accepted is False
    assert fact.provenance_status == "needs_review"


def test_provenance_retained():
    fact = represent_explicit_process_state(process_state="cooked").to_record()
    assert fact["source_id"] == "SRC-PLANAM-SAFETY-POLICY"
    assert fact["source_record_locator"].startswith("recipe_step:")
    assert fact["text_hash"]


def test_review_required_evidence_cannot_masquerade_as_verified():
    fact = legacy_or_ai_fact_for_review(origin="LEGACY_TEXT_SIGNAL")
    record = fact.to_record()
    assert record["accepted_for_p0_e_simulation"] is False
    assert record["verification_status"] == "review_required"


def test_unknown_remains_unknown_in_pregnancy_simulation():
    decisions = evaluate_medical_safety(SimpleNamespace(), _pregnancy_profile())
    assert decisions[0].decision_class == "UNKNOWN"


def test_existing_p0_e_decision_semantics_unchanged():
    profile = _pregnancy_profile()
    unsafe = evaluate_medical_safety(
        SimpleNamespace(
            pasteurization_status="unknown",
            raw_undercooked_status="raw",
            process_state="known",
        ),
        profile,
    )
    warning = evaluate_medical_safety(
        SimpleNamespace(
            pasteurization_status="pasteurized",
            raw_undercooked_status="cooked",
            process_state="known",
        ),
        profile,
    )
    assert unsafe[0].decision_class == "BLOCK"
    assert warning[0].decision_class == "WARN"


def test_allergen_celiac_semantics_unchanged():
    facts = structured_facts_for_food("chicken_egg")
    assert facts[0].concept_id == "egg"
    assert facts[0].relation_type == "contains"


def test_nutrient_pipeline_unchanged():
    facts = facts_by_nutrient("rice")
    assert facts["energy_kcal"].value == 357.0


def test_no_db_mutation_path_introduced():
    result = simulate_pregnancy_process_state(
        [{"id": 1, "title": "Яйцо"}],
        [_ingredient(1, 1, "яйцо")],
        [_step(1, 1, "Отварите яйцо вкрутую.")],
    )
    assert "process_state_facts" in result
    assert "mutation" not in result
