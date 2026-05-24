import hashlib

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.deferred_advice import DeferredNutritionAdvice
from app.models.user import User
from app.schemas.deferred_advice import (
    DeferredAdviceCreate,
    DeferredAdviceResponse,
    DeferredAdviceUpdate,
)
from app.services.app_scope import AppScope


def _advice_key(title: str) -> str:
    return hashlib.sha256(title.strip().encode()).hexdigest()[:32]


def _query(db: Session, user: User, scope: AppScope):
    q = db.query(DeferredNutritionAdvice).filter(
        DeferredNutritionAdvice.user_id == user.id,
        DeferredNutritionAdvice.status == "deferred",
    )
    if scope.is_family and scope.family_id:
        return q.filter(DeferredNutritionAdvice.family_id == scope.family_id)
    return q.filter(DeferredNutritionAdvice.family_id.is_(None))


def list_deferred(
    db: Session, user: User, scope: AppScope
) -> list[DeferredAdviceResponse]:
    rows = _query(db, user, scope).order_by(DeferredNutritionAdvice.created_at.desc()).all()
    return [_to_response(r) for r in rows]


def defer_advice(
    db: Session, user: User, scope: AppScope, payload: DeferredAdviceCreate
) -> DeferredAdviceResponse:
    key = _advice_key(payload.title)
    existing = (
        _query(db, user, scope)
        .filter(DeferredNutritionAdvice.advice_key == key)
        .one_or_none()
    )
    if existing:
        existing.body = payload.body
        existing.title = payload.title.strip()
        db.commit()
        db.refresh(existing)
        return _to_response(existing)

    row = DeferredNutritionAdvice(
        user_id=user.id,
        family_id=scope.family_id if scope.is_family else None,
        advice_key=key,
        title=payload.title.strip(),
        body=payload.body.strip(),
        status="deferred",
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _to_response(row)


def update_deferred(
    db: Session,
    user: User,
    scope: AppScope,
    advice_id: int,
    payload: DeferredAdviceUpdate,
) -> DeferredAdviceResponse:
    row = _get_or_404(db, user, scope, advice_id)
    row.status = payload.status
    db.commit()
    db.refresh(row)
    return _to_response(row)


def delete_deferred(db: Session, user: User, scope: AppScope, advice_id: int) -> None:
    row = _get_or_404(db, user, scope, advice_id)
    db.delete(row)
    db.commit()


def is_advice_deferred(db: Session, user: User, scope: AppScope, title: str) -> bool:
    key = _advice_key(title)
    return (
        _query(db, user, scope)
        .filter(DeferredNutritionAdvice.advice_key == key)
        .count()
        > 0
    )


def _get_or_404(
    db: Session, user: User, scope: AppScope, advice_id: int
) -> DeferredNutritionAdvice:
    row = (
        db.query(DeferredNutritionAdvice)
        .filter(
            DeferredNutritionAdvice.id == advice_id,
            DeferredNutritionAdvice.user_id == user.id,
        )
        .one_or_none()
    )
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    if scope.is_family and row.family_id != scope.family_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    if not scope.is_family and row.family_id is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return row


def _to_response(row: DeferredNutritionAdvice) -> DeferredAdviceResponse:
    return DeferredAdviceResponse(
        id=row.id,
        advice_key=row.advice_key,
        title=row.title,
        body=row.body,
        status=row.status,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )
