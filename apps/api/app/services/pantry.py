from datetime import date

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.family import FamilyMember
from app.models.pantry import FamilyPantryItem
from app.models.user import User
from app.schemas.menu import MenuIngredient
from app.schemas.pantry import (
    PantryItemCreate,
    PantryItemResponse,
    PantryItemUpdate,
    PantryListResponse,
)
from app.services.app_scope import AppScope
from app.services.shopping_list import _infer_category


def _member_names(db: Session, family_id: int) -> dict[int, str]:
    members = (
        db.query(FamilyMember).filter(FamilyMember.family_id == family_id).all()
    )
    return {
        member.user_id: member.display_name
        for member in members
        if member.user_id is not None
    }


def _item_response(
    item: FamilyPantryItem,
    scope: AppScope,
    member_names: dict[int, str],
    today: date,
) -> PantryItemResponse:
    days = (item.expires_at - today).days
    return PantryItemResponse(
        id=item.id,
        scope_mode=scope.mode,
        user_id=item.user_id,
        family_id=item.family_id,
        name=item.name,
        quantity=item.quantity,
        expires_at=item.expires_at,
        is_expired=days < 0,
        days_until_expiry=days,
        added_by_name=member_names.get(item.added_by_user_id)
        if item.added_by_user_id
        else None,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


def _pantry_query(db: Session, scope: AppScope):
    query = db.query(FamilyPantryItem)
    if scope.is_family:
        return query.filter(FamilyPantryItem.family_id == scope.family_id)
    return query.filter(
        FamilyPantryItem.user_id == scope.user_id,
        FamilyPantryItem.family_id.is_(None),
    )


def get_active_items_for_scope(db: Session, scope: AppScope) -> list[FamilyPantryItem]:
    today = date.today()
    return (
        _pantry_query(db, scope)
        .filter(FamilyPantryItem.expires_at >= today)
        .order_by(FamilyPantryItem.expires_at.asc())
        .all()
    )


def format_leftovers_for_prompt(items: list[FamilyPantryItem]) -> list[str]:
    lines: list[str] = []
    for item in items:
        lines.append(
            f"- {item.name}: {item.quantity}, годен до {item.expires_at.isoformat()}"
        )
    return lines


def list_pantry(db: Session, user: User, scope: AppScope) -> PantryListResponse:
    today = date.today()
    items = (
        _pantry_query(db, scope)
        .order_by(FamilyPantryItem.expires_at.asc(), FamilyPantryItem.name.asc())
        .all()
    )
    member_names = (
        _member_names(db, scope.family_id) if scope.is_family and scope.family_id else {}
    )
    responses = [_item_response(item, scope, member_names, today) for item in items]
    active = sum(1 for item in responses if not item.is_expired)
    return PantryListResponse(
        scope_mode=scope.mode,
        user_id=scope.user_id if scope.is_personal else None,
        family_id=scope.family_id,
        items=responses,
        active_count=active,
        expired_count=len(responses) - active,
    )


def add_item(
    db: Session, user: User, scope: AppScope, payload: PantryItemCreate
) -> PantryItemResponse:
    item = FamilyPantryItem(
        user_id=scope.user_id if scope.is_personal else None,
        family_id=scope.family_id if scope.is_family else None,
        name=payload.name.strip(),
        quantity=payload.quantity.strip(),
        expires_at=payload.expires_at,
        added_by_user_id=user.id,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    member_names = (
        _member_names(db, scope.family_id) if scope.is_family and scope.family_id else {}
    )
    return _item_response(item, scope, member_names, date.today())


def _get_item(db: Session, scope: AppScope, item_id: int) -> FamilyPantryItem | None:
    return (
        _pantry_query(db, scope).filter(FamilyPantryItem.id == item_id).one_or_none()
    )


def update_item(
    db: Session,
    user: User,
    scope: AppScope,
    item_id: int,
    payload: PantryItemUpdate,
) -> PantryItemResponse:
    item = _get_item(db, scope, item_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    if payload.name is not None:
        item.name = payload.name.strip()
    if payload.quantity is not None:
        item.quantity = payload.quantity.strip()
    if payload.expires_at is not None:
        item.expires_at = payload.expires_at

    db.commit()
    db.refresh(item)
    member_names = (
        _member_names(db, scope.family_id) if scope.is_family and scope.family_id else {}
    )
    return _item_response(item, scope, member_names, date.today())


def delete_item(db: Session, scope: AppScope, item_id: int) -> None:
    item = _get_item(db, scope, item_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    db.delete(item)
    db.commit()


def leftovers_to_ingredients(items: list[FamilyPantryItem]) -> list[MenuIngredient]:
    result: list[MenuIngredient] = []
    for item in items:
        category = _infer_category(item.name, None)
        result.append(
            MenuIngredient(
                name=item.name,
                amount=item.quantity,
                category=category,
            )
        )
    return result
