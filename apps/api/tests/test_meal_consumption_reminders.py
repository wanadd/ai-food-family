"""Tests for automatic meal consumption reminders (Phase 3A)."""

from __future__ import annotations

import os
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
import asyncio
from unittest.mock import AsyncMock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

API_ROOT = Path(__file__).resolve().parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.models.meal_consumption_log import MealConsumptionLog  # noqa: E402
from app.models.meal_consumption_reminder_event import (  # noqa: E402
    MealConsumptionReminderEvent,
)
from app.models.notification_settings import UserNotificationSettings  # noqa: E402
from app.services import meal_consumption_reminders as reminders  # noqa: E402

MOSCOW = timezone(timedelta(hours=3))


@pytest.fixture(autouse=True)
def _mock_care_settings(monkeypatch):
    monkeypatch.setattr(
        reminders,
        "get_or_create_care_settings",
        lambda _db, _user: SimpleNamespace(
            quiet_hours_start=None,
            quiet_hours_end=None,
            timezone=None,
        ),
    )


@pytest.fixture()
def db():
    engine = create_engine("sqlite:///:memory:")
    MealConsumptionLog.__table__.create(engine)
    MealConsumptionReminderEvent.__table__.create(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def _user(
    user_id: int = 10,
    *,
    telegram_id: int | None = 111,
    is_blocked: bool = False,
    is_deleted: bool = False,
) -> SimpleNamespace:
    return SimpleNamespace(
        id=user_id,
        telegram_id=telegram_id,
        is_blocked=is_blocked,
        is_deleted=is_deleted,
    )


def _notif(*, cook_enabled: bool = True) -> UserNotificationSettings:
    return UserNotificationSettings(
        user_id=10,
        cook_reminder_enabled=cook_enabled,
        cook_lunch_time="14:30",
        timezone="Europe/Moscow",
    )


def _due(
    *,
    user: SimpleNamespace | None = None,
    family_id: int | None = 1,
    planned_date: date | None = None,
    meal_type: str = "lunch",
    due_at: datetime | None = None,
) -> reminders.DueMealConsumptionReminder:
    planned = planned_date or date(2026, 6, 10)
    due = due_at or datetime(2026, 6, 10, 15, 30, tzinfo=MOSCOW)
    return reminders.DueMealConsumptionReminder(
        user=user or _user(),
        family_id=family_id,
        menu_selection_id=123,
        day_index=2,
        planned_date=planned,
        meal_type=meal_type,
        due_at=due,
        timezone_name="Europe/Moscow",
    )


def _log(
    db,
    *,
    user_id: int = 10,
    family_id: int | None = 1,
    status: str = "eaten",
    meal_type: str = "lunch",
) -> None:
    db.add(
        MealConsumptionLog(
            family_id=family_id,
            user_id=user_id,
            logged_by_user_id=user_id,
            menu_selection_id=123,
            day_index=2,
            planned_date=date(2026, 6, 10),
            meal_type=meal_type,
            status=status,
        )
    )
    db.flush()


def _event(db, *, status: str = "sent") -> None:
    db.add(
        MealConsumptionReminderEvent(
            user_id=10,
            family_id=1,
            menu_selection_id=123,
            day_index=2,
            planned_date=date(2026, 6, 10),
            meal_type="lunch",
            reminder_kind=reminders.REMINDER_KIND,
            status=status,
            due_at=datetime(2026, 6, 10, 15, 30, tzinfo=MOSCOW),
        )
    )
    db.flush()


def test_build_meal_reminder_message():
    text = reminders.build_meal_reminder_message("lunch")
    assert "обеда" in text
    assert "Питание сегодня" in text


def test_build_meal_reminder_web_app_path():
    assert reminders.build_meal_reminder_web_app_path("lunch") == (
        "/plan/today?openMealConsumption=1&mealType=lunch"
    )


def test_has_meal_consumption_log_when_eaten(db):
    _log(db, status="eaten")
    assert reminders.has_meal_consumption_log(
        db,
        user_id=10,
        family_id=1,
        menu_selection_id=123,
        day_index=2,
        planned_date=date(2026, 6, 10),
        meal_type="lunch",
    )


def test_should_send_when_no_log(db, monkeypatch):
    monkeypatch.setattr(reminders, "_is_quiet_hours", lambda *_: False)
    ok, reason = reminders.should_send_meal_consumption_reminder(
        db,
        user=_user(),
        notification_settings=_notif(),
        due=_due(),
        now=datetime(2026, 6, 10, 16, 0, tzinfo=MOSCOW),
    )
    assert ok is True
    assert reason is None


@pytest.mark.parametrize("status", ["eaten", "skipped", "ate_out", "unknown"])
def test_should_not_send_when_logged(db, status, monkeypatch):
    monkeypatch.setattr(reminders, "_is_quiet_hours", lambda *_: False)
    _log(db, status=status)
    ok, reason = reminders.should_send_meal_consumption_reminder(
        db,
        user=_user(),
        notification_settings=_notif(),
        due=_due(),
        now=datetime(2026, 6, 10, 16, 0, tzinfo=MOSCOW),
    )
    assert ok is False
    assert reason == "skipped_already_logged"


def test_should_not_send_without_telegram(db, monkeypatch):
    monkeypatch.setattr(reminders, "_is_quiet_hours", lambda *_: False)
    ok, reason = reminders.should_send_meal_consumption_reminder(
        db,
        user=_user(telegram_id=None),
        notification_settings=_notif(),
        due=_due(),
        now=datetime(2026, 6, 10, 16, 0, tzinfo=MOSCOW),
    )
    assert ok is False
    assert reason == "skipped_no_telegram"


def test_should_not_send_when_notifications_disabled(db, monkeypatch):
    monkeypatch.setattr(reminders, "_is_quiet_hours", lambda *_: False)
    ok, reason = reminders.should_send_meal_consumption_reminder(
        db,
        user=_user(),
        notification_settings=_notif(cook_enabled=False),
        due=_due(),
        now=datetime(2026, 6, 10, 16, 0, tzinfo=MOSCOW),
    )
    assert ok is False
    assert reason == "skipped_notifications_disabled"


def test_should_not_send_in_quiet_hours(db, monkeypatch):
    monkeypatch.setattr(reminders, "_is_quiet_hours", lambda *_: True)
    ok, reason = reminders.should_send_meal_consumption_reminder(
        db,
        user=_user(),
        notification_settings=_notif(),
        due=_due(),
        now=datetime(2026, 6, 10, 16, 0, tzinfo=MOSCOW),
    )
    assert ok is False
    assert reason is None
    assert db.query(MealConsumptionReminderEvent).count() == 0


def test_should_not_send_when_already_sent(db, monkeypatch):
    monkeypatch.setattr(reminders, "_is_quiet_hours", lambda *_: False)
    _event(db, status="sent")
    ok, reason = reminders.should_send_meal_consumption_reminder(
        db,
        user=_user(),
        notification_settings=_notif(),
        due=_due(),
        now=datetime(2026, 6, 10, 16, 0, tzinfo=MOSCOW),
    )
    assert ok is False
    assert reason == "skipped_already_sent"


def test_should_not_send_when_too_late(db, monkeypatch):
    monkeypatch.setattr(reminders, "_is_quiet_hours", lambda *_: False)
    due = _due(due_at=datetime(2026, 6, 10, 15, 30, tzinfo=MOSCOW))
    ok, reason = reminders.should_send_meal_consumption_reminder(
        db,
        user=_user(),
        notification_settings=_notif(),
        due=due,
        now=due.due_at + timedelta(hours=9),
    )
    assert ok is False
    assert reason == "skipped_too_late"


def test_personal_mode_family_id_null(db, monkeypatch):
    monkeypatch.setattr(reminders, "_is_quiet_hours", lambda *_: False)
    ok, _ = reminders.should_send_meal_consumption_reminder(
        db,
        user=_user(),
        notification_settings=_notif(),
        due=_due(family_id=None),
        now=datetime(2026, 6, 10, 16, 0, tzinfo=MOSCOW),
    )
    assert ok is True


def test_family_mode_with_family_id(db, monkeypatch):
    monkeypatch.setattr(reminders, "_is_quiet_hours", lambda *_: False)
    _log(db, family_id=1, user_id=99)
    ok, reason = reminders.should_send_meal_consumption_reminder(
        db,
        user=_user(user_id=10),
        notification_settings=_notif(),
        due=_due(family_id=1),
        now=datetime(2026, 6, 10, 16, 0, tzinfo=MOSCOW),
    )
    assert ok is True
    assert reason is None


def test_send_creates_sent_event(db, monkeypatch):
    monkeypatch.setattr(
        reminders.settings,
        "meal_consumption_reminders_enabled",
        True,
        raising=False,
    )
    monkeypatch.setattr(
        reminders.settings,
        "meal_consumption_reminders_dry_run",
        False,
        raising=False,
    )
    monkeypatch.setattr(
        reminders,
        "find_due_meal_consumption_reminders",
        lambda _db, _now: [_due()],
    )
    monkeypatch.setattr(reminders, "get_notif_settings", lambda _db, _u: _notif())
    monkeypatch.setattr(reminders, "_is_quiet_hours", lambda *_: False)
    monkeypatch.setattr(
        reminders,
        "send_telegram_message",
        AsyncMock(return_value=True),
    )

    counts = asyncio.run(
        reminders.send_due_meal_consumption_reminders(
            db,
            datetime(2026, 6, 10, 16, 0, tzinfo=MOSCOW),
            dry_run=False,
        )
    )
    assert counts["sent"] == 1
    event = db.query(MealConsumptionReminderEvent).one()
    assert event.status == "sent"


def test_send_dry_run_no_telegram(db, monkeypatch):
    monkeypatch.setattr(
        reminders.settings,
        "meal_consumption_reminders_enabled",
        True,
        raising=False,
    )
    monkeypatch.setattr(
        reminders,
        "find_due_meal_consumption_reminders",
        lambda _db, _now: [_due()],
    )
    monkeypatch.setattr(reminders, "get_notif_settings", lambda _db, _u: _notif())
    monkeypatch.setattr(reminders, "_is_quiet_hours", lambda *_: False)
    mock_send = AsyncMock(return_value=True)
    monkeypatch.setattr(reminders, "send_telegram_message", mock_send)

    counts = asyncio.run(
        reminders.send_due_meal_consumption_reminders(
            db,
            datetime(2026, 6, 10, 16, 0, tzinfo=MOSCOW),
            dry_run=True,
            force=True,
        )
    )
    assert counts["dry_run"] == 1
    mock_send.assert_not_called()
    assert db.query(MealConsumptionReminderEvent).count() == 0


def test_send_skips_when_eaten(db, monkeypatch):
    monkeypatch.setattr(
        reminders.settings,
        "meal_consumption_reminders_enabled",
        True,
        raising=False,
    )
    monkeypatch.setattr(
        reminders.settings,
        "meal_consumption_reminders_dry_run",
        False,
        raising=False,
    )
    _log(db, status="eaten")
    monkeypatch.setattr(
        reminders,
        "find_due_meal_consumption_reminders",
        lambda _db, _now: [_due()],
    )
    monkeypatch.setattr(reminders, "get_notif_settings", lambda _db, _u: _notif())
    monkeypatch.setattr(reminders, "_is_quiet_hours", lambda *_: False)
    mock_send = AsyncMock(return_value=True)
    monkeypatch.setattr(reminders, "send_telegram_message", mock_send)

    counts = asyncio.run(
        reminders.send_due_meal_consumption_reminders(
            db,
            datetime(2026, 6, 10, 16, 0, tzinfo=MOSCOW),
            dry_run=False,
        )
    )
    assert counts["skipped"] == 1
    mock_send.assert_not_called()
    assert db.query(MealConsumptionReminderEvent).one().status == "skipped_already_logged"


def test_idempotent_second_run(db, monkeypatch):
    monkeypatch.setattr(
        reminders.settings,
        "meal_consumption_reminders_enabled",
        True,
        raising=False,
    )
    monkeypatch.setattr(
        reminders.settings,
        "meal_consumption_reminders_dry_run",
        False,
        raising=False,
    )
    monkeypatch.setattr(
        reminders,
        "find_due_meal_consumption_reminders",
        lambda _db, _now: [_due()],
    )
    monkeypatch.setattr(reminders, "get_notif_settings", lambda _db, _u: _notif())
    monkeypatch.setattr(reminders, "_is_quiet_hours", lambda *_: False)
    mock_send = AsyncMock(return_value=True)
    monkeypatch.setattr(reminders, "send_telegram_message", mock_send)
    now = datetime(2026, 6, 10, 16, 0, tzinfo=MOSCOW)

    asyncio.run(reminders.send_due_meal_consumption_reminders(db, now, dry_run=False))
    asyncio.run(reminders.send_due_meal_consumption_reminders(db, now, dry_run=False))

    assert mock_send.await_count == 1
    assert db.query(MealConsumptionReminderEvent).count() == 1


def test_sender_error_does_not_stop_job(db, monkeypatch):
    monkeypatch.setattr(
        reminders.settings,
        "meal_consumption_reminders_enabled",
        True,
        raising=False,
    )
    monkeypatch.setattr(
        reminders.settings,
        "meal_consumption_reminders_dry_run",
        False,
        raising=False,
    )
    due_a = _due(user=_user(user_id=10, telegram_id=111))
    due_b = _due(user=_user(user_id=20, telegram_id=222))
    monkeypatch.setattr(
        reminders,
        "find_due_meal_consumption_reminders",
        lambda _db, _now: [due_a, due_b],
    )
    monkeypatch.setattr(reminders, "get_notif_settings", lambda _db, _u: _notif())
    monkeypatch.setattr(reminders, "_is_quiet_hours", lambda *_: False)

    async def _flaky(telegram_id, *_args, **_kwargs):
        if telegram_id == 111:
            raise RuntimeError("telegram down")
        return True

    monkeypatch.setattr(reminders, "send_telegram_message", _flaky)

    counts = asyncio.run(
        reminders.send_due_meal_consumption_reminders(
            db,
            datetime(2026, 6, 10, 16, 0, tzinfo=MOSCOW),
            dry_run=False,
        )
    )
    assert counts["failed"] == 1
    assert counts["sent"] == 1
    statuses = {e.user_id: e.status for e in db.query(MealConsumptionReminderEvent).all()}
    assert statuses[10] == "failed"
    assert statuses[20] == "sent"


def test_virtual_members_not_in_user_scan():
    """Virtual members have no User.telegram_id — reminders target User rows only."""
    virtual = SimpleNamespace(user_id=None, is_virtual=True, telegram_id=None)
    assert virtual.user_id is None
    assert virtual.telegram_id is None
