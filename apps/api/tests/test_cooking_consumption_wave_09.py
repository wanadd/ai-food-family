from app.cooking.v2_contracts import CookingBatchV2, ConsumptionEventV2, actual_substitution_changes_safety_input, ai_food_report_is_authoritative, cooking_completion_creates_consumption, recipe_instruction_is_cooking_proof

def test_recipe_instruction_is_not_observed_cooking():
    assert not recipe_instruction_is_cooking_proof("cook for 20 minutes")

def test_cooking_and_consumption_are_separate():
    batch = CookingBatchV2("batch", "version", "slot", "COMPLETED")
    assert not cooking_completion_creates_consumption(batch)

def test_consumption_is_person_scoped_and_unknown_portion_is_preserved():
    event = ConsumptionEventV2("person", "EXTERNAL_MEAL")
    assert event.person_id == "person"
    assert event.portion_state == "UNKNOWN"

def test_ai_report_is_proposal_and_substitution_changes_safety_input():
    assert not ai_food_report_is_authoritative({"food": "milk"})
    assert actual_substitution_changes_safety_input({"actual_product_instance_id": "product"})
