"""Admin panel auth via X-Admin-Session bearer token (post-PIN flow)."""

from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from fastapi import HTTPException, status
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

API_ROOT = Path(__file__).resolve().parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app import deps  # noqa: E402
from app.models.admin import AdminSession  # noqa: E402
from app.models.user import User  # noqa: E402
from app.services import admin_auth  # noqa: E402

ADMIN_TG_ID = 589_328_345
OTHER_TG_ID = 111_111_111
SESSION_TOKEN = "test-session-token-valid-32chars-ok"


@pytest.fixture()
def db():
    engine = create_engine("sqlite:///:memory:")
    User.__table__.create(engine)
    AdminSession.__table__.create(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def _seed_admin_user(db, *, telegram_id: int = ADMIN_TG_ID, blocked=False, deleted=False):
    user = User(
        telegram_id=telegram_id,
        is_blocked=blocked,
        is_deleted=deleted,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _seed_session(
    db,
    user: User,
    *,
    token: str = SESSION_TOKEN,
    active: bool = True,
    expires_delta: timedelta | None = None,
    telegram_id: int | None = None,
):
    now = datetime.now(timezone.utc)
    row = AdminSession(
        user_id=user.id,
        telegram_id=telegram_id if telegram_id is not None else user.telegram_id,
        session_token=token,
        is_active=active,
        created_at=now,
        expires_at=now + (expires_delta or timedelta(hours=12)),
        last_used_at=now,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@pytest.fixture(autouse=True)
def _admin_settings(monkeypatch):
    monkeypatch.setattr(
        admin_auth.settings,
        "admin_telegram_ids",
        str(ADMIN_TG_ID),
    )
    monkeypatch.setattr(admin_auth.settings, "admin_panel_enabled", True)
    monkeypatch.setattr(deps.settings, "admin_telegram_ids", str(ADMIN_TG_ID))
    monkeypatch.setattr(deps.settings, "admin_panel_enabled", True)


def test_validate_admin_session_token_grants_valid_session(db):
    user = _seed_admin_user(db)
    _seed_session(db, user)

    session = admin_auth.validate_admin_session_token(db, SESSION_TOKEN)

    assert session is not None
    assert session.user_id == user.id


def test_validate_admin_session_token_missing_returns_none(db):
    assert admin_auth.validate_admin_session_token(db, None) is None
    assert admin_auth.validate_admin_session_token(db, "") is None


def test_validate_admin_session_token_expired_returns_none(db):
    user = _seed_admin_user(db)
    _seed_session(db, user, expires_delta=timedelta(hours=-1))

    assert admin_auth.validate_admin_session_token(db, SESSION_TOKEN) is None


def test_validate_admin_session_token_non_admin_telegram_id_returns_none(db):
    user = _seed_admin_user(db, telegram_id=OTHER_TG_ID)
    _seed_session(db, user, telegram_id=OTHER_TG_ID)

    assert admin_auth.validate_admin_session_token(db, SESSION_TOKEN) is None


def test_validate_admin_session_token_blocked_user_returns_none(db):
    user = _seed_admin_user(db, blocked=True)
    _seed_session(db, user)

    assert admin_auth.validate_admin_session_token(db, SESSION_TOKEN) is None


def test_validate_admin_session_token_deleted_user_returns_none(db):
    user = _seed_admin_user(db, deleted=True)
    _seed_session(db, user)

    assert admin_auth.validate_admin_session_token(db, SESSION_TOKEN) is None


def test_require_admin_user_with_valid_session_without_init_data(db):
    user = _seed_admin_user(db)
    _seed_session(db, user)

    result = deps.require_admin_user(
        x_telegram_init_data=None,
        x_admin_session=SESSION_TOKEN,
        db=db,
    )

    assert result.id == user.id


def test_require_admin_user_missing_session_and_init_data_returns_401(db):
    with pytest.raises(HTTPException) as exc:
        deps.require_admin_user(
            x_telegram_init_data=None,
            x_admin_session=None,
            db=db,
        )
    assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED


def test_require_admin_user_invalid_session_returns_403(db):
    user = _seed_admin_user(db)
    _seed_session(db, user, expires_delta=timedelta(hours=-1))

    with pytest.raises(HTTPException) as exc:
        deps.require_admin_user(
            x_telegram_init_data=None,
            x_admin_session=SESSION_TOKEN,
            db=db,
        )
    assert exc.value.status_code == status.HTTP_403_FORBIDDEN


def test_require_admin_user_non_admin_session_returns_403(db):
    user = _seed_admin_user(db, telegram_id=OTHER_TG_ID)
    _seed_session(db, user, telegram_id=OTHER_TG_ID)

    with pytest.raises(HTTPException) as exc:
        deps.require_admin_user(
            x_telegram_init_data=None,
            x_admin_session=SESSION_TOKEN,
            db=db,
        )
    assert exc.value.status_code == status.HTTP_403_FORBIDDEN
