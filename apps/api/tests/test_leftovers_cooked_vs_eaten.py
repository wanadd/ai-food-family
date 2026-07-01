"""Prepared stock is not eaten nutrition."""

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

from app.models.cooking_batch import CookingBatch, CookingBatchEvent  # noqa: E402
from app.models.meal_checkin import MealCheckin  # noqa: E402
from app.models.meal_consumption_log import MealConsumptionLog  # noqa: E402
from app.models.pantry import FamilyPantryItem  # noqa: E402
from app.schemas.leftovers import CookingBatchCreateIn  # noqa: E402
from app.services import leftovers as leftovers_service  # noqa: E402
from app.services.app_scope import AppScope  # noqa: E402
from app.services.meal_daily_nutrition import compute_today_nutrition_actual  # noqa: E402


@pytest.fixture()
def db():
    engine = create_engine("sqlite:///:memory:")
    CookingBatch.__table__.create(engine)
    CookingBatchEvent.__table__.create(engine)
    MealConsumptionLog.__table__.create(engine)
    MealCheckin.__table__.create(engine)
    FamilyPantryItem.__table__.create(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(autouse=True)
def _mock_pantry_list(monkeypatch):
    from app.schemas.pantry import PantryListResponse

    monkeypatch.setattr(
        leftovers_service,
        "list_pantry",
        lambda _db, _user, scope: PantryListResponse(
            scope_mode=scope.mode,
            user_id=scope.user_id,
            family_id=scope.family_id,
            items=[],
            active_count=0,
            expired_count=0,
        ),
    )
    import app.services.meal_daily_nutrition as nutrition_svc

    monkeypatch.setattr(
        nutrition_svc,
        "sum_water_for_date",
        lambda *_args, **_kwargs: 0,
    )


def _scope() -> AppScope:
    return AppScope(mode="personal", user_id=10, family_id=None)


def _user() -> SimpleNamespace:
    return SimpleNamespace(id=10)


def test_add_to_prepared_stock_creates_cooking_batch(db):
    batch = leftovers_service.create_or_get_cooking_batch(
        db,
        caller=_user(),
        scope=_scope(),
        payload=CookingBatchCreateIn(
            recipe_id=260,
            recipe_title="Chicken",
            menu_selection_id=1,
            day_index=1,
            planned_date=date.today(),
            meal_type="dinner",
            total_servings=3,
        ),
    )

    assert batch.id is not None
    assert db.query(CookingBatch).count() == 1


def test_prepared_stock_does_not_affect_wellness_eaten_calories(db):
    leftovers_service.create_or_get_cooking_batch(
        db,
        caller=_user(),
        scope=_scope(),
        payload=CookingBatchCreateIn(
            recipe_id=260,
            recipe_title="Chicken",
            menu_selection_id=1,
            day_index=1,
            planned_date=date.today(),
            meal_type="dinner",
            total_servings=3,
        ),
    )

    actual = compute_today_nutrition_actual(db, _user(), _scope())

    assert actual.calories_consumed == 0


def test_leftovers_overview_uses_cooking_batches(db):
    leftovers_service.create_or_get_cooking_batch(
        db,
        caller=_user(),
        scope=_scope(),
        payload=CookingBatchCreateIn(
            recipe_id=260,
            recipe_title="Chicken",
            menu_selection_id=1,
            day_index=1,
            planned_date=date.today(),
            meal_type="dinner",
            total_servings=3,
        ),
    )

    overview = leftovers_service.list_stock_overview(db, _user(), _scope())

    assert overview.summary.prepared_dishes_count == 1
    assert overview.prepared_dishes[0].source == "cooking_batch"
