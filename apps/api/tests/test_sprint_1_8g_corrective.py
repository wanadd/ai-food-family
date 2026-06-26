"""Sprint 1.8G corrective — start tariff, purge safety, admin lifecycle."""

from __future__ import annotations

import importlib.util
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
from app.services import subscription as sub_svc  # noqa: E402
from app.services.plan_codes import START_DAYS, START_PLAN_CODE, public_plan_code  # noqa: E402
from app.services.user_data_purge import _delete_by_user_id, hard_delete_user_row  # noqa: E402

SUBSCRIPTION_SOURCE = (API_ROOT / "app" / "services" / "subscription.py").read_text(
    encoding="utf-8"
)


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


def _make_user(db, *, telegram_id: int, blocked: bool = False, deleted: bool = False) -> User:
    user = User(
        telegram_id=telegram_id,
        username="tester",
        first_name="Test",
    )
    if blocked:
        user.is_blocked = True
    if deleted:
        user.is_deleted = True
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_start_days_is_seven():
    assert START_DAYS == 7
    assert START_PLAN_CODE == "start"


def test_public_plan_code_maps_legacy():
    assert public_plan_code("trial") == "start"
    assert public_plan_code("free") == "start"
    assert public_plan_code("demo") == "start"
    assert public_plan_code("personal") == "personal"


def test_ensure_user_billing_source_uses_start():
    chunk = SUBSCRIPTION_SOURCE.split("def ensure_user_billing")[1].split(
        "def ensure_all_users_have_billing"
    )[0]
    assert "plan_code=START_PLAN_CODE" in chunk
    assert "menu_generations_used=0" in chunk
    assert 'plan_code="trial"' not in chunk


def test_select_plan_stub_source_forbidden():
    chunk = SUBSCRIPTION_SOURCE.split("def select_plan_stub")[1].split("def ")[0]
    assert "Тариф управляется администратором" in chunk
    assert "HTTP_403_FORBIDDEN" in chunk


def test_delete_by_user_id_skips_missing_column(db):
    class _NoUserId:
        pass

    assert _delete_by_user_id(db, _NoUserId, 1) == 0


def test_hard_delete_user_row_bulk(db):
    user = _make_user(db, telegram_id=920_004)
    uid = user.id
    assert hard_delete_user_row(db, uid) == 1
    db.commit()
    assert db.get(User, uid) is None


def test_restore_user_clears_archive(db):
    admin = _make_user(db, telegram_id=900_201)
    target = _make_user(db, telegram_id=910_201, deleted=True)
    manage.restore_user(db, user_id=target.id, admin=admin)
    db.refresh(target)
    assert target.is_deleted is False


def test_archive_does_not_block(db, monkeypatch):
    admin = _make_user(db, telegram_id=900_202)
    target = _make_user(db, telegram_id=910_202)

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


def test_reset_user_as_new_uses_bulk_delete(db):
    import app.services.user_data_purge as purge_mod

    admin = _make_user(db, telegram_id=900_203)
    target = _make_user(db, telegram_id=910_203)
    target_id = target.id

    with patch.object(purge_mod, "purge_user_data", return_value={}), patch.object(
        purge_mod, "hard_delete_user_row", return_value=1
    ) as hard_del:
        manage.reset_user_as_new(db, user_id=target_id, admin=admin)
        hard_del.assert_called_once_with(db, target_id)


def test_select_plan_stub_forbidden(db):
    user = _make_user(db, telegram_id=920_003)
    with pytest.raises(HTTPException) as exc:
        sub_svc.select_plan_stub(db, user, "personal")
    assert exc.value.status_code == 403


def test_prod_reset_script_confirm_token():
    path = API_ROOT.parents[1] / "backend" / "scripts" / "prod_full_user_reset.py"
    spec = importlib.util.spec_from_file_location("prod_full_user_reset", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    assert mod.CONFIRM_TOKEN == "FULL_USER_RESET"
