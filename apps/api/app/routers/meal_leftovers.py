from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_app_scope, get_verified_user
from app.models.user import User
from app.schemas.meal_leftover import (
    MealLeftoverCreate,
    MealLeftoverResponse,
    MealLeftoverUpdate,
)
from app.services.app_scope import AppScope
from app.services import meal_leftovers as meal_leftovers_service

router = APIRouter(prefix="/meal-leftovers", tags=["meal-leftovers"])


@router.get("", response_model=list[MealLeftoverResponse])
def list_meal_leftovers(
    scope: AppScope = Depends(get_app_scope),
    db: Session = Depends(get_db),
) -> list[MealLeftoverResponse]:
    return meal_leftovers_service.list_leftovers(db, scope)


@router.post("", response_model=MealLeftoverResponse)
def create_meal_leftover(
    payload: MealLeftoverCreate,
    scope: AppScope = Depends(get_app_scope),
    user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
) -> MealLeftoverResponse:
    return meal_leftovers_service.create_leftover(db, user, scope, payload)


@router.patch("/{leftover_id}", response_model=MealLeftoverResponse)
def update_meal_leftover(
    leftover_id: int,
    payload: MealLeftoverUpdate,
    scope: AppScope = Depends(get_app_scope),
    db: Session = Depends(get_db),
) -> MealLeftoverResponse:
    return meal_leftovers_service.update_leftover(db, scope, leftover_id, payload)


@router.delete("/{leftover_id}", status_code=204)
def delete_meal_leftover(
    leftover_id: int,
    scope: AppScope = Depends(get_app_scope),
    db: Session = Depends(get_db),
) -> None:
    meal_leftovers_service.delete_leftover(db, scope, leftover_id)
