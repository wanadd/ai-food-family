"""Wellness actual intake uses one source and avoids double counting."""

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

from app.models.meal_checkin import MealCheckin  # noqa: E402
from app.models.meal_consumption_log import MealConsumptionLog  # noqa: E402
from app.models.recipe_engine import RecipeHistory  # noqa: E402
from app.services.app_scope import AppScope  # noqa: E402
from app.services.meal_daily_nutrition import compute_today_nutrition_actual  # noqa: E402


@pytest.fixture()
def db():
    engine = create_engine("sqlite:///:memory:")
    MealCheckin.__table__.create(engine)
    MealConsumptionLog.__table__.create(engine)
    RecipeHistory.__table__.create(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(autouse=True)
def _no_water(monkeypatch):
    import app.services.meal_daily_nutrition as svc

    monkeypatch.setattr(svc, "sum_water_for_date", lambda *_args, **_kwargs: 0)


def _scope() -> AppScope:
    return AppScope(mode="personal", user_id=10, family_id=None)


def _user() -> SimpleNamespace:
    return SimpleNamespace(id=10)


def _consumption(status: str = "eaten", *, meal_type: str = "lunch") -> MealConsumptionLog:
    return MealConsumptionLog(
        family_id=None,
        user_id=10,
        family_member_id=None,
        logged_by_user_id=10,
        planned_date=date.today(),
        meal_type=meal_type,
        recipe_id=1,
        recipe_title="Soup",
        status=status,
        portion_multiplier=1,
        calories_estimated=420 if status == "eaten" else None,
        protein_estimated=30 if status == "eaten" else None,
        fat_estimated=12 if status == "eaten" else None,
        carbs_estimated=45 if status == "eaten" else None,
    )


def _checkin(status: str, *, meal_type: str = "lunch") -> MealCheckin:
    return MealCheckin(
        user_id=10,
        family_id=None,
        meal_type=meal_type,
        planned_date=date.today(),
        actual_status=status,
        actual_calories=500,
        actual_protein_g=25,
        actual_fat_g=15,
        actual_carbs_g=50,
    )


def test_bulk_eaten_updates_wellness_daily_actual_calories(db):
    db.add(_consumption("eaten"))
    db.commit()

    actual = compute_today_nutrition_actual(db, _user(), _scope())

    assert actual.calories_consumed == 420
    assert actual.meals_logged == 1


def test_bulk_skipped_does_not_add_calories(db):
    db.add(_consumption("skipped"))
    db.commit()

    actual = compute_today_nutrition_actual(db, _user(), _scope())

    assert actual.calories_consumed == 0
    assert actual.meals_logged == 0


def test_cooked_does_not_add_calories(db):
    db.add(_checkin("cooked"))
    db.commit()

    actual = compute_today_nutrition_actual(db, _user(), _scope())

    assert actual.calories_consumed == 0


def test_recipe_cooked_history_does_not_add_calories(db):
    db.add(
        RecipeHistory(
            recipe_id=1,
            user_id=10,
            family_id=None,
            cooked_on=date.today(),
            servings=2,
            source="manual",
        )
    )
    db.commit()

    actual = compute_today_nutrition_actual(db, _user(), _scope())

    assert actual.calories_consumed == 0


def test_same_meal_cannot_be_double_counted_through_both_sources(db):
    db.add(_consumption("eaten", meal_type="lunch"))
    db.add(_checkin("ate_home", meal_type="lunch"))
    db.commit()

    actual = compute_today_nutrition_actual(db, _user(), _scope())

    assert actual.calories_consumed == 420
    assert actual.meals_logged == 1


def test_saved_as_leftover_does_not_increase_daily_actual_calories(db):
    db.add(_checkin("saved_as_leftover"))
    db.commit()

    actual = compute_today_nutrition_actual(db, _user(), _scope())

    assert actual.calories_consumed == 0


def test_ate_home_increases_daily_actual_calories(db):
    db.add(_checkin("ate_home"))
    db.commit()

    actual = compute_today_nutrition_actual(db, _user(), _scope())

    assert actual.calories_consumed == 500


def test_skipped_does_not_increase_calories(db):
    db.add(_checkin("skipped"))
    db.commit()

    actual = compute_today_nutrition_actual(db, _user(), _scope())

    assert actual.calories_consumed == 0
