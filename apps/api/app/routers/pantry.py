from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas.pantry import (
    PantryItemCreate,
    PantryItemResponse,
    PantryItemUpdate,
    PantryListResponse,
)
from app.services import pantry as pantry_service

router = APIRouter(prefix="/pantry", tags=["pantry"])


@router.get("/me", response_model=PantryListResponse)
def get_my_pantry(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PantryListResponse:
    return pantry_service.list_pantry(db, user)


@router.post(
    "/items",
    response_model=PantryItemResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_pantry_item(
    payload: PantryItemCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PantryItemResponse:
    return pantry_service.add_item(db, user, payload)


@router.patch("/items/{item_id}", response_model=PantryItemResponse)
def update_pantry_item(
    item_id: int,
    payload: PantryItemUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PantryItemResponse:
    return pantry_service.update_item(db, user, item_id, payload)


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_pantry_item(
    item_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    pantry_service.delete_item(db, user, item_id)
