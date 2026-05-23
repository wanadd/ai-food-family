from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.menu_selection import FamilyMenuSelection
from app.models.user import User
from app.schemas.menu import (
    MenuGenerateRequest,
    MenuGenerateResponse,
    MenuVariant,
    ReplaceDishRequest,
    SelectMenuRequest,
    SelectedMenuResponse,
)
from app.config import settings
from app.services.menu_labels import PLAN_MODE_PROMPT_HINTS
from app.services.app_scope import AppScope
from app.services import shopping_list as shopping_list_service
from app.services import subscription as subscription_service
from app.services.menu_ai import generate_menus, replace_meal
from app.services.menu_context import build_menu_context


async def generate_menus_for_scope(
    db: Session,
    user: User,
    scope: AppScope,
    options: MenuGenerateRequest | None = None,
) -> MenuGenerateResponse:
    context = build_menu_context(db, user, scope)
    if options:
        extras: list[str] = []
        if options.persons_count:
            extras.append(
                f"Количество персон (порций): {options.persons_count}. "
                "Умножай объёмы ингредиентов с учётом этого числа."
            )
        if options.plan_mode:
            hint = PLAN_MODE_PROMPT_HINTS.get(options.plan_mode)
            if hint:
                extras.append(hint)
        if extras:
            context.prompt_text = context.prompt_text + "\n" + "\n".join(extras)
        if options.persons_count:
            context.members_count = options.persons_count

    access = subscription_service.assert_menu_generation_allowed(db, user, scope)
    menus, used_ai = await generate_menus(context)
    subscription_service.commit_menu_generation(
        db,
        user,
        scope,
        access,
        used_ai=used_ai,
        model=settings.openai_model if used_ai else None,
    )
    return MenuGenerateResponse(
        menus=menus,
        scope_mode=context.scope_mode,
        context_label=context.context_label,
        family_name=context.family_name,
        members_count=context.members_count,
        generated_with_ai=used_ai,
    )


async def replace_dish(
    db: Session, user: User, scope: AppScope, payload: ReplaceDishRequest
) -> MenuVariant:
    subscription_service.ensure_user_billing(db, user)
    sub = subscription_service.get_active_subscription(db, user)
    if sub is None or not subscription_service.ai_actions_allowed(sub):
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "code": "trial_expired",
                "message": (
                    "Пробный период закончился. Выберите тариф для AI-действий."
                ),
            },
        )

    context = build_menu_context(db, user, scope)
    try:
        updated = await replace_meal(
            context, payload.menu, payload.meal_index, payload.hint
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    selection = _get_latest_selection(db, scope)
    if selection is not None and selection.variant == updated.variant:
        selection.menu_data = updated.model_dump(mode="json")
        db.commit()
        shopping_list_service.sync_from_menu(db, scope, updated, selection.id)

    subscription_service.log_ai_usage(
        db,
        user_id=user.id,
        family_id=scope.family_id,
        action_type="menu_replace_dish",
        ams_spent=0,
        model=settings.openai_model,
        metadata={"variant": updated.variant},
    )

    return updated


def select_menu(
    db: Session, user: User, scope: AppScope, payload: SelectMenuRequest
) -> SelectedMenuResponse:
    existing = _get_latest_selection(db, scope)
    menu_dict = payload.menu.model_dump(mode="json")

    if existing is not None:
        existing.variant = payload.menu.variant
        existing.menu_data = menu_dict
        existing.user_id = user.id
        existing.family_id = scope.family_id if scope.is_family else None
        existing.selected_at = datetime.now(timezone.utc)
        selection = existing
    else:
        selection = FamilyMenuSelection(
            user_id=user.id,
            family_id=scope.family_id if scope.is_family else None,
            variant=payload.menu.variant,
            menu_data=menu_dict,
        )
        db.add(selection)

    db.commit()
    db.refresh(selection)
    shopping_list_service.sync_from_menu(db, scope, payload.menu, selection.id)
    return _selection_response(selection, scope)


def get_selected_menu(
    db: Session, scope: AppScope
) -> SelectedMenuResponse | None:
    selection = _get_latest_selection(db, scope)
    if selection is None:
        return None
    return _selection_response(selection, scope)


def _get_latest_selection(
    db: Session, scope: AppScope
) -> FamilyMenuSelection | None:
    query = db.query(FamilyMenuSelection)
    if scope.is_family:
        query = query.filter(FamilyMenuSelection.family_id == scope.family_id)
    else:
        query = query.filter(
            FamilyMenuSelection.user_id == scope.user_id,
            FamilyMenuSelection.family_id.is_(None),
        )
    return query.order_by(FamilyMenuSelection.selected_at.desc()).first()


def _selection_response(
    selection: FamilyMenuSelection, scope: AppScope
) -> SelectedMenuResponse:
    return SelectedMenuResponse(
        id=selection.id,
        scope_mode=scope.mode,
        user_id=selection.user_id,
        family_id=selection.family_id,
        variant=selection.variant,  # type: ignore[arg-type]
        menu=MenuVariant.model_validate(selection.menu_data),
        selected_at=selection.selected_at,
    )
