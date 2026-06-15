"""Tests for cooking_batches prepared leftovers (Phase 4A)."""

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

from app.models.cooking_batch import CookingBatch, CookingBatchEvent  # noqa: E402
from app.models.meal_consumption_log import MealConsumptionLog  # noqa: E402
from app.models.pantry import FamilyPantryItem  # noqa: E402
from app.schemas.leftovers import (  # noqa: E402
    CookingBatchAdjustIn,
    CookingBatchCreateIn,
    CookingBatchUseIn,
)
from app.services import leftovers as svc  # noqa: E402
from app.services.app_scope import AppScope  # noqa: E402


@pytest.fixture()
def db():
    engine = create_engine("sqlite:///:memory:")
    CookingBatch.__table__.create(engine)
    CookingBatchEvent.__table__.create(engine)
    MealConsumptionLog.__table__.create(engine)
    FamilyPantryItem.__table__.create(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def _user(user_id: int = 10) -> SimpleNamespace:
    return SimpleNamespace(id=user_id)


def _scope_personal(user_id: int = 10) -> AppScope:
    return AppScope(mode="personal", user_id=user_id, family_id=None)


def _scope_family(user_id: int = 10, family_id: int = 1) -> AppScope:
    return AppScope(mode="family", user_id=user_id, family_id=family_id)


def _membership(family_id: int = 1, role: str = "admin") -> SimpleNamespace:
    return SimpleNamespace(family_id=family_id, role=role)


def _create_payload(**kwargs) -> CookingBatchCreateIn:
    defaults = {
        "family_id": None,
        "recipe_id": 260,
        "recipe_title": "Курица с брокколи",
        "menu_selection_id": 123,
        "day_index": 1,
        "planned_date": date(2026, 6, 14),
        "meal_type": "dinner",
        "total_servings": 4.0,
    }
    defaults.update(kwargs)
    return CookingBatchCreateIn(**defaults)


@pytest.fixture(autouse=True)
def _mock_pantry_list(monkeypatch):
    from app.schemas.pantry import PantryListResponse

    monkeypatch.setattr(
        svc,
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


def test_personal_create_batch_without_family_id(db):
    batch = svc.create_or_get_cooking_batch(
        db,
        caller=_user(10),
        scope=_scope_personal(10),
        payload=_create_payload(),
    )
    assert batch.family_id is None
    assert batch.owner_user_id == 10
    assert batch.remaining_servings == 4.0
    assert batch.batch_status == "active"
    assert db.query(CookingBatchEvent).filter_by(event_type="created").count() == 1


def test_personal_sees_prepared_in_overview(db):
    svc.create_or_get_cooking_batch(
        db,
        caller=_user(10),
        scope=_scope_personal(10),
        payload=_create_payload(),
    )
    overview = svc.list_stock_overview(db, _user(10), _scope_personal(10))
    assert len(overview.prepared_dishes) == 1
    assert overview.summary.prepared_dishes_count == 1


def test_personal_records_usage(db):
    batch = svc.create_or_get_cooking_batch(
        db,
        caller=_user(10),
        scope=_scope_personal(10),
        payload=_create_payload(total_servings=4),
    )
    updated = svc.record_cooking_batch_usage(
        db,
        caller=_user(10),
        scope=_scope_personal(10),
        batch_id=batch.id,
        payload=CookingBatchUseIn(servings_used=1),
    )
    assert updated.remaining_servings == 3.0


def test_remaining_cannot_go_negative(db):
    batch = svc.create_or_get_cooking_batch(
        db,
        caller=_user(10),
        scope=_scope_personal(10),
        payload=_create_payload(total_servings=2),
    )
    updated = svc.record_cooking_batch_usage(
        db,
        caller=_user(10),
        scope=_scope_personal(10),
        batch_id=batch.id,
        payload=CookingBatchUseIn(servings_used=5),
    )
    assert updated.remaining_servings == 0.0
    assert updated.batch_status == "finished"


def test_adjust_remaining(db):
    batch = svc.create_or_get_cooking_batch(
        db,
        caller=_user(10),
        scope=_scope_personal(10),
        payload=_create_payload(total_servings=4),
    )
    updated = svc.adjust_cooking_batch_remaining(
        db,
        caller=_user(10),
        scope=_scope_personal(10),
        batch_id=batch.id,
        payload=CookingBatchAdjustIn(remaining_servings=1.5),
    )
    assert updated.remaining_servings == 1.5


def test_adjust_cannot_exceed_total(db):
    batch = svc.create_or_get_cooking_batch(
        db,
        caller=_user(10),
        scope=_scope_personal(10),
        payload=_create_payload(total_servings=4),
    )
    with pytest.raises(HTTPException) as exc:
        svc.adjust_cooking_batch_remaining(
            db,
            caller=_user(10),
            scope=_scope_personal(10),
            batch_id=batch.id,
            payload=CookingBatchAdjustIn(remaining_servings=5),
        )
    assert exc.value.status_code == 400


def test_finish_batch(db):
    batch = svc.create_or_get_cooking_batch(
        db,
        caller=_user(10),
        scope=_scope_personal(10),
        payload=_create_payload(),
    )
    finished = svc.finish_cooking_batch(
        db, caller=_user(10), scope=_scope_personal(10), batch_id=batch.id
    )
    assert finished.remaining_servings == 0.0
    assert finished.batch_status == "finished"


def test_discard_batch(db):
    batch = svc.create_or_get_cooking_batch(
        db,
        caller=_user(10),
        scope=_scope_personal(10),
        payload=_create_payload(),
    )
    discarded = svc.discard_cooking_batch(
        db, caller=_user(10), scope=_scope_personal(10), batch_id=batch.id
    )
    assert discarded.batch_status == "discarded"
    assert discarded.remaining_servings == 0.0


def test_repeated_create_does_not_duplicate(db):
    first = svc.create_or_get_cooking_batch(
        db,
        caller=_user(10),
        scope=_scope_personal(10),
        payload=_create_payload(),
    )
    second = svc.create_or_get_cooking_batch(
        db,
        caller=_user(10),
        scope=_scope_personal(10),
        payload=_create_payload(),
    )
    assert first.id == second.id
    assert db.query(CookingBatch).count() == 1


def test_lookup_returns_same_active_batch_after_create(db):
    created = svc.create_or_get_cooking_batch(
        db,
        caller=_user(10),
        scope=_scope_personal(10),
        payload=_create_payload(total_servings=4),
    )
    svc.record_cooking_batch_usage(
        db,
        caller=_user(10),
        scope=_scope_personal(10),
        batch_id=created.id,
        payload=CookingBatchUseIn(servings_used=2),
    )
    found = svc.lookup_active_cooking_batch(
        db,
        _scope_personal(10),
        recipe_id=260,
        menu_selection_id=123,
        day_index=1,
        meal_type="dinner",
        planned_date=date(2026, 6, 14),
    )
    assert found is not None
    assert found.id == created.id
    assert found.remaining_servings == 2.0
    assert found.total_servings == 4.0


def test_lookup_filter_by_recipe_menu_day_meal(db):
    svc.create_or_get_cooking_batch(
        db,
        caller=_user(10),
        scope=_scope_personal(10),
        payload=_create_payload(recipe_id=260, meal_type="dinner"),
    )
    svc.create_or_get_cooking_batch(
        db,
        caller=_user(10),
        scope=_scope_personal(10),
        payload=_create_payload(recipe_id=261, meal_type="lunch"),
    )
    found = svc.lookup_active_cooking_batch(
        db,
        _scope_personal(10),
        recipe_id=260,
        menu_selection_id=123,
        day_index=1,
        meal_type="dinner",
    )
    assert found is not None
    assert found.recipe_id == 260
    assert found.meal_type == "dinner"


def test_lookup_returns_none_when_finished(db):
    batch = svc.create_or_get_cooking_batch(
        db,
        caller=_user(10),
        scope=_scope_personal(10),
        payload=_create_payload(),
    )
    svc.finish_cooking_batch(
        db, caller=_user(10), scope=_scope_personal(10), batch_id=batch.id
    )
    found = svc.lookup_active_cooking_batch(
        db,
        _scope_personal(10),
        recipe_id=260,
        menu_selection_id=123,
        day_index=1,
        meal_type="dinner",
    )
    assert found is None


def test_adjust_physical_amount_cannot_exceed_total(db):
    from app.schemas.leftovers import CookingBatchCreateIn, CookingBatchAdjustIn

    batch = svc.create_or_get_cooking_batch(
        db,
        caller=_user(10),
        scope=_scope_personal(10),
        payload=CookingBatchCreateIn(
            family_id=None,
            recipe_id=260,
            recipe_title="Суп",
            menu_selection_id=123,
            day_index=1,
            planned_date=date(2026, 6, 14),
            meal_type="dinner",
            total_servings=14,
            total_amount_value=5,
            total_amount_unit="л",
            remaining_amount_value=5,
            remaining_amount_unit="л",
            yield_type="volume",
        ),
    )
    with pytest.raises(HTTPException):
        svc.adjust_cooking_batch_remaining(
            db,
            caller=_user(10),
            scope=_scope_personal(10),
            batch_id=batch.id,
            payload=CookingBatchAdjustIn(
                remaining_servings=10,
                remaining_amount_value=6,
                remaining_amount_unit="л",
            ),
        )


def test_family_admin_creates_batch(db, monkeypatch):
    monkeypatch.setattr(svc, "_membership", lambda _db, _u: _membership(role="admin"))
    batch = svc.create_or_get_cooking_batch(
        db,
        caller=_user(1),
        scope=_scope_family(1, 1),
        payload=_create_payload(family_id=1),
    )
    assert batch.family_id == 1
    assert batch.owner_user_id is None


def test_family_admin_records_usage(db, monkeypatch):
    monkeypatch.setattr(svc, "_membership", lambda _db, _u: _membership(role="admin"))
    batch = svc.create_or_get_cooking_batch(
        db,
        caller=_user(1),
        scope=_scope_family(1, 1),
        payload=_create_payload(family_id=1, total_servings=5),
    )
    updated = svc.record_cooking_batch_usage(
        db,
        caller=_user(1),
        scope=_scope_family(1, 1),
        batch_id=batch.id,
        payload=CookingBatchUseIn(servings_used=2),
    )
    assert updated.remaining_servings == 3.0


def test_family_adult_cannot_modify(db, monkeypatch):
    monkeypatch.setattr(svc, "_membership", lambda _db, _u: _membership(role="adult"))
    batch = svc.create_or_get_cooking_batch(
        db,
        caller=_user(1),
        scope=_scope_family(1, 1),
        payload=_create_payload(family_id=1),
    )
    with pytest.raises(HTTPException) as exc:
        svc.record_cooking_batch_usage(
            db,
            caller=_user(20),
            scope=_scope_family(20, 1),
            batch_id=batch.id,
            payload=CookingBatchUseIn(servings_used=1),
        )
    assert exc.value.status_code == 403


def test_user_outside_family_cannot_access(db, monkeypatch):
    monkeypatch.setattr(svc, "_membership", lambda _db, _u: None)
    with pytest.raises(HTTPException) as exc:
        svc._validate_family_access(db, _user(99), 1)
    assert exc.value.status_code == 403


def test_usage_does_not_create_meal_consumption_logs(db):
    batch = svc.create_or_get_cooking_batch(
        db,
        caller=_user(10),
        scope=_scope_personal(10),
        payload=_create_payload(total_servings=3),
    )
    svc.record_cooking_batch_usage(
        db,
        caller=_user(10),
        scope=_scope_personal(10),
        batch_id=batch.id,
        payload=CookingBatchUseIn(servings_used=1),
    )
    assert db.query(MealConsumptionLog).count() == 0


def test_list_active_only(db):
    batch = svc.create_or_get_cooking_batch(
        db,
        caller=_user(10),
        scope=_scope_personal(10),
        payload=_create_payload(),
    )
    svc.finish_cooking_batch(
        db, caller=_user(10), scope=_scope_personal(10), batch_id=batch.id
    )
    svc.create_or_get_cooking_batch(
        db,
        caller=_user(10),
        scope=_scope_personal(10),
        payload=_create_payload(recipe_id=261, meal_type="lunch"),
    )
    active = svc.list_cooking_batches(db, _scope_personal(10), active_only=True)
    assert len(active) == 1
    assert active[0].recipe_id == 261


def test_events_written(db):
    batch = svc.create_or_get_cooking_batch(
        db,
        caller=_user(10),
        scope=_scope_personal(10),
        payload=_create_payload(),
    )
    svc.record_cooking_batch_usage(
        db,
        caller=_user(10),
        scope=_scope_personal(10),
        batch_id=batch.id,
        payload=CookingBatchUseIn(servings_used=1),
    )
    types = {e.event_type for e in db.query(CookingBatchEvent).all()}
    assert types == {"created", "used"}


def test_overview_products_not_broken(db, monkeypatch):
    from app.schemas.pantry import PantryItemResponse, PantryListResponse
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)
    monkeypatch.setattr(
        svc,
        "list_pantry",
        lambda _db, _user, scope: PantryListResponse(
            scope_mode=scope.mode,
            user_id=scope.user_id,
            family_id=scope.family_id,
            items=[
                PantryItemResponse(
                    id=1,
                    scope_mode="personal",
                    user_id=10,
                    family_id=None,
                    name="Рис",
                    category="Бакалея",
                    quantity="800",
                    unit="г",
                    source="manual",
                    note=None,
                    expires_at=None,
                    is_expired=False,
                    days_until_expiry=999,
                    added_by_name=None,
                    created_at=now,
                    updated_at=now,
                )
            ],
            active_count=1,
            expired_count=0,
        ),
    )
    overview = svc.list_stock_overview(db, _user(10), _scope_personal(10))
    assert overview.summary.products_count == 1
    assert overview.products[0].title == "Рис"
