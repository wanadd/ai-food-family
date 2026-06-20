"""External food logs — manual foundation for future AI parse (Phase 4C)."""

from __future__ import annotations

from datetime import date, datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.external_food_log import ExternalFoodLog
from app.models.user import User
from app.schemas.external_food_log import ExternalFoodLogCreateIn, ExternalFoodLogOut


def create_external_food_log(
    db: Session,
    *,
    caller: User,
    payload: ExternalFoodLogCreateIn,
) -> ExternalFoodLog:
    row = ExternalFoodLog(
        user_id=caller.id,
        family_id=payload.family_id,
        meal_type=payload.meal_type,
        planned_date=payload.planned_date,
        source_type=payload.source_type or "manual",
        input_text=payload.input_text,
        parsed_title=payload.parsed_title or payload.input_text,
        calories_estimated=payload.calories_estimated,
        protein_estimated=payload.protein_estimated,
        fat_estimated=payload.fat_estimated,
        carbs_estimated=payload.carbs_estimated,
        confidence=payload.confidence,
        status=payload.status or "draft",
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def confirm_external_food_log(
    db: Session,
    *,
    caller: User,
    log_id: int,
) -> ExternalFoodLog:
    row = db.get(ExternalFoodLog, log_id)
    if row is None or row.user_id != caller.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    row.status = "confirmed"
    row.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(row)
    return row


def list_external_food_logs(
    db: Session,
    *,
    caller: User,
    planned_date: date,
    status_filter: str | None = None,
) -> list[ExternalFoodLog]:
    q = db.query(ExternalFoodLog).filter(
        ExternalFoodLog.user_id == caller.id,
        ExternalFoodLog.planned_date == planned_date,
    )
    if status_filter:
        q = q.filter(ExternalFoodLog.status == status_filter)
    return q.order_by(ExternalFoodLog.created_at.desc()).all()


def external_food_to_out(row: ExternalFoodLog) -> ExternalFoodLogOut:
    return ExternalFoodLogOut.model_validate(row)
