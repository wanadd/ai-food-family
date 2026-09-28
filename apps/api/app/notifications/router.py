from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.notifications.v2_service import authorize_subject, upsert_preference
from app.v2.authorization import AuthorizedContext, authorized_context

router = APIRouter(prefix="/api/v2", tags=["v2-notifications"])


class NotificationPreferenceRequest(BaseModel):
    subject_kind: str = Field(pattern="^(PERSON|HOUSEHOLD)$")
    subject_id: str
    channel: str = Field(min_length=1, max_length=32)
    enabled: bool = True
    shopping_enabled: bool | None = None
    cooking_enabled: bool | None = None
    timezone: str | None = Field(default=None, max_length=64)
    quiet_hours_start: str | None = Field(default=None, pattern=r"^([01][0-9]|2[0-3]):[0-5][0-9]$")
    quiet_hours_end: str | None = Field(default=None, pattern=r"^([01][0-9]|2[0-3]):[0-5][0-9]$")


def _context(db: Session = Depends(get_db), authorization: str | None = Header(default=None), session_token: str | None = Header(default=None, alias="X-Planam-Session")) -> AuthorizedContext:
    return authorized_context(db, authorization=authorization, x_planam_session=session_token)


@router.post("/notification-preferences")
def set_notification_preferences(
    payload: NotificationPreferenceRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    authorization: str | None = Header(default=None),
    session_token: str | None = Header(default=None, alias="X-Planam-Session"),
    context: AuthorizedContext = Depends(_context),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    if not idempotency_key:
        from app.v2.errors import error
        raise error("validation_error", 422, details={"header": "Idempotency-Key is required"})
    authorize_subject(
        db, context=context, subject_kind=payload.subject_kind, subject_id=payload.subject_id,
        authorization=authorization, session_token=session_token,
    )
    row = upsert_preference(
        db, context=context, subject_kind=payload.subject_kind, subject_id=payload.subject_id,
        channel=payload.channel, enabled=payload.enabled, timezone_name=payload.timezone,
        shopping_enabled=payload.shopping_enabled, cooking_enabled=payload.cooking_enabled,
        quiet_hours_start=payload.quiet_hours_start, quiet_hours_end=payload.quiet_hours_end,
        idempotency_key=idempotency_key,
    )
    db.commit()
    return {
        "preference_id": row.preference_id, "subject_kind": row.subject_kind,
        "subject_id": row.subject_id, "channel": row.channel, "enabled": row.enabled,
        "shopping_enabled": row.shopping_enabled, "cooking_enabled": row.cooking_enabled,
        "timezone": row.timezone, "quiet_hours_start": row.quiet_hours_start,
        "quiet_hours_end": row.quiet_hours_end,
    }
