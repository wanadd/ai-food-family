"""Menu selection persistence (no dependency on menu generation / AI)."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.menu_selection import FamilyMenuSelection
from app.schemas.menu import MenuVariant, SelectedMenuResponse
from app.services.app_scope import AppScope


def get_latest_selection(
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


def menu_from_storage(menu_data: dict) -> MenuVariant:
    data = dict(menu_data)
    data.pop("_meta", None)
    return MenuVariant.model_validate(data)


def selection_response(
    selection: FamilyMenuSelection, scope: AppScope
) -> SelectedMenuResponse:
    return SelectedMenuResponse(
        id=selection.id,
        scope_mode=scope.mode,
        user_id=selection.user_id,
        family_id=selection.family_id,
        variant=selection.variant,  # type: ignore[arg-type]
        menu=menu_from_storage(selection.menu_data),
        selected_at=selection.selected_at,
    )


def get_selected_menu(
    db: Session, scope: AppScope
) -> SelectedMenuResponse | None:
    selection = get_latest_selection(db, scope)
    if selection is None:
        return None
    return selection_response(selection, scope)
