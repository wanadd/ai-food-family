from datetime import date

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.meal_leftover import MealLeftover
from app.models.user import User
from app.schemas.meal_leftover import (
    MealLeftoverCreate,
    MealLeftoverResponse,
    MealLeftoverUpdate,
)
from app.services.app_scope import AppScope
def _leftover_query(db: Session, scope: AppScope):
    q = db.query(MealLeftover)
    if scope.is_family:
        return q.filter(MealLeftover.family_id == scope.family_id)
    return q.filter(
        MealLeftover.user_id == scope.user_id,
        MealLeftover.family_id.is_(None),
    )


USABLE_LEFTOVER_STATUSES = ("active", "planned_to_eat")


def list_active_leftovers(
    db: Session,
    scope: AppScope,
    *,
    include_frozen: bool = False,
) -> list[MealLeftover]:
    today = date.today()
    statuses = list(USABLE_LEFTOVER_STATUSES)
    if include_frozen:
        statuses.append("frozen")
    return (
        _leftover_query(db, scope)
        .filter(
            (MealLeftover.valid_until.is_(None))
            | (MealLeftover.valid_until >= today)
        )
        .filter(MealLeftover.portions_remaining > 0)
        .filter(MealLeftover.leftover_status.in_(statuses))
        .order_by(MealLeftover.valid_until.asc().nulls_last())
        .all()
    )


def list_leftovers(db: Session, scope: AppScope) -> list[MealLeftoverResponse]:
    rows = (
        _leftover_query(db, scope)
        .order_by(MealLeftover.created_at.desc())
        .all()
    )
    return [_to_response(row, scope) for row in rows]


def create_leftover(
    db: Session,
    user: User,
    scope: AppScope,
    payload: MealLeftoverCreate,
) -> MealLeftoverResponse:
    row = MealLeftover(
        user_id=scope.user_id if not scope.is_family else None,
        family_id=scope.family_id if scope.is_family else None,
        dish_name=payload.dish_name.strip(),
        portions_remaining=payload.portions_remaining,
        valid_until=payload.valid_until,
        note=payload.note,
        added_by_user_id=user.id,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _to_response(row, scope)


def update_leftover(
    db: Session,
    scope: AppScope,
    leftover_id: int,
    payload: MealLeftoverUpdate,
) -> MealLeftoverResponse:
    row = _get_or_404(db, scope, leftover_id)
    data = payload.model_dump(exclude_unset=True)
    if "dish_name" in data and data["dish_name"] is not None:
        row.dish_name = data["dish_name"].strip()
    if "portions_remaining" in data:
        row.portions_remaining = data["portions_remaining"]
    if "valid_until" in data:
        row.valid_until = data["valid_until"]
    if "note" in data:
        row.note = data["note"] or None
    if "leftover_status" in data and data["leftover_status"] is not None:
        row.leftover_status = data["leftover_status"]
    db.commit()
    db.refresh(row)
    return _to_response(row, scope)


def delete_leftover(db: Session, scope: AppScope, leftover_id: int) -> None:
    row = _get_or_404(db, scope, leftover_id)
    db.delete(row)
    db.commit()


def _get_or_404(db: Session, scope: AppScope, leftover_id: int) -> MealLeftover:
    row = (
        _leftover_query(db, scope).filter(MealLeftover.id == leftover_id).one_or_none()
    )
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return row


def _to_response(row: MealLeftover, scope: AppScope) -> MealLeftoverResponse:
    return MealLeftoverResponse(
        id=row.id,
        scope_mode=scope.mode,
        dish_name=row.dish_name,
        portions_remaining=row.portions_remaining,
        valid_until=row.valid_until,
        note=row.note,
        leftover_status=getattr(row, "leftover_status", None) or "active",
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def format_meal_leftovers_for_prompt(rows: list[MealLeftover]) -> list[str]:
    if not rows:
        return []
    lines = ["Готовые остатки блюд (учти при меню, не дублируй готовку):"]
    for row in rows:
        until = ""
        if row.valid_until:
            until = f", съесть до {row.valid_until.isoformat()}"
        lines.append(
            f"- {row.dish_name}: {row.portions_remaining} порц.{until}"
        )
    return lines
