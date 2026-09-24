from datetime import datetime, timedelta, timezone

from app.cooking.v2_contracts import (
    CookingBatchV2,
    ConsumptionEventV2,
    cooking_completion_creates_consumption,
    recipe_instruction_is_cooking_proof,
)
from app.health.v2_contracts import (
    HealthProjectionV2,
    ai_can_override_safety,
    recommendation_provenance,
)
from app.platform.v2_contracts import (
    DurableJobV2,
    NotificationIntentV2,
    delivery_is_allowed,
    job_payload_is_minimized,
    outbox_marks_delivered_after_success,
    retry_status,
)
from app.shopping.v2_contracts import (
    PantryMovementV2,
    ReceiptProposalV2,
    ShoppingDemandV2,
    ocr_is_verified_purchase,
)


def test_run_b_operational_chain_preserves_provenance_and_person_scope():
    person_id = "person-1"
    household_id = "household-1"
    evidence_id = "evidence-1"
    recipe_version_id = "recipe-version-1"
    plan_slot_id = "plan-slot-1"

    demand = ShoppingDemandV2(
        display_text="milk",
        quantity=1,
        unit="L",
        source_kind="PLAN",
        plan_revision_id="plan-revision-1",
        plan_slot_id=plan_slot_id,
        recipe_version_id=recipe_version_id,
        participant_person_id=person_id,
        product_requirement={"food_identity_key": "milk"},
    )
    proposal = ReceiptProposalV2(extraction_kind="OCR", confidence="HIGH")
    assert demand.recipe_version_id == recipe_version_id
    assert proposal.verified is False
    assert not ocr_is_verified_purchase(proposal)

    verified = ReceiptProposalV2(
        extraction_kind="OCR",
        status="VERIFIED",
        confidence="HIGH",
        verified=True,
    )
    assert ocr_is_verified_purchase(verified)
    pantry_movement = PantryMovementV2("PURCHASE", 1, "receipt-1:line-1")
    assert pantry_movement.idempotency_key.startswith("receipt-1")

    batch = CookingBatchV2(
        "batch-1",
        recipe_version_id=recipe_version_id,
        plan_slot_id=plan_slot_id,
        status="COMPLETED",
        actual_product_instance_ids=("product-instance-1",),
        substitutions=({"actual_food_identity_key": "oat-milk"},),
    )
    assert not recipe_instruction_is_cooking_proof("cook thoroughly")
    assert not cooking_completion_creates_consumption(batch)

    consumption = ConsumptionEventV2(
        person_id=person_id,
        source_kind="OBSERVED",
        status="CONFIRMED",
        actual_portion=1,
        actual_portion_unit="serving",
        nutrition_state="PARTIAL",
        provenance={"cooking_batch_id": batch.cooking_batch_id, "evidence_id": evidence_id},
    )
    projection = HealthProjectionV2(
        person_id=person_id,
        completeness="PARTIAL",
        planned={"plan_slot_id": plan_slot_id},
        actual={"consumption_event_id": "consumption-1", "nutrition_state": consumption.nutrition_state},
        safety_status="BLOCK",
    )
    assert projection.person_id == person_id
    assert projection.completeness == "PARTIAL"
    assert ai_can_override_safety("BLOCK", "SAFE") is False

    intent = NotificationIntentV2(
        dedupe_key="health:person-1:2026-09-24",
        intent_type="HEALTH_REVIEW",
        source_domain="health",
        recipient_person_id=person_id,
        household_id=household_id,
    )
    quiet_until = datetime.now(timezone.utc) + timedelta(hours=1)
    assert intent.recipient_person_id == person_id
    assert delivery_is_allowed("ALLOWED", datetime.now(timezone.utc), quiet_until) is False

    job = DurableJobV2("notification.deliver", intent.dedupe_key)
    assert job_payload_is_minimized({"intent_id": intent.dedupe_key})
    assert retry_status(1, job.max_attempts, True) == "RETRY"
    assert outbox_marks_delivered_after_success(True)
    assert recommendation_provenance("health_projection", person_id, [evidence_id], ["missing_nutrient"])["person_id"] == person_id


def test_run_b_negative_cases_do_not_promote_plans_or_proposals_to_facts():
    planned_batch = CookingBatchV2("planned-only", status="PLANNED")
    assert not cooking_completion_creates_consumption(planned_batch)
    assert not recipe_instruction_is_cooking_proof("cook thoroughly")

    unverified = ReceiptProposalV2(extraction_kind="OCR", status="REVIEW_REQUIRED")
    assert not ocr_is_verified_purchase(unverified)

    unknown_consumption = ConsumptionEventV2(person_id="person-1", source_kind="PLANNED")
    projection = HealthProjectionV2(
        person_id="person-1",
        completeness="UNKNOWN",
        actual={"consumption_event_id": None, "nutrition_state": unknown_consumption.nutrition_state},
        safety_status="UNKNOWN",
    )
    assert projection.completeness == "UNKNOWN"
    assert unknown_consumption.nutrition_state == "UNKNOWN"
    assert ai_can_override_safety("UNKNOWN", "SAFE") is False
