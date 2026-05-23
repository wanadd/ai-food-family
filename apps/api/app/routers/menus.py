import logging

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from app.database import SessionLocal, get_db
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
from app.schemas.menu_overview import (
    MenuOverviewResponse,
    MenuQuickActionRequest,
    MenuQuickActionResponse,
)
from app.services import menu as menu_service
from app.services import menu_overview as menu_overview_service
from app.services import care as care_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/menus", tags=["menus"])


async def _send_menu_care_notification(user_id: int) -> None:
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).one_or_none()
        if user is not None:
            await care_service.maybe_notify_menu_ready(db, user)
    except Exception:
        logger.exception("Menu care notification failed for user %s", user_id)
    finally:
        db.close()


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
    background_tasks: BackgroundTasks,
    scope: AppScope = Depends(get_app_scope),
    user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
) -> SelectedMenuResponse:
    result = menu_service.select_menu(db, user, scope, payload)
    background_tasks.add_task(_send_menu_care_notification, user.id)
    return result


@router.get("/selected", response_model=SelectedMenuResponse | None)
def get_selected_menu(
    scope: AppScope = Depends(get_app_scope),
    db: Session = Depends(get_db),
) -> SelectedMenuResponse | None:
    return menu_service.get_selected_menu(db, scope)


@router.get("/overview", response_model=MenuOverviewResponse)
def get_menu_overview(
    scope: AppScope = Depends(get_app_scope),
    user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
) -> MenuOverviewResponse:
    return menu_overview_service.get_menu_overview(db, user, scope)


@router.post("/quick-action", response_model=MenuQuickActionResponse)
async def menu_quick_action(
    payload: MenuQuickActionRequest,
    scope: AppScope = Depends(get_app_scope),
    user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
) -> MenuQuickActionResponse:
    redirect, selected, message = await menu_service.run_quick_action(
        db, user, scope, payload.action
    )
    return MenuQuickActionResponse(
        action=payload.action,
        redirect_path=redirect,
        selected_menu=selected,
        message=message,
    )
