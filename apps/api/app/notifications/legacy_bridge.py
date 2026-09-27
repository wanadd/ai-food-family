"""Bounded bridge from legacy notification producers to canonical W7 work."""
from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.orm import Session
from sqlalchemy import inspect

from app.core.models import CoreAccount, CorePerson, ExternalIdentity
from app.models.user import User
from app.notifications.v2_service import create_notification_intent


def canonical_person_for_legacy_user(db: Session, user: User) -> CorePerson | None:
    if not user.telegram_id:
        return None
    identity = (
        db.query(ExternalIdentity)
        .filter(
            ExternalIdentity.provider == "telegram",
            ExternalIdentity.provider_subject == str(user.telegram_id),
            ExternalIdentity.status == "active",
        )
        .one_or_none()
    )
    if identity is None:
        return None
    account = db.get(CoreAccount, identity.account_id)
    if account is None or account.status != "active" or not account.primary_person_id:
        return None
    return db.get(CorePerson, account.primary_person_id)


def enqueue_legacy_notification(
    db: Session,
    user: User,
    *,
    intent_type: str,
    occurrence_key: str,
    text: str,
    navigation: dict[str, Any] | None = None,
    channel: str = "telegram",
) -> bool:
    """Create canonical durable work; never resolve or call a provider here."""
    if db.bind is None or not inspect(db.bind).has_table("notification_intents"):
        return False
    person = canonical_person_for_legacy_user(db, user)
    if person is None:
        return False
    aggregate_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"planam:legacy-notification:{user.id}:{occurrence_key}"))
    create_notification_intent(
        db,
        owner_domain="legacy_notification_compatibility",
        aggregate_id=aggregate_id,
        intent_type=intent_type,
        subject_kind="PERSON",
        subject_id=person.person_id,
        recipient_person_id=person.person_id,
        idempotency_key=occurrence_key,
        payload={"channel": channel, "text": text},
        navigation=navigation or {},
    )
    return True
