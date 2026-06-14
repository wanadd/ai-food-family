"""Tests for meal consumption logs (Phase 2A)."""

from __future__ import annotations

import os
import sys
from datetime import date
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

API_ROOT = Path(__file__).resolve().parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.models.meal_consumption_log import MealConsumptionLog  # noqa: E402
from app.schemas.meal_consumption import (  # noqa: E402
    MealConsumptionBulkIn,
    MealConsumptionEntryIn,
)
from app.services import meal_consumption as svc  # noqa: E402


@pytest.fixture()
def db():
    engine = create_engine("sqlite:///:memory:")
    MealConsumptionLog.__table__.create(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def _user(user_id: int) -> SimpleNamespace:
    return SimpleNamespace(id=user_id)


def _membership(family_id: int = 1, role: str = "adult") -> SimpleNamespace:
    return SimpleNamespace(family_id=family_id, role=role)


def _bulk_payload(
    family_id: int = 1,
    *,
    user_id: int | None = 10,
    family_member_id: int | None = None,
    status: str = "eaten",
    portion: float = 1.0,
) -> MealConsumptionBulkIn:
    return MealConsumptionBulkIn(
        family_id=family_id,
        menu_selection_id=123,
        day_index=2,
        planned_date=date(2026, 6, 14),
        entries=[
            MealConsumptionEntryIn(
                user_id=user_id,
                family_member_id=family_member_id,
                meal_type="lunch",
                recipe_id=256,
                recipe_title="Овощной суп",
                status=status,
                portion_multiplier=portion,
            )
        ],
    )


@pytest.fixture(autouse=True)
def _allow_save(monkeypatch):
    monkeypatch.setattr(
        svc,
        "_caller_membership",
        lambda _db, _user: _membership(),
    )
    monkeypatch.setattr(
        svc,
        "_estimate_nutrition",
        lambda *_args, **_kwargs: (None, None, None, None),
    )


@pytest.fixture()
def simple_resolve(monkeypatch):
    monkeypatch.setattr(
        svc,
        "_resolve_subject",
        lambda _db, *, family_id, entry, caller: (
            entry.user_id or caller.id,
            entry.family_member_id,
        ),
    )


def test_user_saves_for_self(db, simple_resolve):
    rows = svc.save_meal_consumption_logs(
        db, caller=_user(10), payload=_bulk_payload(user_id=10)
    )
    assert len(rows) == 1
    assert rows[0].user_id == 10
    assert rows[0].status == "eaten"


def test_admin_saves_for_child_member(db, monkeypatch, simple_resolve):
    monkeypatch.setattr(
        svc,
        "_resolve_subject",
        lambda _db, *, family_id, entry, caller: (None, 3),
    )
    rows = svc.save_meal_consumption_logs(
        db,
        caller=_user(1),
        payload=_bulk_payload(user_id=None, family_member_id=3),
    )
    assert len(rows) == 1
    assert rows[0].family_member_id == 3


def test_adult_cannot_save_for_other_member(db, monkeypatch):
    def deny_other(_db, *, caller, family_id, target_user_id, target_family_member_id):
        return target_user_id == caller.id

    monkeypatch.setattr(svc, "can_log_for_member", deny_other)

    other_member = SimpleNamespace(id=2, family_id=1, user_id=20)

    class FakeQuery:
        def filter(self, *_args, **_kwargs):
            return self

        def one_or_none(self):
            return other_member

    monkeypatch.setattr(db, "query", lambda _model: FakeQuery())

    with pytest.raises(HTTPException) as exc:
        svc.save_meal_consumption_logs(
            db, caller=_user(10), payload=_bulk_payload(user_id=20)
        )
    assert exc.value.status_code == 403
    assert exc.value.detail == svc.PERMISSION_DENIED


def test_user_cannot_save_outside_family(db, monkeypatch):
    monkeypatch.setattr(svc, "_caller_membership", lambda _db, _user: None)
    with pytest.raises(HTTPException) as exc:
        svc.save_meal_consumption_logs(
            db, caller=_user(10), payload=_bulk_payload(family_id=99, user_id=10)
        )
    assert exc.value.status_code == 403
    assert exc.value.detail == svc.FAMILY_REQUIRED


def test_upsert_updates_not_duplicates(db, simple_resolve):
    svc.save_meal_consumption_logs(
        db, caller=_user(10), payload=_bulk_payload(user_id=10, portion=1.0)
    )
    svc.save_meal_consumption_logs(
        db, caller=_user(10), payload=_bulk_payload(user_id=10, portion=1.5)
    )
    assert db.query(MealConsumptionLog).count() == 1
    assert db.query(MealConsumptionLog).one().portion_multiplier == 1.5


def test_ate_out_status_and_zero_portion(db, simple_resolve):
    rows = svc.save_meal_consumption_logs(
        db,
        caller=_user(10),
        payload=_bulk_payload(user_id=10, status="ate_out", portion=2.0),
    )
    assert rows[0].status == "ate_out"
    assert rows[0].portion_multiplier == 0.0


@pytest.mark.parametrize("portion", [0.5, 1.0, 1.5, 2.0])
def test_portion_multipliers(db, simple_resolve, portion: float):
    rows = svc.save_meal_consumption_logs(
        db,
        caller=_user(10),
        payload=_bulk_payload(user_id=10, portion=portion),
    )
    assert rows[0].portion_multiplier == portion


def test_get_returns_saved_logs(db, simple_resolve):
    svc.save_meal_consumption_logs(
        db, caller=_user(10), payload=_bulk_payload(user_id=10)
    )
    rows = svc.get_meal_consumption_logs(
        db,
        caller=_user(10),
        family_id=1,
        menu_selection_id=123,
        day_index=2,
    )
    assert len(rows) == 1
    assert rows[0].meal_type == "lunch"


def test_can_log_for_member_rules(db, monkeypatch):
    adult_member = _membership(role="adult")
    admin_member = _membership(role="admin")

    def membership_for(user):
        return admin_member if user.id == 1 else adult_member

    monkeypatch.setattr(svc, "_caller_membership", lambda _db, user: membership_for(user))

    target_member = SimpleNamespace(id=5, family_id=1, user_id=10)

    class FakeQuery:
        def filter(self, *_args, **_kwargs):
            return self

        def one_or_none(self):
            return target_member

    monkeypatch.setattr(db, "query", lambda _model: FakeQuery())
    monkeypatch.setattr(
        db,
        "get",
        lambda _model, _pk: target_member if _pk == 5 else None,
    )

    assert svc.can_log_for_member(
        db,
        caller=_user(10),
        family_id=1,
        target_user_id=10,
        target_family_member_id=None,
    )
    assert not svc.can_log_for_member(
        db,
        caller=_user(10),
        family_id=1,
        target_user_id=20,
        target_family_member_id=None,
    )
    assert svc.can_log_for_member(
        db,
        caller=_user(1),
        family_id=1,
        target_user_id=10,
        target_family_member_id=None,
    )
