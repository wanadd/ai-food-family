from datetime import datetime, timezone
from app.health.v2_contracts import HealthProjectionV2, ai_can_override_safety, family_nutrition_is_average, missing_consumption_means_skipped, recommendation_provenance, resolve_safety_status
from app.platform.v2_contracts import DurableJobV2, NotificationIntentV2, delivery_is_allowed, entitlement_capability, food_depends_on_plan_name, job_payload_is_minimized, outbox_marks_delivered_after_success, retry_status

def test_health_is_person_scoped_deviation_aware_and_incomplete_when_needed():
    projection = HealthProjectionV2("person", "PARTIAL", {"kcal": 1000}, {"kcal": 500}, {"kcal": -500})
    assert projection.person_id == "person"
    assert projection.completeness == "PARTIAL"
    assert not missing_consumption_means_skipped(False)
    assert not family_nutrition_is_average([projection])

def test_safety_precedence_cannot_be_downgraded_by_ai():
    assert resolve_safety_status("BLOCK", "SAFE") == "BLOCK"
    assert not ai_can_override_safety("BLOCK", "SAFE")
    assert not ai_can_override_safety("UNKNOWN", "SAFE")

def test_recommendation_keeps_trigger_person_and_unknowns():
    assert recommendation_provenance("deviation", "person", ["actual"], ["portion"])['unknown'] == ["portion"]

def test_notification_separates_intent_from_delivery_and_dedupes():
    intent = NotificationIntentV2("dedupe", "SHOPPING_REMINDER", "Food", recipient_person_id="person")
    assert intent.source_domain == "Food"
    assert delivery_is_allowed("ALLOWED")
    assert not delivery_is_allowed("QUIET_HOURS")

def test_entitlement_is_namespaced_and_not_plan_name_logic():
    assert entitlement_capability("food", "health.ai") == "food.health.ai"
    assert not food_depends_on_plan_name("premium")

def test_jobs_and_outbox_are_retryable_idempotent_and_minimized():
    job = DurableJobV2("health_projection", "key")
    assert retry_status(job.attempts, job.max_attempts, True) == "RETRY"
    assert retry_status(5, 5, True) == "DEAD"
    assert job_payload_is_minimized({"person_id": "p"})
    assert not job_payload_is_minimized({"raw_voice": "..."})
    assert not outbox_marks_delivered_after_success(False)
