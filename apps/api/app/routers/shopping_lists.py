from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_app_scope, get_verified_user
from app.services.app_scope import AppScope
from app.models.user import User
from app.schemas.shopping_list import ShoppingListResponse, ToggleItemRequest
from app.services import shopping_list as shopping_list_service

router = APIRouter(prefix="/shopping-lists", tags=["shopping-lists"])


@router.get("/me", response_model=ShoppingListResponse)
def get_my_shopping_list(
    scope: AppScope = Depends(get_app_scope),
    user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
) -> ShoppingListResponse:
    return shopping_list_service.get_shopping_list(db, user, scope)


@router.post("/sync", response_model=ShoppingListResponse)
def sync_shopping_list(
    scope: AppScope = Depends(get_app_scope),
    db: Session = Depends(get_db),
) -> ShoppingListResponse:
    return shopping_list_service.sync_shopping_list_for_scope(db, scope)


@router.patch("/items/{item_id}", response_model=ShoppingListResponse)
def toggle_shopping_item(
    item_id: str,
    payload: ToggleItemRequest,
    scope: AppScope = Depends(get_app_scope),
    user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
) -> ShoppingListResponse:
    return shopping_list_service.toggle_item(
        db,
        user,
        scope,
        item_id,
        payload.checked,
        remove_from_pantry=payload.remove_from_pantry,
    )
