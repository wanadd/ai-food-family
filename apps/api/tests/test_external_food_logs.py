"""Tests for external_food_logs foundation (Phase 4C)."""

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
from app.schemas.external_food_log import ExternalFoodLogCreateIn  # noqa: E402
from app.services import external_food_logs as svc  # noqa: E402


@pytest.fixture()
def db():
    engine = create_engine("sqlite:///:memory:")
    ExternalFoodLog.__table__.create(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def _user(user_id: int = 10) -> SimpleNamespace:
    return SimpleNamespace(id=user_id)


def test_create_draft_external_food(db):
    row = svc.create_external_food_log(
        db,
        caller=_user(10),
        payload=ExternalFoodLogCreateIn(
            planned_date=date(2026, 6, 14),
            input_text="бургер и кофе",
            status="draft",
        ),
    )
    assert row.status == "draft"
    assert row.input_text == "бургер и кофе"


def test_confirm_external_food(db):
    row = svc.create_external_food_log(
        db,
        caller=_user(10),
        payload=ExternalFoodLogCreateIn(
            planned_date=date(2026, 6, 14),
            input_text="салат",
            status="draft",
        ),
    )
    confirmed = svc.confirm_external_food_log(db, caller=_user(10), log_id=row.id)
    assert confirmed.status == "confirmed"


def test_draft_not_in_confirmed_list(db):
    svc.create_external_food_log(
        db,
        caller=_user(10),
        payload=ExternalFoodLogCreateIn(
            planned_date=date(2026, 6, 14),
            input_text="draft only",
            status="draft",
        ),
    )
    confirmed = svc.list_external_food_logs(
        db,
        caller=_user(10),
        planned_date=date(2026, 6, 14),
        status_filter="confirmed",
    )
    assert confirmed == []
