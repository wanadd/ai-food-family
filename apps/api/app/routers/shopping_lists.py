from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_app_scope, get_verified_user
from app.models.user import User
from app.schemas.shopping_list import (
    ShoppingItemCreateRequest,
    ShoppingItemUpdateRequest,
    ShoppingListResponse,
    ToggleItemRequest,
)
from app.services.app_scope import AppScope
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


@router.post(
    "/items",
    response_model=ShoppingListResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_shopping_item(
    payload: ShoppingItemCreateRequest,
    scope: AppScope = Depends(get_app_scope),
    user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
) -> ShoppingListResponse:
    return shopping_list_service.create_item(db, user, scope, payload)


@router.patch("/items/{item_id}", response_model=ShoppingListResponse)
def update_shopping_item(
    item_id: str,
    payload: ShoppingItemUpdateRequest,
    scope: AppScope = Depends(get_app_scope),
    user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
) -> ShoppingListResponse:
    if payload.checked is not None:
        return shopping_list_service.toggle_item(
            db,
            user,
            scope,
            item_id,
            payload.checked,
            remove_from_pantry=payload.remove_from_pantry,
        )
    return shopping_list_service.update_item(db, user, scope, item_id, payload)


@router.delete("/items/{item_id}", response_model=ShoppingListResponse)
def delete_shopping_item(
    item_id: str,
    scope: AppScope = Depends(get_app_scope),
    user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
) -> ShoppingListResponse:
    return shopping_list_service.delete_item(db, user, scope, item_id)


@router.patch("/items/{item_id}/toggle", response_model=ShoppingListResponse)
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
