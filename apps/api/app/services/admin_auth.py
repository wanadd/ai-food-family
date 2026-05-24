"""Admin PIN flow, sessions, and rate limiting."""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import settings
from app.models.admin import AdminLoginAttempt, AdminSession
from app.models.user import User
from app.services.admin_audit import log_admin_action

SESSION_TTL_HOURS = 12
MAX_PIN_ATTEMPTS = 5
LOCKOUT_MINUTES = 15
STATE_AWAITING_ADMIN_PIN = "awaiting_admin_pin"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def is_admin_telegram_id(telegram_id: int) -> bool:
    return telegram_id in settings.admin_telegram_id_set()


def panel_enabled() -> bool:
    return settings.admin_panel_enabled_flag and bool(settings.admin_telegram_id_set())


def admin_webapp_url(session_token: str) -> str:
    base = (settings.telegram_webapp_url or "").rstrip("/")
    return f"{base}/admin?admin_session={session_token}"


def _count_failed_attempts(db: Session, telegram_id: int, since: datetime) -> int:
    return (
        db.query(func.count(AdminLoginAttempt.id))
        .filter(
            AdminLoginAttempt.telegram_id == telegram_id,
            AdminLoginAttempt.success.is_(False),
            AdminLoginAttempt.created_at >= since,
        )
        .scalar()
        or 0
    )


def is_pin_locked(db: Session, telegram_id: int) -> bool:
    since = _now() - timedelta(minutes=LOCKOUT_MINUTES)
    return _count_failed_attempts(db, telegram_id, since) >= MAX_PIN_ATTEMPTS


def record_pin_attempt(db: Session, telegram_id: int, *, success: bool) -> None:
    db.add(AdminLoginAttempt(telegram_id=telegram_id, success=success))
    db.commit()


def verify_pin(pin: str) -> bool:
    expected = (settings.admin_pin or "").strip()
    if not expected:
        return False
    return secrets.compare_digest(pin.strip(), expected)


def create_admin_session(db: Session, user: User) -> AdminSession:
    token = secrets.token_urlsafe(32)
    now = _now()
    row = AdminSession(
        user_id=user.id,
        telegram_id=user.telegram_id,
        session_token=token,
        is_active=True,
        created_at=now,
        expires_at=now + timedelta(hours=SESSION_TTL_HOURS),
        last_used_at=now,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    log_admin_action(
        db,
        admin_user_id=user.id,
        action_type="admin_login",
        target_type="user",
        target_id=user.id,
    )
    return row


def get_valid_session(
    db: Session, user: User, session_token: str | None
) -> AdminSession | None:
    if not session_token or not panel_enabled():
        return None
    if not is_admin_telegram_id(user.telegram_id):
        return None
    now = _now()
    row = (
        db.query(AdminSession)
        .filter(
            AdminSession.session_token == session_token,
            AdminSession.user_id == user.id,
            AdminSession.is_active.is_(True),
            AdminSession.expires_at > now,
        )
        .one_or_none()
    )
    if row is None:
        return None
    row.last_used_at = now
    db.commit()
    return row


def require_valid_session(
    db: Session, user: User, session_token: str | None
) -> AdminSession:
    session = get_valid_session(db, user, session_token)
    if session is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return session
