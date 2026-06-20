"""Tests for health_intelligence foundation (Phase 4C)."""

from __future__ import annotations

import os
import sys
from datetime import date
from pathlib import Path
from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

API_ROOT = Path(__file__).resolve().parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.models.external_food_log import ExternalFoodLog  # noqa: E402
from app.models.meal_consumption_log import MealConsumptionLog  # noqa: E402
from app.services import health_intelligence as health  # noqa: E402
from app.services.app_scope import AppScope  # noqa: E402


@pytest.fixture()
def db():
    engine = create_engine("sqlite:///:memory:")
    MealConsumptionLog.__table__.create(engine)
    ExternalFoodLog.__table__.create(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_no_logs_returns_no_fact_data():
    status = health.resolve_health_status(
        has_logs=False,
        skipped=0,
        ate_out=0,
        external_confirmed=False,
        logged_meals=0,
        planned_meals=3,
    )
    assert status == "no_fact_data"


def test_on_plan_when_eaten_only():
    status = health.resolve_health_status(
        has_logs=True,
        skipped=0,
        ate_out=0,
        external_confirmed=False,
        logged_meals=3,
        planned_meals=3,
    )
    assert status == "on_plan"


def test_skipped_off_plan():
    status = health.resolve_health_status(
        has_logs=True,
        skipped=1,
        ate_out=0,
        external_confirmed=False,
        logged_meals=1,
        planned_meals=3,
    )
    assert status == "off_plan_due_to_skip"


def test_external_food_off_plan():
    status = health.resolve_health_status(
        has_logs=False,
        skipped=0,
        ate_out=0,
        external_confirmed=True,
        logged_meals=0,
        planned_meals=3,
    )
    assert status == "off_plan_due_to_external_food"


def test_recommendations_no_fact_data():
    tips = health.build_health_recommendations(
        status="no_fact_data",
        skipped=0,
        ate_out=0,
        not_logged=3,
        remaining_kcal=None,
        protein_gap=None,
    )
    assert any("не отмечен" in t.lower() for t in tips)


def test_recommendations_on_plan():
    tips = health.build_health_recommendations(
        status="on_plan",
        skipped=0,
        ate_out=0,
        not_logged=0,
        remaining_kcal=100,
        protein_gap=0,
    )
    assert any("по плану" in t.lower() for t in tips)
