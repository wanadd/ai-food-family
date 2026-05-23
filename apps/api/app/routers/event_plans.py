from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_app_scope, get_verified_user
from app.models.user import User
from app.schemas.event_plan import (
    EventPlanCreateRequest,
    EventPlanDetail,
    EventPlanListResponse,
)
from app.services.app_scope import AppScope
from app.services import event_plan as event_plan_service

router = APIRouter(prefix="/event-plans", tags=["event-plans"])


@router.post("", response_model=EventPlanDetail)
def create_event_plan(
    payload: EventPlanCreateRequest,
    user: User = Depends(get_verified_user),
    scope: AppScope = Depends(get_app_scope),
    db: Session = Depends(get_db),
) -> EventPlanDetail:
    return event_plan_service.create_event_plan(db, user, scope, payload)


@router.get("", response_model=EventPlanListResponse)
def list_event_plans(
    user: User = Depends(get_verified_user),
    scope: AppScope = Depends(get_app_scope),
    db: Session = Depends(get_db),
) -> EventPlanListResponse:
    return event_plan_service.list_event_plans(db, user, scope)


@router.get("/{plan_id}", response_model=EventPlanDetail)
def get_event_plan(
    plan_id: int,
    user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
) -> EventPlanDetail:
    plan = event_plan_service.get_event_plan(db, user, plan_id)
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return plan


@router.post("/{plan_id}/create-shopping-list", status_code=status.HTTP_204_NO_CONTENT)
def create_event_shopping_list(
    plan_id: int,
    user: User = Depends(get_verified_user),
    scope: AppScope = Depends(get_app_scope),
    db: Session = Depends(get_db),
) -> None:
    event_plan_service.create_shopping_from_event(db, user, scope, plan_id)
