"""Tests for menu day/week nutrition aggregation."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

API_ROOT = Path(__file__).resolve().parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.database import Base  # noqa: E402
from app.models.progress import NutritionTarget  # noqa: E402
from app.schemas.menu_nutrition import (  # noqa: E402
    DayNutritionResponse,
    WeekNutritionResponse,
)
from app.services.nutrition import plan_aggregator as agg  # noqa: E402

FALLBACK = agg.FALLBACK_TARGETS
TARGETS = {"kcal": 2200, "protein": 130, "fat": 80, "carbs": 240}


def _recipe(kcal, p, f, c, conf):
    return {
        "kcal_per_serving": kcal,
        "protein_per_serving": p,
        "fat_per_serving": f,
        "carbs_per_serving": c,
        "confidence": conf,
    }


# --------------------------- pure core ---------------------------

def test_empty_menu_totals_zero():
    day = agg.aggregate_day("2026-06-07", [], {}, TARGETS)
    assert day["totals"] == {"kcal": 0, "protein": 0, "fat": 0, "carbs": 0}
    assert day["confidence"] == "unavailable"
    assert day["coverage"]["total_items"] == 0
    assert day["warnings"] == []  # empty state handled by UI


def test_one_exact_recipe():
    rmap = {1: _recipe(500, 30, 20, 40, "exact")}
    items = [{"recipe_id": 1, "meal_type": "lunch", "name": "Курица"}]
    day = agg.aggregate_day("2026-06-07", items, rmap, TARGETS)
    assert day["totals"]["kcal"] == 500
    assert day["confidence"] == "exact"
    assert day["progress"]["kcal_pct"] == round(500 / 2200 * 100)


def test_serving_multiplier_applied():
    rmap = {1: _recipe(300, 10, 10, 30, "exact"), 2: _recipe(200, 5, 5, 20, "exact")}
    items = [
        {"recipe_id": 1, "meal_type": "lunch", "name": "A", "serving_multiplier": 2.0},
        {"recipe_id": 2, "meal_type": "dinner", "name": "B", "serving_multiplier": 1.0},
    ]
    day = agg.aggregate_day("2026-06-07", items, rmap, TARGETS)
    assert day["totals"]["kcal"] == 300 * 2 + 200  # 800


def test_unavailable_recipe_not_counted_as_zero():
    rmap = {
        1: _recipe(500, 30, 20, 40, "exact"),
        2: _recipe(None, None, None, None, "unavailable"),
    }
    items = [
        {"recipe_id": 1, "meal_type": "lunch", "name": "A"},
        {"recipe_id": 2, "meal_type": "dinner", "name": "B"},
    ]
    day = agg.aggregate_day("2026-06-07", items, rmap, TARGETS)
    assert day["totals"]["kcal"] == 500  # unavailable excluded, not added as 0
    assert day["coverage"]["unavailable_items"] == 1
    assert day["coverage"]["calculated_items"] == 1
    assert day["confidence"] in {"low_confidence", "unavailable"}


def test_low_confidence_counted_but_lowers_confidence():
    rmap = {
        1: _recipe(400, 20, 15, 30, "estimated"),
        2: _recipe(350, 10, 12, 40, "low_confidence"),
    }
    items = [
        {"recipe_id": 1, "meal_type": "lunch", "name": "A"},
        {"recipe_id": 2, "meal_type": "dinner", "name": "B"},
    ]
    day = agg.aggregate_day("2026-06-07", items, rmap, TARGETS)
    assert day["totals"]["kcal"] == 750  # low_confidence still counted
    assert day["coverage"]["low_confidence_items"] == 1
    assert day["confidence"] in {"estimated", "low_confidence"}


def test_day_schema_valid():
    rmap = {1: _recipe(500, 30, 20, 40, "exact")}
    items = [{"recipe_id": 1, "meal_type": "lunch", "name": "Курица"}]
    day = agg.aggregate_day("2026-06-07", items, rmap, TARGETS)
    model = DayNutritionResponse(**day)
    assert model.confidence == "exact"
    assert model.totals.kcal == 500


def test_week_aggregation_and_schema():
    rmap = {1: _recipe(500, 30, 20, 40, "exact")}
    items = [{"recipe_id": 1, "meal_type": "lunch", "name": "A"}]
    days = [agg.aggregate_day(f"2026-06-0{i}", items, rmap, TARGETS) for i in range(3, 6)]
    days += [agg.aggregate_day("2026-06-06", [], {}, TARGETS)]  # one empty day
    week = agg.aggregate_week("2026-06-03", "2026-06-09", days)
    assert week["weekly_total"]["kcal"] == 1500  # 3 days x 500
    assert week["weekly_average"]["kcal"] == 500  # averaged over days with data
    model = WeekNutritionResponse(**week)
    assert model.start_date == "2026-06-03"


def test_meals_grouped_with_other():
    rmap = {1: _recipe(300, 10, 10, 30, "exact")}
    items = [
        {"recipe_id": 1, "meal_type": "breakfast", "name": "A"},
        {"recipe_id": 1, "meal_type": "dessert", "name": "B"},  # -> other
    ]
    day = agg.aggregate_day("2026-06-07", items, rmap, TARGETS)
    meal_types = {m["meal_type"] for m in day["meals"]}
    assert "breakfast" in meal_types
    assert "other" in meal_types


# --------------------------- targets resolver (DB) ---------------------------

@pytest.fixture()
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine, tables=[NutritionTarget.__table__])
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()


def test_resolve_targets_fallback_when_missing(db_session):
    targets = agg.resolve_targets(db_session, user_id=999)
    assert targets == FALLBACK  # kcal 2200, macros None — not persisted
    assert db_session.query(NutritionTarget).count() == 0  # nothing written


def test_resolve_targets_uses_existing_row(db_session):
    db_session.add(
        NutritionTarget(
            user_id=1, calories_target=1800, protein_target_g=120,
            fat_target_g=60, carbs_target_g=200,
        )
    )
    db_session.commit()
    targets = agg.resolve_targets(db_session, user_id=1)
    assert targets == {"kcal": 1800, "protein": 120, "fat": 60, "carbs": 200}


# --------------------------- nutritionist context ---------------------------

def test_nutrition_context_fields():
    rmap = {
        1: _recipe(500, 30, 20, 40, "exact"),
        2: _recipe(350, 10, 12, 40, "low_confidence"),
    }
    items = [
        {"recipe_id": 1, "meal_type": "lunch", "name": "A"},
        {"recipe_id": 2, "meal_type": "dinner", "name": "B"},
    ]
    day = agg.aggregate_day("2026-06-07", items, rmap, TARGETS)
    week = agg.aggregate_week("2026-06-07", "2026-06-13", [day])
    ctx = agg.shape_nutrition_context(day, week)
    assert ctx["date"] == "2026-06-07"
    assert "day_totals" in ctx and "week_average" in ctx
    assert ctx["goals"] == TARGETS
    assert ctx["deltas"]["kcal"]["status"] == "deficit"  # 850 < 2200
    assert any(r["confidence"] == "low_confidence" for r in ctx["top_low_confidence_recipes"])
