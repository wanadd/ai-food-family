from datetime import datetime, timezone

import logging

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
from app.services.ai_client import current_model_name
from app.services.menu_labels import PLAN_MODE_PROMPT_HINTS
from app.services.app_scope import AppScope
from app.services import shopping_list as shopping_list_service
from app.services import subscription as subscription_service
from app.services.menu_ai import generate_menus, replace_meal
from app.services.menu_context import build_menu_context
from app.services.menu_context_fingerprint import (
    compute_context_fingerprint,
    resolve_persons_count,
)
from app.services.meal_leftovers import list_active_leftovers
from app.services.pantry import get_active_items_for_scope
from app.services.menu_restriction_safety import (
    append_safety_notes_to_menus,
    load_restriction_safe_recipe_pool,
    resolve_menu_profile,
    sanitize_menu_variants,
)

logger = logging.getLogger(__name__)


async def generate_menus_for_scope(
    db: Session,
    user: User,
    scope: AppScope,
    options: MenuGenerateRequest | None = None,
) -> MenuGenerateResponse:
    context = build_menu_context(db, user, scope)
    persons = resolve_persons_count(db, user, scope)
    plan_mode = "healthy"
    if options:
        extras: list[str] = []
        if options.persons_count:
            persons = options.persons_count
        if options.plan_mode:
            plan_mode = options.plan_mode
        if options.plan_days:
            extras.append(
                f"Составь меню на {options.plan_days} дней. "
                "Для каждого дня укажи завтрак, обед, ужин и перекус при необходимости."
            )
        if options.nutrition_goal:
            extras.append(
                f"Цель питания для этого плана: {options.nutrition_goal}."
            )
        extras.append(
            f"Количество персон (порций): {persons}. "
            "Умножай объёмы ингредиентов с учётом этого числа."
        )
        hint = PLAN_MODE_PROMPT_HINTS.get(options.plan_mode or "")
        if hint:
            extras.append(hint)
        if extras:
            context.prompt_text = context.prompt_text + "\n" + "\n".join(extras)
        context.members_count = persons

    access = subscription_service.assert_menu_generation_allowed(db, user, scope)
    drink_mode = "none"
    allow_alcohol = False
    if options:
        if options.drink_mode:
            drink_mode = options.drink_mode
        allow_alcohol = bool(options.allow_alcohol)

    plan_days = options.plan_days if options and options.plan_days else 1

    profile = resolve_menu_profile(db, user)
    safe_pool = load_restriction_safe_recipe_pool(db, profile) if profile else []

    menus, used_ai = await generate_menus(
        context,
        db=db,
        user=user,
        scope=scope,
        persons_count=persons,
        drink_mode=drink_mode,  # type: ignore[arg-type]
        allow_alcohol=allow_alcohol,
        plan_days=plan_days,
    )

    menus, safety_notes = sanitize_menu_variants(
        db,
        menus,
        profile,
        replacement_pool=safe_pool,
    )
    if safety_notes:
        menus = append_safety_notes_to_menus(menus, safety_notes)

    if plan_days > 1:
        from app.services.menu_days import expand_variant_to_plan_days

        menus = [
            expand_variant_to_plan_days(db, m, plan_days, user=user, scope=scope)
            for m in menus
        ]
    subscription_service.commit_menu_generation(
        db,
        user,
        scope,
        access,
        used_ai=used_ai,
        model=current_model_name() if used_ai else None,
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
    meal_name = (
        payload.menu.meals[payload.meal_index].name
        if payload.meal_index < len(payload.menu.meals)
        else "?"
    )
    logger.info(
        "menu.replace_dish user=%s variant=%s meal_index=%s day_index=%s meal=%r",
        user.id,
        payload.menu.variant,
        payload.meal_index,
        payload.day_index,
        meal_name,
    )
    try:
        updated = await replace_meal(
            context,
            payload.menu,
            payload.meal_index,
            payload.hint,
            db=db,
            user=user,
            scope=scope,
            day_index=payload.day_index,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    selection = _get_latest_selection(db, scope)
    if selection is not None and selection.variant == updated.variant:
        menu_dict = updated.model_dump(mode="json")
        if isinstance(selection.menu_data, dict) and "_meta" in selection.menu_data:
            menu_dict["_meta"] = selection.menu_data["_meta"]
        selection.menu_data = menu_dict
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

    logger.info(
        "menu.replace_dish ok user=%s new_meal=%r",
        user.id,
        updated.meals[payload.meal_index].name
        if payload.meal_index < len(updated.meals)
        else "?",
    )

    return updated


def select_menu(
    db: Session,
    user: User,
    scope: AppScope,
    payload: SelectMenuRequest,
    *,
    plan_mode: str | None = None,
    persons_count: int | None = None,
) -> SelectedMenuResponse:
    existing = _get_latest_selection(db, scope)
    menu_dict = payload.menu.model_dump(mode="json")
    persons = persons_count or resolve_persons_count(db, user, scope)
    mode_key = plan_mode or "healthy"
    pantry_items = get_active_items_for_scope(db, scope)
    leftovers = list_active_leftovers(db, scope)
    pantry_used = min(800, max(120, len(pantry_items) * 35)) if pantry_items else 0
    menu_dict["_meta"] = {
        "context_fingerprint": compute_context_fingerprint(
            db, user, scope, persons_count=persons, plan_mode=mode_key
        ),
        "plan_mode": mode_key,
        "persons_count": persons,
        "pantry_used_rub": pantry_used,
        "savings_rub": pantry_used,
        "leftovers_count": len(leftovers),
        "plan_days": payload.menu.plan_days or menu_dict.get("plan_days") or 1,
    }

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
    from app.services.menu_selection import get_selected_menu as _get

    return _get(db, scope)


def _get_latest_selection(
    db: Session, scope: AppScope
) -> FamilyMenuSelection | None:
    from app.services.menu_selection import get_latest_selection

    return get_latest_selection(db, scope)


def _menu_from_storage(menu_data: dict) -> MenuVariant:
    from app.services.menu_selection import menu_from_storage

    return menu_from_storage(menu_data)


def _selection_response(
    selection: FamilyMenuSelection, scope: AppScope
) -> SelectedMenuResponse:
    from app.services.menu_selection import selection_response

    return selection_response(selection, scope)


async def run_quick_action(
    db: Session,
    user: User,
    scope: AppScope,
    action: str,
) -> tuple[str | None, SelectedMenuResponse | None, str | None]:
    if action == "replace_dish":
        return "/menu/current?replace=1", None, "Выберите блюдо для замены"

    mode_map = {
        "cheaper": ("economy", "economy"),
        "more_pantry": ("use_pantry", "balanced"),
        "more_protein": ("sport", "balanced"),
        "less_cooking_time": ("quick_simple", "quick"),
    }
    if action not in mode_map:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown action")

    plan_mode, pick_variant = mode_map[action]
    persons = resolve_persons_count(db, user, scope)
    result = await generate_menus_for_scope(
        db,
        user,
        scope,
        MenuGenerateRequest(persons_count=persons, plan_mode=plan_mode),
    )
    chosen = next((m for m in result.menus if m.variant == pick_variant), result.menus[0])
    saved = select_menu(
        db,
        user,
        scope,
        SelectMenuRequest(menu=chosen),
        plan_mode=plan_mode,
        persons_count=persons,
    )
    return None, saved, "Меню обновлено"
