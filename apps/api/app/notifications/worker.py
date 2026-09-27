"""Post-commit notification worker primitives.

The provider call is intentionally outside the claim and result transactions.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.notifications.delivery import DeliveryRouter
from app.core.models import CoreAccount, ExternalIdentity
from app.notifications.v2_models import NotificationIntent
from app.notifications.v2_service import claim_job, create_delivery, finish_job


async def process_one_notification_job(db: Session, *, worker_id: str, router: DeliveryRouter) -> bool:
    job = claim_job(db, worker_id=worker_id)
    if job is None:
        return False
    intent_id = (job.payload_json or {}).get("intent_id")
    intent = db.get(NotificationIntent, intent_id)
    if intent is None:
        finish_job(db, job.job_id, success=False, error_code="intent_missing", error_message="Notification intent is missing")
        return True
    payload: dict[str, Any] = dict(intent.payload_json or {})
    provider = str(payload.get("provider", "telegram"))
    destination = ""
    if provider == "telegram" and intent.recipient_person_id:
        identity = db.query(ExternalIdentity).filter(
            ExternalIdentity.account_id.in_(
                db.query(CoreAccount.account_id).filter(CoreAccount.primary_person_id == intent.recipient_person_id)
            ),
            ExternalIdentity.provider == "telegram",
            ExternalIdentity.status == "active",
        ).first()
        if identity is not None:
            destination = identity.provider_subject
    if not destination:
        finish_job(db, job.job_id, success=False, error_code="recipient_missing", error_message="Provider destination is missing")
        return True
    delivery = create_delivery(
        db, intent, channel=str(payload.get("channel", "telegram")), provider=provider,
        provider_subject=destination, delivery_key=f"{intent.intent_id}:{provider}:{destination}",
    )
    db.commit()
    result = await router.deliver(provider=provider, destination=destination, payload=payload)
    delivery = db.get(type(delivery), delivery.delivery_id)
    if delivery is not None:
        delivery.attempt_count += 1
        delivery.last_attempt_at = datetime.now(timezone.utc)
        delivery.state = "succeeded" if result.success else "retryable" if result.retryable else "failed"
        delivery.provider_message_id = result.provider_message_id
        delivery.provider_metadata_json = result.provider_metadata or {}
        delivery.last_error_code = result.error_code
        delivery.last_error_message = result.error_message
        db.commit()
    finish_job(db, job.job_id, success=result.success, retryable=result.retryable, error_code=result.error_code, error_message=result.error_message)
    return True
