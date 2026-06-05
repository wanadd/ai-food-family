import logging
from datetime import date

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
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
    MenuPlanItem,
    MenuQuickActionRequest,
    MenuQuickActionResponse,
    MenuTodayResponse,
    ReplaceMenuSlotRequest,
    ReplaceMenuSlotResponse,
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
    logger.info(
        "POST /menus/replace-dish user=%s meal_index=%s day_index=%s",
        user.id,
        payload.meal_index,
        payload.day_index,
    )
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


@router.get("/today", response_model=MenuTodayResponse)
def get_menu_today(
    plan_date: str | None = Query(default=None, alias="date"),
    scope: AppScope = Depends(get_app_scope),
    db: Session = Depends(get_db),
) -> MenuTodayResponse:
    from app.schemas.menu_overview import MenuPlanItem
    from app.services.menu_recipe_plan import get_plan_for_date

    date_value = plan_date or date.today().isoformat()
    try:
        date_iso, items, menu = get_plan_for_date(db, scope, plan_date=date_value)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    return MenuTodayResponse(
        date=date_iso,
        items=[MenuPlanItem(**item) for item in items],
        menu=menu,
    )


@router.post("/items/{slot_id}/replace", response_model=ReplaceMenuSlotResponse)
def replace_menu_item(
    slot_id: str,
    payload: ReplaceMenuSlotRequest,
    scope: AppScope = Depends(get_app_scope),
    user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
) -> ReplaceMenuSlotResponse:
    from app.services import recipes as recipes_service
    from app.services.menu_recipe_plan import replace_recipe_in_slot

    recipe = recipes_service.get_recipe_model(db, payload.recipe_id)
    if recipe is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipe not found",
        )
    try:
        item_dict, menu = replace_recipe_in_slot(
            db,
            user,
            scope,
            recipe,
            slot_id=slot_id,
            servings=payload.servings,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    return ReplaceMenuSlotResponse(item=MenuPlanItem(**item_dict), menu=menu)


@router.delete("/items/{slot_id}", response_model=SelectedMenuResponse)
def delete_menu_item(
    slot_id: str,
    scope: AppScope = Depends(get_app_scope),
    user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
) -> SelectedMenuResponse:
    from app.services.menu_recipe_plan import remove_menu_item

    try:
        remove_menu_item(db, user, scope, slot_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    selected = menu_service.get_selected_menu(db, scope)
    if selected is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Меню не найдено",
        )
    return selected


@router.get("/selected", response_model=SelectedMenuResponse | None)
def get_selected_menu(
    scope: AppScope = Depends(get_app_scope),
    db: Session = Depends(get_db),
) -> SelectedMenuResponse | None:
    import logging

    result = menu_service.get_selected_menu(db, scope)
    logging.getLogger(__name__).info(
        "Menu loaded scope=%s has_menu=%s",
        scope.mode,
        result is not None,
    )
    return result


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
