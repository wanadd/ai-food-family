from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.admin import AdminSession
from app.models.user import User
from app.routers.v2_admin import _admin


@pytest.fixture()
def db():
    engine = create_engine("sqlite:///:memory:")
    User.__table__.create(engine)
    AdminSession.__table__.create(engine)
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()


def test_v2_admin_dependency_rejects_missing_session(db):
    from app.v2.errors import V2Error

    try:
        _admin(db, None)
    except V2Error as exc:
        assert exc.status_code == 403
    else:
        raise AssertionError("missing admin session must be forbidden")


def test_v2_admin_dependency_accepts_explicit_server_session(db, monkeypatch):
    user = User(telegram_id=987654321, username="operator", first_name="Operator")
    db.add(user)
    db.flush()
    session = AdminSession(
        user_id=user.id,
        telegram_id=user.telegram_id,
        session_token="w9-test-session",
        is_active=True,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )
    db.add(session)
    db.commit()
    monkeypatch.setattr("app.services.admin_auth.panel_enabled", lambda: True)
    monkeypatch.setattr("app.services.admin_auth.is_admin_telegram_id", lambda _: True)
    assert _admin(db, "w9-test-session").id == user.id
