from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_app_scope, get_verified_user
from app.services.app_scope import AppScope
from app.models.user import User
from app.schemas.menu import (
    MenuGenerateRequest,
    MenuGenerateResponse,
    MenuVariant,
    ReplaceDishRequest,
    SelectMenuRequest,
    SelectedMenuResponse,
)
from app.services import menu as menu_service

router = APIRouter(prefix="/menus", tags=["menus"])


@router.post("/generate", response_model=MenuGenerateResponse)
async def generate_menus(
    payload: MenuGenerateRequest | None = None,
    scope: AppScope = Depends(get_app_scope),
    user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
) -> MenuGenerateResponse:
    return await menu_service.generate_menus_for_scope(
        db, user, scope, payload or MenuGenerateRequest()
    )


@router.post("/replace-dish", response_model=MenuVariant)
async def replace_dish(
    payload: ReplaceDishRequest,
    scope: AppScope = Depends(get_app_scope),
    user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
) -> MenuVariant:
    return await menu_service.replace_dish(db, user, scope, payload)


@router.post("/select", response_model=SelectedMenuResponse)
def select_menu(
    payload: SelectMenuRequest,
    scope: AppScope = Depends(get_app_scope),
    user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
) -> SelectedMenuResponse:
    return menu_service.select_menu(db, user, scope, payload)


@router.get("/selected", response_model=SelectedMenuResponse | None)
def get_selected_menu(
    scope: AppScope = Depends(get_app_scope),
    db: Session = Depends(get_db),
) -> SelectedMenuResponse | None:
    return menu_service.get_selected_menu(db, scope)
