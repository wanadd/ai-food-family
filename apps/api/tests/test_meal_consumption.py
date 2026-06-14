"""Tests for meal consumption logs (Phase 2A + personal hotfix)."""

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
    family_id: int | None = 1,
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
        "_estimate_nutrition",
        lambda *_args, **_kwargs: (None, None, None, None),
    )


def test_personal_save_without_family_id(db):
    rows = svc.save_meal_consumption_logs(
        db, caller=_user(10), payload=_bulk_payload(family_id=None, user_id=10)
    )
    assert len(rows) == 1
    assert rows[0].family_id is None
    assert rows[0].user_id == 10
    assert rows[0].family_member_id is None


def test_personal_get_without_family_id(db):
    svc.save_meal_consumption_logs(
        db, caller=_user(10), payload=_bulk_payload(family_id=None, user_id=10)
    )
    rows = svc.get_meal_consumption_logs(
        db,
        caller=_user(10),
        family_id=None,
        menu_selection_id=123,
        day_index=2,
    )
    assert len(rows) == 1
    assert rows[0].user_id == 10


def test_personal_upsert_without_family_id(db):
    svc.save_meal_consumption_logs(
        db, caller=_user(10), payload=_bulk_payload(family_id=None, user_id=10, portion=1.0)
    )
    svc.save_meal_consumption_logs(
        db, caller=_user(10), payload=_bulk_payload(family_id=None, user_id=10, portion=1.5)
    )
    assert db.query(MealConsumptionLog).count() == 1
    assert db.query(MealConsumptionLog).one().portion_multiplier == 1.5


def test_personal_cannot_save_for_other_user(db):
    with pytest.raises(HTTPException) as exc:
        svc.save_meal_consumption_logs(
            db, caller=_user(10), payload=_bulk_payload(family_id=None, user_id=20)
        )
    assert exc.value.status_code == 403
    assert exc.value.detail == svc.PERMISSION_DENIED


def test_personal_cannot_save_family_member_id(db):
    with pytest.raises(HTTPException) as exc:
        svc.save_meal_consumption_logs(
            db,
            caller=_user(10),
            payload=_bulk_payload(family_id=None, user_id=None, family_member_id=3),
        )
    assert exc.value.status_code == 403


def test_user_saves_for_self_in_family(db, monkeypatch):
    monkeypatch.setattr(svc, "_caller_membership", lambda _db, _user: _membership())
    rows = svc.save_meal_consumption_logs(
        db, caller=_user(10), payload=_bulk_payload(user_id=10)
    )
    assert rows[0].user_id == 10
    assert rows[0].family_id == 1


def test_admin_saves_for_virtual_member(db, monkeypatch):
    virtual = SimpleNamespace(
        id=3, family_id=1, user_id=None, is_virtual=True, role="child"
    )
    monkeypatch.setattr(svc, "_caller_membership", lambda _db, _user: _membership(role="admin"))
    monkeypatch.setattr(
        "sqlalchemy.orm.session.Session.get",
        lambda _self, model, pk: virtual if pk == 3 else None,
    )

    rows = svc.save_meal_consumption_logs(
        db,
        caller=_user(1),
        payload=_bulk_payload(user_id=None, family_member_id=3),
    )
    assert rows[0].family_member_id == 3
    assert rows[0].user_id is None


def test_admin_cannot_save_for_other_real_user(db, monkeypatch):
    monkeypatch.setattr(svc, "_caller_membership", lambda _db, _user: _membership(role="admin"))
    with pytest.raises(HTTPException) as exc:
        svc.save_meal_consumption_logs(
            db, caller=_user(1), payload=_bulk_payload(user_id=20)
        )
    assert exc.value.status_code == 403
    assert exc.value.detail == svc.PERMISSION_DENIED


def test_adult_cannot_save_virtual_member(db, monkeypatch):
    virtual = SimpleNamespace(
        id=3, family_id=1, user_id=None, is_virtual=True, role="child"
    )
    monkeypatch.setattr(svc, "_caller_membership", lambda _db, _user: _membership(role="adult"))
    monkeypatch.setattr(
        "sqlalchemy.orm.session.Session.get",
        lambda _self, model, pk: virtual if pk == 3 else None,
    )
    with pytest.raises(HTTPException) as exc:
        svc.save_meal_consumption_logs(
            db,
            caller=_user(10),
            payload=_bulk_payload(user_id=None, family_member_id=3),
        )
    assert exc.value.status_code == 403


def test_user_cannot_save_outside_family(db, monkeypatch):
    monkeypatch.setattr(svc, "_caller_membership", lambda _db, _user: _membership())
    with pytest.raises(HTTPException) as exc:
        svc.save_meal_consumption_logs(
            db, caller=_user(10), payload=_bulk_payload(family_id=99, user_id=10)
        )
    assert exc.value.status_code == 403
    assert exc.value.detail == svc.FAMILY_ACCESS_DENIED


def test_upsert_updates_not_duplicates(db, monkeypatch):
    monkeypatch.setattr(svc, "_caller_membership", lambda _db, _user: _membership())
    svc.save_meal_consumption_logs(
        db, caller=_user(10), payload=_bulk_payload(user_id=10, portion=1.0)
    )
    svc.save_meal_consumption_logs(
        db, caller=_user(10), payload=_bulk_payload(user_id=10, portion=1.5)
    )
    assert db.query(MealConsumptionLog).count() == 1


def test_ate_out_status_and_zero_portion(db, monkeypatch):
    monkeypatch.setattr(svc, "_caller_membership", lambda _db, _user: _membership())
    rows = svc.save_meal_consumption_logs(
        db,
        caller=_user(10),
        payload=_bulk_payload(user_id=10, status="ate_out", portion=2.0),
    )
    assert rows[0].status == "ate_out"
    assert rows[0].portion_multiplier == 0.0


@pytest.mark.parametrize("portion", [0.5, 1.0, 1.5, 2.0])
def test_portion_multipliers(db, monkeypatch, portion: float):
    monkeypatch.setattr(svc, "_caller_membership", lambda _db, _user: _membership())
    rows = svc.save_meal_consumption_logs(
        db,
        caller=_user(10),
        payload=_bulk_payload(user_id=10, portion=portion),
    )
    assert rows[0].portion_multiplier == portion


def test_get_returns_only_current_user_logs(db, monkeypatch):
    monkeypatch.setattr(svc, "_caller_membership", lambda _db, _user: _membership())
    svc.save_meal_consumption_logs(
        db, caller=_user(10), payload=_bulk_payload(user_id=10)
    )
    other = MealConsumptionLog(
        family_id=1,
        user_id=20,
        logged_by_user_id=1,
        meal_type="dinner",
        status="eaten",
        portion_multiplier=1,
    )
    db.add(other)
    db.commit()

    rows = svc.get_meal_consumption_logs(db, caller=_user(10), family_id=1)
    assert len(rows) == 1
    assert rows[0].user_id == 10


def test_can_log_for_member_rules(db, monkeypatch):
    adult_member = _membership(role="adult")
    admin_member = _membership(role="admin")
    virtual = SimpleNamespace(
        id=5, family_id=1, user_id=None, is_virtual=True, role="child"
    )

    def membership_for(user):
        return admin_member if user.id == 1 else adult_member

    monkeypatch.setattr(svc, "_caller_membership", lambda _db, user: membership_for(user))
    monkeypatch.setattr(
        "sqlalchemy.orm.session.Session.get",
        lambda _self, model, pk: virtual if pk == 5 else None,
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
    assert not svc.can_log_for_member(
        db,
        caller=_user(1),
        family_id=1,
        target_user_id=10,
        target_family_member_id=None,
    )
    assert svc.can_log_for_member(
        db,
        caller=_user(1),
        family_id=1,
        target_user_id=None,
        target_family_member_id=5,
    )
    assert svc.can_log_for_member(
        db,
        caller=_user(10),
        family_id=None,
        target_user_id=10,
        target_family_member_id=None,
    )
