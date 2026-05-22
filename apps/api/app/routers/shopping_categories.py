from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_app_scope, get_verified_user
from app.models.user import User
from app.schemas.shopping_category import (
    ShoppingCategoryCreateRequest,
    ShoppingCategoryResponse,
)
from app.services.app_scope import AppScope
from app.services import shopping_category_service as category_service

router = APIRouter(prefix="/shopping-categories", tags=["shopping-categories"])


@router.get("", response_model=list[ShoppingCategoryResponse])
def list_shopping_categories(
    scope: AppScope = Depends(get_app_scope),
    db: Session = Depends(get_db),
) -> list[ShoppingCategoryResponse]:
    rows = category_service.list_categories(db, scope)
    return [
        ShoppingCategoryResponse(
            id=r.id,
            slug=r.slug,
            name=r.name,
            icon=r.icon,
            is_food=r.is_food,
            is_system=r.is_system,
            created_at=r.created_at,
        )
        for r in rows
    ]


@router.post(
    "",
    response_model=ShoppingCategoryResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_shopping_category(
    payload: ShoppingCategoryCreateRequest,
    scope: AppScope = Depends(get_app_scope),
    user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
) -> ShoppingCategoryResponse:
    row = category_service.create_category(db, scope, payload)
    return ShoppingCategoryResponse(
        id=row.id,
        slug=row.slug,
        name=row.name,
        icon=row.icon,
        is_food=row.is_food,
        is_system=row.is_system,
        created_at=row.created_at,
    )
