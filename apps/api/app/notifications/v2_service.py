from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import and_, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.notifications.v2_models import Job, NotificationDelivery, NotificationIntent, NotificationPreference, OutboxEvent
from app.v2.authorization import AuthorizedContext, authorized_context
from app.v2.errors import error

UTC = timezone.utc


def request_hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    return hashlib.sha256(encoded).hexdigest()


def authorize_subject(
    db: Session,
    *,
    context: AuthorizedContext,
    subject_kind: str,
    subject_id: str,
    authorization: str | None = None,
    session_token: str | None = None,
) -> AuthorizedContext:
    if subject_kind not in {"PERSON", "HOUSEHOLD"}:
        raise error("validation_error", 422, details={"subject_kind": "must be PERSON or HOUSEHOLD"})
    try:
        return authorized_context(
            db,
            authorization=authorization,
            x_planam_session=session_token,
            x_person_id=subject_id if subject_kind == "PERSON" else None,
            x_household_id=subject_id if subject_kind == "HOUSEHOLD" else None,
            required_capability="notification.preference.write",
        )
    except Exception:
        # The current actor's own person is valid even when no explicit grant row exists.
        if subject_kind == "PERSON" and context.actor_person and context.actor_person.person_id == subject_id:
            return context
        raise


def upsert_preference(
    db: Session,
    *,
    context: AuthorizedContext,
    subject_kind: str,
    subject_id: str,
    channel: str,
    enabled: bool,
    timezone_name: str | None,
    quiet_hours_start: str | None,
    quiet_hours_end: str | None,
    idempotency_key: str,
) -> NotificationPreference:
    payload = {
        "subject_kind": subject_kind,
        "subject_id": subject_id,
        "channel": channel,
        "enabled": enabled,
        "timezone": timezone_name,
        "quiet_hours_start": quiet_hours_start,
        "quiet_hours_end": quiet_hours_end,
    }
    fingerprint = request_hash(payload)
    existing = (
        db.query(NotificationPreference)
        .filter(
            NotificationPreference.subject_kind == subject_kind,
            NotificationPreference.subject_id == subject_id,
            NotificationPreference.channel == channel,
            NotificationPreference.idempotency_key == idempotency_key,
        )
        .first()
    )
    if existing is not None:
        if existing.request_hash != fingerprint:
            raise error("idempotency_conflict", 409)
        return existing
    row = (
        db.query(NotificationPreference)
        .filter(
            NotificationPreference.subject_kind == subject_kind,
            NotificationPreference.subject_id == subject_id,
            NotificationPreference.channel == channel,
        )
        .with_for_update()
        .first()
    )
    if row is None:
        row = NotificationPreference(
            preference_id=str(uuid.uuid4()),
            subject_kind=subject_kind,
            subject_id=subject_id,
            channel=channel,
            enabled=enabled,
            timezone=timezone_name,
            quiet_hours_start=quiet_hours_start,
            quiet_hours_end=quiet_hours_end,
            idempotency_key=idempotency_key,
            request_hash=fingerprint,
        )
        db.add(row)
    else:
        row.enabled = enabled
        row.timezone = timezone_name
        row.quiet_hours_start = quiet_hours_start
        row.quiet_hours_end = quiet_hours_end
        row.idempotency_key = idempotency_key
        row.request_hash = fingerprint
    return row


def create_notification_intent(
    db: Session,
    *,
    owner_domain: str,
    aggregate_id: str,
    intent_type: str,
    subject_kind: str,
    subject_id: str,
    idempotency_key: str,
    payload: dict[str, Any] | None = None,
    navigation: dict[str, Any] | None = None,
    recipient_person_id: str | None = None,
    recipient_household_id: str | None = None,
) -> NotificationIntent:
    existing = db.query(NotificationIntent).filter_by(
        owner_domain=owner_domain,
        aggregate_id=aggregate_id,
        intent_type=intent_type,
        idempotency_key=idempotency_key,
    ).first()
    if existing is not None:
        return existing
    intent = NotificationIntent(
        intent_id=str(uuid.uuid4()), owner_domain=owner_domain, aggregate_id=aggregate_id,
        intent_type=intent_type, subject_kind=subject_kind, subject_id=subject_id,
        recipient_person_id=recipient_person_id, recipient_household_id=recipient_household_id,
        payload_json=payload or {}, navigation_json=navigation or {}, idempotency_key=idempotency_key,
    )
    db.add(intent)
    db.flush()
    db.add(OutboxEvent(
        outbox_event_id=str(uuid.uuid4()), aggregate_id=aggregate_id,
        event_kind="notification.intent.created", payload_json={"intent_id": intent.intent_id},
        idempotency_key=idempotency_key,
    ))
    db.add(Job(
        job_id=str(uuid.uuid4()), kind="notification.delivery", idempotency_key=f"intent:{intent.intent_id}",
        payload_json={"intent_id": intent.intent_id},
    ))
    return intent


def claim_job(db: Session, *, worker_id: str, lease_seconds: int = 60) -> Job | None:
    now = datetime.now(UTC)
    job = (
        db.query(Job)
        .filter(
            or_(
                and_(Job.state.in_(["pending", "retryable"]), Job.available_at <= now),
                and_(Job.state == "leased", Job.lease_until < now),
            )
        )
        .order_by(Job.available_at, Job.created_at)
        .with_for_update(skip_locked=True)
        .first()
    )
    if job is None:
        return None
    job.state = "leased"
    job.lease_owner = worker_id
    job.lease_until = now + timedelta(seconds=lease_seconds)
    job.attempt_count += 1
    db.commit()
    return job


def finish_job(db: Session, job_id: str, *, success: bool, retryable: bool = False, error_code: str | None = None, error_message: str | None = None) -> Job | None:
    job = db.get(Job, job_id)
    if job is None:
        return None
    job.state = "succeeded" if success else "retryable" if retryable and (job.max_attempts is None or job.attempt_count < job.max_attempts) else "dead-letter"
    job.lease_owner = None
    job.lease_until = None
    job.last_error_code = error_code
    job.last_error_message = error_message[:500] if error_message else None
    if job.state == "retryable":
        job.available_at = datetime.now(UTC) + timedelta(seconds=min(300, 2 ** min(job.attempt_count, 8)))
    db.commit()
    return job


def create_delivery(db: Session, intent: NotificationIntent, *, channel: str, provider: str, provider_subject: str, delivery_key: str) -> NotificationDelivery:
    existing = db.query(NotificationDelivery).filter_by(delivery_key=delivery_key).first()
    if existing is not None:
        return existing
    row = NotificationDelivery(
        delivery_id=str(uuid.uuid4()), intent_id=intent.intent_id, channel=channel,
        provider=provider, provider_subject=provider_subject, delivery_key=delivery_key,
    )
    db.add(row)
    db.flush()
    return row
