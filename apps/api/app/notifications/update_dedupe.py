from __future__ import annotations

import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.notifications.v2_models import OutboxEvent


def claim_telegram_update(db: Session, update_id: int) -> bool:
    """Durably claim a provider update before translating it into a command."""
    aggregate_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"planam:telegram:update:{update_id}"))
    row = OutboxEvent(
        outbox_event_id=str(uuid.uuid4()),
        aggregate_id=aggregate_id,
        event_kind="telegram.update.received",
        idempotency_key=str(update_id),
        payload_json={"provider": "telegram", "update_id": update_id},
    )
    db.add(row)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        return False
    return True
