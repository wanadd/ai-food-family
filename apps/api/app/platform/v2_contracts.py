from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime

@dataclass(frozen=True)
class NotificationIntentV2:
    dedupe_key: str
    intent_type: str
    source_domain: str
    recipient_person_id: str | None = None
    household_id: str | None = None

def delivery_is_allowed(preference_status: str, now: datetime | None = None, quiet_until: datetime | None = None) -> bool:
    return preference_status == "ALLOWED" and (quiet_until is None or now is None or now >= quiet_until)

def entitlement_capability(namespace: str, capability: str) -> str:
    return f"{namespace}.{capability}"

def food_depends_on_plan_name(_: str) -> bool:
    return False

@dataclass(frozen=True)
class DurableJobV2:
    job_type: str
    idempotency_key: str
    attempts: int = 0
    max_attempts: int = 5
    status: str = "PENDING"

def retry_status(attempts: int, max_attempts: int, retryable: bool) -> str:
    if not retryable:
        return "DEAD"
    return "RETRY" if attempts < max_attempts else "DEAD"

def job_payload_is_minimized(payload: dict) -> bool:
    return not any(key in payload for key in ("raw_receipt_image", "full_profile", "raw_voice"))

def outbox_marks_delivered_after_success(external_success: bool) -> bool:
    return external_success
