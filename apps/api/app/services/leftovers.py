"""Prepared dish leftovers (cooking_batches) — Phase 4A.

Separate from family_pantry_items (raw products) and meal_consumption_logs (personal KBJU).
"""

from __future__ import annotations

from datetime import date, datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.cooking_batch import CookingBatch, CookingBatchEvent
from app.models.family import FamilyMember, FamilyRole
from app.models.meal_consumption_log import MealConsumptionLog
from app.models.recipe import Recipe
from app.models.user import User
from app.schemas.leftovers import (
    CookingBatchAdjustIn,
    CookingBatchCreateIn,
    CookingBatchOut,
    CookingBatchUseIn,
    PreparedDishOut,
    StockProductOut,
    StocksOverviewOut,
    StocksSummaryOut,
)
from app.services import family as family_service
from app.services.app_scope import AppScope
from app.services.pantry import get_active_items_for_scope, list_pantry

ACTIVE_BATCH_STATUSES = frozenset({"active"})
TERMINAL_BATCH_STATUSES = frozenset({"finished", "discarded"})
PERMISSION_DENIED = "Нет прав управлять остатками этого блюда"
FAMILY_ACCESS_DENIED = "Нет доступа к остаткам этой семьи"


def _membership(db: Session, user: User) -> FamilyMember | None:
    return family_service.get_user_membership(db, user)


def _is_family_admin(membership: FamilyMember | None) -> bool:
    return membership is not None and membership.role == FamilyRole.ADMIN.value


def _batch_query(db: Session, scope: AppScope):
    q = db.query(CookingBatch)
    if scope.is_family:
        return q.filter(CookingBatch.family_id == scope.family_id)
    return q.filter(
        CookingBatch.owner_user_id == scope.user_id,
        CookingBatch.family_id.is_(None),
    )


def can_manage_prepared_leftovers(
    db: Session,
    *,
    caller: User,
    batch: CookingBatch,
) -> bool:
    if batch.family_id is None:
        return batch.owner_user_id == caller.id
    membership = _membership(db, caller)
    return (
        membership is not None
        and membership.family_id == batch.family_id
        and _is_family_admin(membership)
    )


def _validate_family_access(db: Session, caller: User, family_id: int | None) -> None:
    if family_id is None:
        return
    membership = _membership(db, caller)
    if membership is None or membership.family_id != family_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=FAMILY_ACCESS_DENIED,
        )


def _get_batch_or_404(db: Session, scope: AppScope, batch_id: int) -> CookingBatch:
    row = _batch_query(db, scope).filter(CookingBatch.id == batch_id).one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return row


def _record_event(
    db: Session,
    *,
    batch: CookingBatch,
    event_type: str,
    actor_user_id: int,
    servings_delta: float | None = None,
    remaining_after: float | None = None,
    note: str | None = None,
) -> CookingBatchEvent:
    event = CookingBatchEvent(
        batch_id=batch.id,
        event_type=event_type,
        actor_user_id=actor_user_id,
        servings_delta=servings_delta,
        remaining_after=remaining_after,
        note=note,
    )
    db.add(event)
    return event


def _default_total_servings(db: Session, recipe_id: int | None, requested: float) -> float:
    if requested > 0:
        return requested
    if recipe_id:
        recipe = db.get(Recipe, recipe_id)
        if recipe and recipe.servings and recipe.servings > 0:
            return float(recipe.servings)
    return 1.0


def _find_active_batch(
    db: Session,
    scope: AppScope,
    *,
    recipe_id: int | None,
    menu_selection_id: int | None,
    day_index: int | None,
    meal_type: str | None,
    planned_date: date | None = None,
) -> CookingBatch | None:
    q = _batch_query(db, scope).filter(CookingBatch.batch_status == "active")
    if recipe_id is not None:
        q = q.filter(CookingBatch.recipe_id == recipe_id)
    if menu_selection_id is not None:
        q = q.filter(CookingBatch.menu_selection_id == menu_selection_id)
    if day_index is not None:
        q = q.filter(CookingBatch.day_index == day_index)
    if meal_type is not None:
        q = q.filter(CookingBatch.meal_type == meal_type)
    if planned_date is not None:
        q = q.filter(CookingBatch.planned_date == planned_date)
    return q.order_by(CookingBatch.id.desc()).first()


def lookup_active_cooking_batch(
    db: Session,
    scope: AppScope,
    *,
    recipe_id: int | None = None,
    menu_selection_id: int | None = None,
    day_index: int | None = None,
    meal_type: str | None = None,
    planned_date: date | None = None,
) -> CookingBatch | None:
    """Find active batch for a specific dish in the current scope."""
    return _find_active_batch(
        db,
        scope,
        recipe_id=recipe_id,
        menu_selection_id=menu_selection_id,
        day_index=day_index,
        meal_type=meal_type,
        planned_date=planned_date,
    )


def create_or_get_cooking_batch(
    db: Session,
    *,
    caller: User,
    scope: AppScope,
    payload: CookingBatchCreateIn,
) -> CookingBatch:
    _validate_family_access(db, caller, payload.family_id)

    existing = _find_active_batch(
        db,
        scope,
        recipe_id=payload.recipe_id,
        menu_selection_id=payload.menu_selection_id,
        day_index=payload.day_index,
        meal_type=payload.meal_type,
    )
    if existing is not None:
        return existing

    total = _default_total_servings(db, payload.recipe_id, payload.total_servings)
    now = datetime.now(timezone.utc)

    if scope.is_family:
        family_id = scope.family_id
        owner_user_id = None
    else:
        family_id = None
        owner_user_id = caller.id

    batch = CookingBatch(
        family_id=family_id,
        owner_user_id=owner_user_id,
        created_by_user_id=caller.id,
        recipe_id=payload.recipe_id,
        recipe_title=payload.recipe_title.strip(),
        menu_selection_id=payload.menu_selection_id,
        day_index=payload.day_index,
        planned_date=payload.planned_date,
        meal_type=payload.meal_type,
        batch_status="active",
        total_servings=total,
        remaining_servings=total,
        serving_unit=payload.serving_unit or "порция",
        cooked_at=now,
    )
    db.add(batch)
    db.flush()
    _record_event(
        db,
        batch=batch,
        event_type="created",
        actor_user_id=caller.id,
        servings_delta=total,
        remaining_after=total,
    )
    db.commit()
    db.refresh(batch)
    return batch


def record_cooking_batch_usage(
    db: Session,
    *,
    caller: User,
    scope: AppScope,
    batch_id: int,
    payload: CookingBatchUseIn,
) -> CookingBatch:
    batch = _get_batch_or_404(db, scope, batch_id)
    if not can_manage_prepared_leftovers(db, caller=caller, batch=batch):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=PERMISSION_DENIED)
    if batch.batch_status not in ACTIVE_BATCH_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Batch is not active",
        )

    remaining = max(0.0, float(batch.remaining_servings) - payload.servings_used)
    batch.remaining_servings = remaining
    if remaining <= 0:
        batch.batch_status = "finished"
    _record_event(
        db,
        batch=batch,
        event_type="used",
        actor_user_id=caller.id,
        servings_delta=-payload.servings_used,
        remaining_after=remaining,
        note=payload.note,
    )
    db.commit()
    db.refresh(batch)
    return batch


def adjust_cooking_batch_remaining(
    db: Session,
    *,
    caller: User,
    scope: AppScope,
    batch_id: int,
    payload: CookingBatchAdjustIn,
) -> CookingBatch:
    batch = _get_batch_or_404(db, scope, batch_id)
    if not can_manage_prepared_leftovers(db, caller=caller, batch=batch):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=PERMISSION_DENIED)
    if payload.remaining_servings > batch.total_servings:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Остаток не может превышать приготовленное количество",
        )

    batch.remaining_servings = payload.remaining_servings
    if payload.remaining_servings <= 0:
        batch.batch_status = "finished"
    elif batch.batch_status != "discarded":
        batch.batch_status = "active"

    _record_event(
        db,
        batch=batch,
        event_type="adjusted",
        actor_user_id=caller.id,
        remaining_after=payload.remaining_servings,
        note=payload.note,
    )
    db.commit()
    db.refresh(batch)
    return batch


def finish_cooking_batch(
    db: Session,
    *,
    caller: User,
    scope: AppScope,
    batch_id: int,
) -> CookingBatch:
    batch = _get_batch_or_404(db, scope, batch_id)
    if not can_manage_prepared_leftovers(db, caller=caller, batch=batch):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=PERMISSION_DENIED)

    batch.remaining_servings = 0.0
    batch.batch_status = "finished"
    _record_event(
        db,
        batch=batch,
        event_type="finished",
        actor_user_id=caller.id,
        remaining_after=0.0,
    )
    db.commit()
    db.refresh(batch)
    return batch


def discard_cooking_batch(
    db: Session,
    *,
    caller: User,
    scope: AppScope,
    batch_id: int,
) -> CookingBatch:
    batch = _get_batch_or_404(db, scope, batch_id)
    if not can_manage_prepared_leftovers(db, caller=caller, batch=batch):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=PERMISSION_DENIED)

    batch.remaining_servings = 0.0
    batch.batch_status = "discarded"
    _record_event(
        db,
        batch=batch,
        event_type="discarded",
        actor_user_id=caller.id,
        remaining_after=0.0,
    )
    db.commit()
    db.refresh(batch)
    return batch


def list_cooking_batches(
    db: Session,
    scope: AppScope,
    *,
    active_only: bool = True,
) -> list[CookingBatch]:
    q = _batch_query(db, scope)
    if active_only:
        q = q.filter(
            CookingBatch.batch_status == "active",
            CookingBatch.remaining_servings > 0,
        )
    return q.order_by(CookingBatch.updated_at.desc()).all()


def list_stock_overview(
    db: Session,
    user: User,
    scope: AppScope,
    *,
    include_prepared: bool = True,
) -> StocksOverviewOut:
    pantry = list_pantry(db, user, scope)
    products = [
        StockProductOut(
            id=item.id,
            title=item.name,
            quantity=item.quantity,
            unit=item.unit or "",
            category=item.category,
        )
        for item in pantry.items
        if not item.is_expired
    ]

    prepared: list[PreparedDishOut] = []
    if include_prepared:
        for batch in list_cooking_batches(db, scope, active_only=True):
            prepared.append(
                PreparedDishOut(
                    id=batch.id,
                    recipe_id=batch.recipe_id,
                    recipe_title=batch.recipe_title,
                    remaining_servings=batch.remaining_servings,
                    total_servings=batch.total_servings,
                    serving_unit=batch.serving_unit,
                    meal_type=batch.meal_type,
                    planned_date=batch.planned_date,
                    day_index=batch.day_index,
                    menu_selection_id=batch.menu_selection_id,
                    batch_status=batch.batch_status,
                    can_manage=can_manage_prepared_leftovers(
                        db, caller=user, batch=batch
                    ),
                )
            )

    products_count = len(products)
    prepared_count = len(prepared)
    return StocksOverviewOut(
        products=products,
        prepared_dishes=prepared,
        summary=StocksSummaryOut(
            products_count=products_count,
            prepared_dishes_count=prepared_count,
            total_positions_count=products_count + prepared_count,
        ),
    )


def batch_to_out(batch: CookingBatch) -> CookingBatchOut:
    return CookingBatchOut.model_validate(batch)


def count_active_prepared_dishes(db: Session, scope: AppScope) -> int:
    return len(list_cooking_batches(db, scope, active_only=True))


def assert_no_meal_consumption_side_effect(db: Session, user_id: int) -> int:
    """Diagnostic helper for tests — returns consumption log count."""
    return db.query(MealConsumptionLog).filter(MealConsumptionLog.user_id == user_id).count()
