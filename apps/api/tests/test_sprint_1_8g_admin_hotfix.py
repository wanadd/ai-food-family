"""Sprint 1.8G — admin access, trial, user reset semantics."""

import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

API_ROOT = Path(__file__).resolve().parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.models.user import User  # noqa: E402
from app.services import admin_manage as manage  # noqa: E402
from app.services.subscription_catalog import TRIAL_DAYS  # noqa: E402

MANAGE_SOURCE = (API_ROOT / "app" / "services" / "admin_manage.py").read_text(encoding="utf-8")


@pytest.fixture()
def db():
    engine = create_engine("sqlite:///:memory:")
    User.__table__.create(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(autouse=True)
def _noop_audit(monkeypatch):
    monkeypatch.setattr("app.services.admin_manage.log_admin_action", lambda *a, **k: None)


def _make_user(db, *, telegram_id: int, blocked: bool = False) -> User:
    user = User(
        telegram_id=telegram_id,
        username="tester",
        first_name="Test",
    )
    if blocked:
        user.is_blocked = True
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_trial_days_is_seven():
    assert TRIAL_DAYS == 7


def test_delete_user_source_does_not_block():
    chunk = MANAGE_SOURCE.split("def delete_user")[1].split("def clear_user_data")[0]
    assert "is_blocked = True" not in chunk


def test_reset_user_as_new_removes_row(db):
    import app.services.user_data_purge as purge_mod

    admin = _make_user(db, telegram_id=900_000_101)
    target = _make_user(db, telegram_id=910_002, blocked=True)
    target_id = target.id

    def _hard_delete_row(session, user):
        session.query(User).filter(User.id == user.id).delete(synchronize_session=False)

    with patch.object(purge_mod, "purge_user_data", return_value={}), patch.object(
        purge_mod, "hard_delete_user_row", side_effect=_hard_delete_row
    ):
        manage.reset_user_as_new(db, user_id=target_id, admin=admin)

    assert db.get(User, target_id) is None


def test_block_and_unblock_user(db):
    admin = _make_user(db, telegram_id=900_000_102)
    target = _make_user(db, telegram_id=910_003)

    manage.block_user(db, user_id=target.id, admin=admin, reason="qa")
    db.refresh(target)
    assert target.is_blocked is True

    manage.unblock_user(db, user_id=target.id, admin=admin)
    db.refresh(target)
    assert target.is_blocked is False


def test_cannot_block_self(db):
    admin = _make_user(db, telegram_id=900_000_103)

    with pytest.raises(HTTPException) as exc:
        manage.block_user(db, user_id=admin.id, admin=admin)
    assert exc.value.status_code == 400


def test_soft_delete_does_not_block(db, monkeypatch):
    admin = _make_user(db, telegram_id=900_000_104)
    target = _make_user(db, telegram_id=910_004)

    class _Q:
        def filter(self, *args, **kwargs):
            return self

        def one_or_none(self):
            return None

        def update(self, *args, **kwargs):
            return 0

    monkeypatch.setattr(db, "query", lambda *args, **kwargs: _Q())

    manage.delete_user(db, user_id=target.id, admin=admin)
    db.refresh(target)
    assert target.is_deleted is True
    assert target.is_blocked is False
