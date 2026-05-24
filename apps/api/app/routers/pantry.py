import logging

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_app_scope, get_verified_user
from app.services.app_scope import AppScope
from app.models.user import User
from app.schemas.pantry import (
    PantryItemCreate,
    PantryItemResponse,
    PantryItemUpdate,
    PantryListResponse,
)
from app.services import pantry as pantry_service

router = APIRouter(prefix="/pantry", tags=["pantry"])
logger = logging.getLogger(__name__)


@router.get("/me", response_model=PantryListResponse)
def get_my_pantry(
    scope: AppScope = Depends(get_app_scope),
    user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
) -> PantryListResponse:
    result = pantry_service.list_pantry(db, user, scope)
    logger.info(
        "Pantry loaded user_id=%s active=%s",
        user.id,
        result.active_count,
    )
    return result


@router.post(
    "/items",
    response_model=PantryItemResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_pantry_item(
    payload: PantryItemCreate,
    scope: AppScope = Depends(get_app_scope),
    user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
) -> PantryItemResponse:
    return pantry_service.add_item(db, user, scope, payload)


@router.patch("/items/{item_id}", response_model=PantryItemResponse)
def update_pantry_item(
    item_id: int,
    payload: PantryItemUpdate,
    scope: AppScope = Depends(get_app_scope),
    user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
) -> PantryItemResponse:
    return pantry_service.update_item(db, user, scope, item_id, payload)


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_pantry_item(
    item_id: int,
    scope: AppScope = Depends(get_app_scope),
    db: Session = Depends(get_db),
) -> None:
    pantry_service.delete_item(db, scope, item_id)
