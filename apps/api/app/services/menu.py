from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.menu_selection import FamilyMenuSelection
from app.models.user import User
from app.schemas.menu import (
    MenuGenerateResponse,
    MenuVariant,
    ReplaceDishRequest,
    SelectMenuRequest,
    SelectedMenuResponse,
)
from app.services import family as family_service
from app.services import shopping_list as shopping_list_service
from app.services.menu_ai import generate_menus, replace_meal
from app.services.menu_context import build_menu_context


async def generate_family_menus(db: Session, user: User) -> MenuGenerateResponse:
    context = build_menu_context(db, user)
    menus, used_ai = await generate_menus(context)
    return MenuGenerateResponse(
        menus=menus,
        family_name=context.family_name,
        members_count=context.members_count,
        generated_with_ai=used_ai,
    )


async def replace_dish(
    db: Session, user: User, payload: ReplaceDishRequest
) -> MenuVariant:
    context = build_menu_context(db, user)
    try:
        updated = await replace_meal(
            context, payload.menu, payload.meal_index, payload.hint
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    membership = family_service.get_user_membership(db, user)
    if membership is not None:
        selection = (
            db.query(FamilyMenuSelection)
            .filter(FamilyMenuSelection.family_id == membership.family_id)
            .order_by(FamilyMenuSelection.selected_at.desc())
            .first()
        )
        if selection is not None and selection.variant == updated.variant:
            selection.menu_data = updated.model_dump(mode="json")
            db.commit()
            shopping_list_service.sync_from_menu(
                db,
                membership.family_id,
                updated,
                selection.id,
            )

    return updated


def select_menu(
    db: Session, user: User, payload: SelectMenuRequest
) -> SelectedMenuResponse:
    membership = family_service.get_user_membership(db, user)
    if membership is None:
        return SelectedMenuResponse(
            id=0,
            family_id=0,
            variant=payload.menu.variant,
            menu=payload.menu,
            selected_at=datetime.now(timezone.utc),
        )

    existing = (
        db.query(FamilyMenuSelection)
        .filter(FamilyMenuSelection.family_id == membership.family_id)
        .order_by(FamilyMenuSelection.selected_at.desc())
        .first()
    )

    menu_dict = payload.menu.model_dump(mode="json")

    if existing is not None:
        existing.variant = payload.menu.variant
        existing.menu_data = menu_dict
        existing.user_id = user.id
        selection = existing
    else:
        selection = FamilyMenuSelection(
            family_id=membership.family_id,
            user_id=user.id,
            variant=payload.menu.variant,
            menu_data=menu_dict,
        )
        db.add(selection)

    db.commit()
    db.refresh(selection)
    shopping_list_service.sync_from_menu(
        db,
        membership.family_id,
        payload.menu,
        selection.id,
    )
    return _selection_response(selection)


def get_selected_menu(db: Session, user: User) -> SelectedMenuResponse | None:
    membership = family_service.get_user_membership(db, user)
    if membership is None:
        return None

    selection = (
        db.query(FamilyMenuSelection)
        .filter(FamilyMenuSelection.family_id == membership.family_id)
        .order_by(FamilyMenuSelection.selected_at.desc())
        .first()
    )
    if selection is None:
        return None
    return _selection_response(selection)


def _selection_response(selection: FamilyMenuSelection) -> SelectedMenuResponse:
    return SelectedMenuResponse(
        id=selection.id,
        family_id=selection.family_id,
        variant=selection.variant,  # type: ignore[arg-type]
        menu=MenuVariant.model_validate(selection.menu_data),
        selected_at=selection.selected_at,
    )
