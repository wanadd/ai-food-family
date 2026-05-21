from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas.shopping_list import ShoppingListResponse, ToggleItemRequest
from app.services import shopping_list as shopping_list_service

router = APIRouter(prefix="/shopping-lists", tags=["shopping-lists"])


@router.get("/me", response_model=ShoppingListResponse)
def get_my_shopping_list(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ShoppingListResponse:
    return shopping_list_service.get_shopping_list(db, user)


@router.post("/sync", response_model=ShoppingListResponse)
def sync_shopping_list(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ShoppingListResponse:
    return shopping_list_service.sync_shopping_list_for_user(db, user)


@router.patch("/items/{item_id}", response_model=ShoppingListResponse)
def toggle_shopping_item(
    item_id: str,
    payload: ToggleItemRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ShoppingListResponse:
    return shopping_list_service.toggle_item(db, user, item_id, payload.checked)
