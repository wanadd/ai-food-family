"""Tests for meal consumption nutrition summary (Phase 2B + personal hotfix)."""

from __future__ import annotations

import os
import sys
from datetime import date
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

API_ROOT = Path(__file__).resolve().parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.models.meal_consumption_log import MealConsumptionLog  # noqa: E402
from app.services import meal_consumption_nutrition as svc  # noqa: E402


def _day_plan(*, kcal: int = 1850, meals: int = 3) -> dict:
    return {
        "totals": {"kcal": kcal, "protein": 120, "fat": 70, "carbs": 180},
        "targets": {"kcal": 2200, "protein": None, "fat": None, "carbs": None},
        "coverage": {"total_items": meals},
    }


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


@pytest.fixture(autouse=True)
def _patch_build_day(monkeypatch):
    monkeypatch.setattr(
        svc,
        "build_day_nutrition",
        lambda _db, _uid, _scope, _date: _day_plan(),
    )


def _log(
    *,
    user_id: int | None = 10,
    family_id: int | None = 1,
    family_member_id: int | None = None,
    status: str = "eaten",
    calories: float | None = 400.0,
) -> MealConsumptionLog:
    return MealConsumptionLog(
        family_id=family_id,
        user_id=user_id,
        family_member_id=family_member_id,
        logged_by_user_id=10,
        menu_selection_id=123,
        day_index=2,
        planned_date=date(2026, 6, 14),
        meal_type="lunch",
        recipe_id=1,
        recipe_title="Суп",
        status=status,
        portion_multiplier=1,
        calories_estimated=calories,
        protein_estimated=25,
        fat_estimated=15,
        carbs_estimated=40,
    )


def _summary(db, monkeypatch, logs: list[MealConsumptionLog], *, family_id: int | None = 1):
    monkeypatch.setattr(svc, "get_meal_consumption_logs", lambda *_a, **_k: logs)
    if family_id is not None:
        monkeypatch.setattr(
            svc,
            "_caller_membership",
            lambda _db, _user: SimpleNamespace(family_id=family_id, role="adult"),
        )
    return svc.get_meal_consumption_nutrition_summary(
        db,
        caller=SimpleNamespace(id=10),
        scope=SimpleNamespace(mode="personal", user_id=10, family_id=None),
        family_id=family_id,
        menu_selection_id=123,
        day_index=2,
        planned_date=date(2026, 6, 14),
    )


def test_no_logs_mode_planned(db, monkeypatch):
    data = _summary(db, monkeypatch, [])
    assert data["mode"] == "planned"
    assert data["actual"] is None


def test_personal_mode_actual_after_save(db, monkeypatch):
    data = _summary(db, monkeypatch, [_log(family_id=None)], family_id=None)
    assert data["mode"] == "actual"
    assert data["actual"]["calories"] == 400


def test_eaten_portion_counts(db, monkeypatch):
    data = _summary(db, monkeypatch, [_log(calories=400)])
    assert data["actual"]["calories"] == 400


def test_skipped_not_in_actual(db, monkeypatch):
    data = _summary(db, monkeypatch, [_log(status="skipped", calories=None)])
    assert data["actual"]["calories"] == 0
    assert data["counts"]["skipped"] == 1


def test_ate_out_count_only(db, monkeypatch):
    data = _summary(db, monkeypatch, [_log(status="ate_out", calories=None)])
    assert data["actual"]["calories"] == 0
    assert data["counts"]["ate_out"] == 1


def test_virtual_member_logs_not_in_current_user_summary(db, monkeypatch):
    logs = [
        _log(user_id=10, calories=300),
        _log(user_id=None, family_member_id=5, calories=900),
    ]
    data = _summary(db, monkeypatch, logs)
    assert data["actual"]["calories"] == 300
    assert data["counts"]["logged_meals"] == 1


def test_other_family_forbidden(db, monkeypatch):
    monkeypatch.setattr(
        svc,
        "_caller_membership",
        lambda _db, _user: SimpleNamespace(family_id=1, role="adult"),
    )
    with pytest.raises(HTTPException) as exc:
        svc.get_meal_consumption_nutrition_summary(
            db,
            caller=SimpleNamespace(id=10),
            scope=SimpleNamespace(mode="family", user_id=10, family_id=1),
            family_id=99,
            menu_selection_id=123,
            day_index=2,
            planned_date=date(2026, 6, 14),
        )
    assert exc.value.status_code == 403
