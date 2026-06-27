"""Hotfix 1.8H — notification onboarding, care guards, dedup, reset script."""

from __future__ import annotations

import importlib.util
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import create_engine, text

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

API_ROOT = Path(__file__).resolve().parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.models.user import User  # noqa: E402
from app.schemas.notifications import NotificationOnboardingRequest  # noqa: E402
from app.services import notifications as notif_service  # noqa: E402
from app.services.care_guard import (  # noqa: E402
    PANTRY_SEMANTIC_KEY,
    can_send_care_notification,
    can_send_scheduled_reminder,
)


def test_default_settings_row_is_quiet():
    row = notif_service._default_settings_row(user_id=1)
    assert row.notifications_onboarded is False
    assert row.care_mode == "off"
    assert row.enabled_notification_types == []
    assert row.buy_reminder_enabled is False
    assert row.cook_reminder_enabled is False


def test_fresh_user_blocked_from_pantry(monkeypatch):
    user = SimpleNamespace(id=1)
    notif = SimpleNamespace(
        notifications_onboarded=False,
        care_mode="off",
        enabled_notification_types=[],
    )
    monkeypatch.setattr(
        "app.services.care_guard.get_or_create_settings", lambda _db, _u: notif
    )
    db = MagicMock()
    assert (
        can_send_care_notification(
            db, user, "pantry", semantic_key=PANTRY_SEMANTIC_KEY
        )
        is False
    )


def test_fresh_user_scheduled_reminder_blocked(monkeypatch):
    user = SimpleNamespace(id=1)
    notif = SimpleNamespace(notifications_onboarded=False, care_mode="off")
    monkeypatch.setattr(
        "app.services.care_guard.get_or_create_settings", lambda _db, _u: notif
    )
    assert can_send_scheduled_reminder(MagicMock(), user) is False


def test_onboarding_skip_sets_off(db_sqlite):
    db = db_sqlite
    user = _make_user(db)
    out = notif_service.apply_onboarding(
        db,
        user,
        NotificationOnboardingRequest(care_mode="off", enabled_notification_types=[]),
    )
    assert out.notifications_onboarded is True
    assert out.care_mode == "off"
    assert out.buy_reminder_enabled is False


def test_onboarding_enables_selected_types(db_sqlite):
    from app.models.care import CareSettings

    db = db_sqlite
    user = _make_user(db)
    out = notif_service.apply_onboarding(
        db,
        user,
        NotificationOnboardingRequest(
            care_mode="normal",
            enabled_notification_types=["menu", "pantry"],
            quiet_hours_start="22:00",
            quiet_hours_end="09:00",
        ),
    )
    assert out.notifications_onboarded is True
    assert "menu" in out.enabled_notification_types
    assert out.cook_reminder_enabled is True
    care = (
        db.query(CareSettings)
        .filter(CareSettings.user_id == user.id)
        .one()
    )
    assert care.pantry_enabled is True
    assert care.quiet_hours_start == "22:00"


def test_pantry_dedup_within_24h(db_sqlite, monkeypatch):
    from app.services.care import create_care_notification

    db = db_sqlite
    user = _make_user(db)
    notif_service.apply_onboarding(
        db,
        user,
        NotificationOnboardingRequest(
            care_mode="normal",
            enabled_notification_types=["pantry"],
        ),
    )
    monkeypatch.setattr(
        "app.services.care_guard.user_has_menu", lambda _db, _user: True
    )
    monkeypatch.setattr(
        "app.services.care_guard.user_profile_completed",
        lambda _db, _user: True,
    )
    first = create_care_notification(
        db,
        user,
        "pantry",
        semantic_key=PANTRY_SEMANTIC_KEY,
    )
    second = create_care_notification(
        db,
        user,
        "pantry",
        semantic_key=PANTRY_SEMANTIC_KEY,
    )
    assert first is not None
    assert second is None


def test_telegram_update_dedup():
    from app.services.telegram_update_dedup import should_process_telegram_update

    client = MagicMock()
    client.set.side_effect = [True, False]
    with patch(
        "app.services.telegram_update_dedup._redis_client", return_value=client
    ):
        assert should_process_telegram_update({"update_id": 42}) is True
        assert should_process_telegram_update({"update_id": 42}) is False


def test_telegram_callback_dedup():
    from app.services.telegram_update_dedup import should_process_telegram_update

    client = MagicMock()
    client.set.side_effect = [True, True, False]
    with patch(
        "app.services.telegram_update_dedup._redis_client", return_value=client
    ):
        update = {"update_id": 1, "callback_query": {"id": "cb-99"}}
        assert should_process_telegram_update(update) is True
        assert should_process_telegram_update(update) is False


def test_scheduler_lock_skips_when_redis_busy(monkeypatch):
    from app.services.scheduler_lock import notification_scheduler_lock

    client = MagicMock()
    client.set.return_value = False
    fake_redis = MagicMock()
    fake_redis.from_url.return_value = client
    monkeypatch.setitem(sys.modules, "redis", fake_redis)

    db = MagicMock()
    db.execute.return_value.scalar.return_value = False

    with notification_scheduler_lock(db) as locked:
        assert locked is False


def test_prod_reset_dry_run_sqlite(tmp_path, monkeypatch):
    path = API_ROOT.parents[1] / "backend" / "scripts" / "prod_full_user_reset.py"
    spec = importlib.util.spec_from_file_location("prod_full_user_reset", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)

    db_path = tmp_path / "reset.db"
    url = f"sqlite:///{db_path.as_posix()}"
    monkeypatch.setenv("DATABASE_URL", url)
    monkeypatch.setattr(sys, "argv", ["prod_full_user_reset.py"])
    engine = create_engine(url)
    with engine.begin() as conn:
        conn.execute(
            text(
                "CREATE TABLE users (id INTEGER PRIMARY KEY, telegram_id INTEGER, "
                "username TEXT, first_name TEXT, is_blocked BOOLEAN, is_deleted BOOLEAN, created_at TEXT)"
            )
        )
        conn.execute(text("CREATE TABLE recipes (id INTEGER PRIMARY KEY, user_id INTEGER)"))
        conn.execute(text("INSERT INTO recipes (id, user_id) VALUES (1, NULL)"))
        conn.execute(
            text(
                "CREATE TABLE subscription_plans (id INTEGER PRIMARY KEY, code TEXT, name TEXT, is_active BOOLEAN, sort_order INTEGER)"
            )
        )
        conn.execute(text("INSERT INTO subscription_plans VALUES (1, 'start', 'Start', 1, 1)"))

    rc = mod.main()
    assert rc == 0


def test_prod_reset_apply_no_autobegin_error(tmp_path, monkeypatch):
    path = API_ROOT.parents[1] / "backend" / "scripts" / "prod_full_user_reset.py"
    spec = importlib.util.spec_from_file_location("prod_full_user_reset", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)

    db_path = tmp_path / "apply.db"
    url = f"sqlite:///{db_path.as_posix()}"
    monkeypatch.setenv("DATABASE_URL", url)
    engine = create_engine(url)
    with engine.begin() as conn:
        conn.execute(
            text(
                "CREATE TABLE users (id INTEGER PRIMARY KEY, telegram_id INTEGER, "
                "username TEXT, first_name TEXT, is_blocked BOOLEAN, is_deleted BOOLEAN, created_at TEXT)"
            )
        )
        conn.execute(text("INSERT INTO users VALUES (1, 10, 'a', 'A', 0, 0, '2026-01-01')"))
        conn.execute(text("CREATE TABLE recipes (id INTEGER PRIMARY KEY, user_id INTEGER)"))
        conn.execute(text("INSERT INTO recipes (id, user_id) VALUES (1, 1), (2, NULL)"))
        conn.execute(
            text(
                "CREATE TABLE subscription_plans (id INTEGER PRIMARY KEY, code TEXT, name TEXT, is_active BOOLEAN, sort_order INTEGER)"
            )
        )
        conn.execute(text("INSERT INTO subscription_plans VALUES (1, 'start', 'Start', 1, 1)"))

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "prod_full_user_reset.py",
            "--apply",
            "--confirm",
            "FULL_USER_RESET",
            "--backup-dir",
            str(tmp_path),
        ],
    )
    rc = mod.main()
    assert rc == 0

    with engine.connect() as conn:
        users = conn.execute(text("SELECT COUNT(*) FROM users")).scalar()
        recipes = conn.execute(text("SELECT COUNT(*) FROM recipes")).scalar()
    assert users == 0
    assert recipes == 2


def test_onboarded_user_with_menu_may_get_pantry(monkeypatch):
    user = SimpleNamespace(id=1)
    notif = SimpleNamespace(
        notifications_onboarded=True,
        care_mode="normal",
        enabled_notification_types=["pantry"],
    )
    care = SimpleNamespace(pantry_enabled=True)
    monkeypatch.setattr(
        "app.services.care_guard.get_or_create_settings", lambda _db, _u: notif
    )
    monkeypatch.setattr(
        "app.services.care_guard._care_settings_row", lambda _db, _u: care
    )
    monkeypatch.setattr(
        "app.services.care_guard.user_has_menu", lambda _db, _user: True
    )
    monkeypatch.setattr(
        "app.services.care_guard.user_profile_completed",
        lambda _db, _user: True,
    )
    monkeypatch.setattr(
        "app.services.care_guard._recent_duplicate", lambda *_a, **_k: False
    )
    assert (
        can_send_care_notification(
            MagicMock(), user, "pantry", semantic_key=PANTRY_SEMANTIC_KEY
        )
        is True
    )


@pytest.fixture()
def db_sqlite():
    from sqlalchemy import JSON
    from sqlalchemy.orm import sessionmaker

    from app.models.care import CareNotification, CareSettings
    from app.models.notification_settings import UserNotificationSettings

    UserNotificationSettings.__table__.c.enabled_notification_types.type = JSON()
    CareNotification.__table__.c.payload.type = JSON()

    engine = create_engine("sqlite:///:memory:")
    User.__table__.create(engine)
    UserNotificationSettings.__table__.create(engine)
    CareSettings.__table__.create(engine)
    CareNotification.__table__.create(engine)

    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def _make_user(db) -> User:
    user = User(telegram_id=9001, username="u", first_name="U")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
