from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_app_scope, get_verified_user
from app.models.user import User
from app.schemas.leftovers import (
    CookingBatchAdjustIn,
    CookingBatchCreateIn,
    CookingBatchOut,
    CookingBatchUseIn,
    StocksOverviewOut,
)
from app.services.app_scope import AppScope
from app.services import leftovers as leftovers_service

router = APIRouter(prefix="/leftovers", tags=["leftovers"])


@router.get("", response_model=StocksOverviewOut)
def get_stocks_overview(
    family_id: int | None = Query(default=None),
    include_prepared: bool = Query(default=True),
    user: User = Depends(get_verified_user),
    scope: AppScope = Depends(get_app_scope),
    db: Session = Depends(get_db),
) -> StocksOverviewOut:
    if family_id is not None:
        leftovers_service._validate_family_access(db, user, family_id)
    return leftovers_service.list_stock_overview(
        db, user, scope, include_prepared=include_prepared
    )


@router.get("/prepared", response_model=list[CookingBatchOut])
def list_prepared_leftovers(
    recipe_id: int | None = Query(default=None),
    menu_selection_id: int | None = Query(default=None),
    day_index: int | None = Query(default=None),
    meal_type: str | None = Query(default=None),
    planned_date: date | None = Query(default=None),
    user: User = Depends(get_verified_user),
    scope: AppScope = Depends(get_app_scope),
    db: Session = Depends(get_db),
) -> list[CookingBatchOut]:
    has_lookup = any(
        v is not None
        for v in (recipe_id, menu_selection_id, day_index, meal_type, planned_date)
    )
    if has_lookup:
        batch = leftovers_service.lookup_active_cooking_batch(
            db,
            scope,
            recipe_id=recipe_id,
            menu_selection_id=menu_selection_id,
            day_index=day_index,
            meal_type=meal_type,
            planned_date=planned_date,
        )
        if batch is None:
            return []
        return [leftovers_service.batch_to_out(batch)]
    rows = leftovers_service.list_cooking_batches(db, scope, active_only=True)
    return [leftovers_service.batch_to_out(row) for row in rows]


@router.post("/batches", response_model=CookingBatchOut)
def create_cooking_batch(
    payload: CookingBatchCreateIn,
    user: User = Depends(get_verified_user),
    scope: AppScope = Depends(get_app_scope),
    db: Session = Depends(get_db),
) -> CookingBatchOut:
    batch = leftovers_service.create_or_get_cooking_batch(
        db, caller=user, scope=scope, payload=payload
    )
    return leftovers_service.batch_to_out(batch)


@router.post("/batches/{batch_id}/use", response_model=CookingBatchOut)
def use_cooking_batch(
    batch_id: int,
    payload: CookingBatchUseIn,
    user: User = Depends(get_verified_user),
    scope: AppScope = Depends(get_app_scope),
    db: Session = Depends(get_db),
) -> CookingBatchOut:
    batch = leftovers_service.record_cooking_batch_usage(
        db, caller=user, scope=scope, batch_id=batch_id, payload=payload
    )
    return leftovers_service.batch_to_out(batch)


@router.post("/batches/{batch_id}/adjust", response_model=CookingBatchOut)
def adjust_cooking_batch(
    batch_id: int,
    payload: CookingBatchAdjustIn,
    user: User = Depends(get_verified_user),
    scope: AppScope = Depends(get_app_scope),
    db: Session = Depends(get_db),
) -> CookingBatchOut:
    batch = leftovers_service.adjust_cooking_batch_remaining(
        db, caller=user, scope=scope, batch_id=batch_id, payload=payload
    )
    return leftovers_service.batch_to_out(batch)


@router.post("/batches/{batch_id}/finish", response_model=CookingBatchOut)
def finish_cooking_batch(
    batch_id: int,
    user: User = Depends(get_verified_user),
    scope: AppScope = Depends(get_app_scope),
    db: Session = Depends(get_db),
) -> CookingBatchOut:
    batch = leftovers_service.finish_cooking_batch(
        db, caller=user, scope=scope, batch_id=batch_id
    )
    return leftovers_service.batch_to_out(batch)


@router.post("/batches/{batch_id}/discard", response_model=CookingBatchOut)
def discard_cooking_batch(
    batch_id: int,
    user: User = Depends(get_verified_user),
    scope: AppScope = Depends(get_app_scope),
    db: Session = Depends(get_db),
) -> CookingBatchOut:
    batch = leftovers_service.discard_cooking_batch(
        db, caller=user, scope=scope, batch_id=batch_id
    )
    return leftovers_service.batch_to_out(batch)
