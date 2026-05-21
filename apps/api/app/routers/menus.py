from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas.menu import (
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
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MenuGenerateResponse:
    return await menu_service.generate_family_menus(db, user)


@router.post("/replace-dish", response_model=MenuVariant)
async def replace_dish(
    payload: ReplaceDishRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MenuVariant:
    return await menu_service.replace_dish(db, user, payload)


@router.post("/select", response_model=SelectedMenuResponse)
def select_menu(
    payload: SelectMenuRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SelectedMenuResponse:
    return menu_service.select_menu(db, user, payload)


@router.get("/selected", response_model=SelectedMenuResponse | None)
def get_selected_menu(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SelectedMenuResponse | None:
    return menu_service.get_selected_menu(db, user)
