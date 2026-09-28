from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models.admin import AdminSession
from app.models.user import User
from app.services import admin as admin_service
from app.services.admin_auth import validate_admin_session_token
from app.v2.errors import error

router = APIRouter(prefix="/api/v2/admin", tags=["v2-admin"])


class AdminSessionExchangeRequest(BaseModel):
    init_data: str = Field(min_length=1)


class AdminSessionExchangeResponse(BaseModel):
    session_token: str
    expires_at: datetime
    role: str = "SYSTEM_ADMIN"


class AdminMetric(BaseModel):
    value: int | float | None = None
    state: str = "available"


class AdminOverviewResponse(BaseModel):
    generated_at: datetime
    api: AdminMetric
    database: AdminMetric
    users: AdminMetric
    households: AdminMetric
    active_subscriptions: AdminMetric
    errors_last_24h: AdminMetric
    analytics: AdminMetric


class AdminAnalyticsResponse(BaseModel):
    state: str
    message: str
    events: list[dict] = Field(default_factory=list)


def _admin(
    db: Session = Depends(get_db),
    token: str | None = Header(default=None, alias="X-Admin-Session"),
) -> User:
    session = validate_admin_session_token(db, token)
    if session is None:
        raise error("forbidden", 403)
    user = db.get(User, session.user_id)
    if user is None:
        raise error("forbidden", 403)
    return user


@router.post("/session/exchange", response_model=AdminSessionExchangeResponse)
def exchange_admin_session(
    payload: AdminSessionExchangeRequest,
    db: Session = Depends(get_db),
) -> AdminSessionExchangeResponse:
    # Telegram init data authenticates the edge request; the PIN-created session
    # remains the explicit admin privilege. No bearer is transported in a URL.
    user = get_current_user(x_telegram_init_data=payload.init_data, db=db)
    now = datetime.now(timezone.utc)
    session = (
        db.query(AdminSession)
        .filter(
            AdminSession.user_id == user.id,
            AdminSession.is_active.is_(True),
            AdminSession.expires_at > now,
        )
        .order_by(AdminSession.created_at.desc())
        .first()
    )
    if session is None or validate_admin_session_token(db, session.session_token) is None:
        raise error("forbidden", 403)
    return AdminSessionExchangeResponse(
        session_token=session.session_token,
        expires_at=session.expires_at,
    )


@router.get("/overview", response_model=AdminOverviewResponse)
def admin_overview(
    _: User = Depends(_admin),
    db: Session = Depends(get_db),
) -> AdminOverviewResponse:
    try:
        db.execute(text("SELECT 1"))
        database = AdminMetric(value=1)
    except Exception:
        database = AdminMetric(state="unavailable")
    summary = admin_service.get_summary(db)
    return AdminOverviewResponse(
        generated_at=datetime.now(timezone.utc),
        api=AdminMetric(value=1),
        database=database,
        users=AdminMetric(value=summary.get("total_users")),
        households=AdminMetric(value=summary.get("total_families")),
        active_subscriptions=AdminMetric(value=summary.get("active_subscriptions")),
        errors_last_24h=AdminMetric(value=summary.get("errors_last_24h")),
        analytics=AdminMetric(state="not_available"),
    )


@router.get("/analytics", response_model=AdminAnalyticsResponse)
def admin_analytics(_: User = Depends(_admin)) -> AdminAnalyticsResponse:
    return AdminAnalyticsResponse(
        state="not_available",
        message="Analytics persistence is not configured in this environment.",
    )
