"""Tests for meal consumption nutrition summary (Phase 2B)."""

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
def _patch_membership(monkeypatch):
    monkeypatch.setattr(
        svc,
        "_caller_membership",
        lambda _db, _user: SimpleNamespace(family_id=1, role="adult"),
    )
    monkeypatch.setattr(
        svc,
        "build_day_nutrition",
        lambda _db, _uid, _scope, _date: _day_plan(),
    )


def _patch_logs(monkeypatch, logs: list[MealConsumptionLog]):
    monkeypatch.setattr(svc, "get_meal_consumption_logs", lambda *_a, **_k: logs)


def _log(
    *,
    user_id: int = 10,
    status: str = "eaten",
    portion: float = 1.0,
    calories: float | None = 400.0,
    protein: float | None = 25.0,
    fat: float | None = 15.0,
    carbs: float | None = 40.0,
    recipe_id: int = 1,
) -> MealConsumptionLog:
    return MealConsumptionLog(
        family_id=1,
        user_id=user_id,
        logged_by_user_id=10,
        menu_selection_id=123,
        day_index=2,
        planned_date=date(2026, 6, 14),
        meal_type="lunch",
        recipe_id=recipe_id,
        recipe_title="Суп",
        status=status,
        portion_multiplier=portion,
        calories_estimated=calories,
        protein_estimated=protein,
        fat_estimated=fat,
        carbs_estimated=carbs,
    )


def _summary(db, monkeypatch, logs: list[MealConsumptionLog] | None = None):
    _patch_logs(monkeypatch, logs or [])
    return svc.get_meal_consumption_nutrition_summary(
        db,
        caller=SimpleNamespace(id=10),
        scope=SimpleNamespace(mode="family", user_id=10, family_id=1),
        family_id=1,
        menu_selection_id=123,
        day_index=2,
        planned_date=date(2026, 6, 14),
    )


def test_no_logs_mode_planned(db, monkeypatch):
    data = _summary(db, monkeypatch)
    assert data["mode"] == "planned"
    assert data["has_consumption_logs"] is False
    assert data["actual"] is None
    assert data["planned"]["calories"] == 1850
    assert data["counts"]["logged_meals"] == 0


def test_eaten_portion_1_uses_stored_macros(db, monkeypatch):
    data = _summary(db, monkeypatch, [_log(portion=1.0, calories=400)])
    assert data["mode"] == "actual"
    assert data["actual"]["calories"] == 400
    assert data["counts"]["eaten"] == 1


def test_eaten_portion_half(db, monkeypatch):
    data = _summary(db, monkeypatch, [_log(portion=0.5, calories=200)])
    assert data["actual"]["calories"] == 200


def test_eaten_portion_one_and_half(db, monkeypatch):
    data = _summary(db, monkeypatch, [_log(portion=1.5, calories=600)])
    assert data["actual"]["calories"] == 600


def test_skipped_not_in_actual(db, monkeypatch):
    data = _summary(db, monkeypatch, [_log(status="skipped", calories=None)])
    assert data["actual"]["calories"] == 0
    assert data["counts"]["skipped"] == 1
    assert data["counts"]["eaten"] == 0


def test_ate_out_not_in_actual_but_counted(db, monkeypatch):
    data = _summary(db, monkeypatch, [_log(status="ate_out", calories=None)])
    assert data["actual"]["calories"] == 0
    assert data["counts"]["ate_out"] == 1


def test_upsert_single_log_not_doubled(db, monkeypatch):
    log = _log(calories=500)
    data = _summary(db, monkeypatch, [log])
    assert data["actual"]["calories"] == 500
    assert data["counts"]["logged_meals"] == 1


def test_logged_vs_planned_counts(db, monkeypatch):
    data = _summary(db, monkeypatch, [_log()])
    assert data["counts"]["planned_meals"] == 3
    assert data["counts"]["logged_meals"] == 1


def test_other_family_forbidden(db, monkeypatch):
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


def test_only_current_user_logs(db, monkeypatch):
    logs = [
        _log(user_id=10, calories=300),
        _log(user_id=20, calories=900),
    ]
    data = _summary(db, monkeypatch, logs)
    assert data["actual"]["calories"] == 300
    assert data["counts"]["logged_meals"] == 1


def test_fallback_estimate_when_macros_missing(db, monkeypatch):
    monkeypatch.setattr(
        svc,
        "_estimate_nutrition",
        lambda *_a, **_k: (320.0, 20.0, 12.0, 35.0),
    )
    log = _log(calories=None, protein=None, fat=None, carbs=None)
    data = _summary(db, monkeypatch, [log])
    assert data["actual"]["calories"] == 320
