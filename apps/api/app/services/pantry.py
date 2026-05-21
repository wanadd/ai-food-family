from datetime import date

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.family import FamilyMember
from app.models.pantry import FamilyPantryItem
from app.models.user import User
from app.schemas.pantry import (
    PantryItemCreate,
    PantryItemResponse,
    PantryItemUpdate,
    PantryListResponse,
)
from app.services import family as family_service
from app.services.shopping_list import _infer_category
from app.schemas.menu import MenuIngredient


def _require_family_membership(db: Session, user: User) -> FamilyMember:
    membership = family_service.get_user_membership(db, user)
    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Создайте семью для общего учёта остатков",
        )
    return membership


def _member_names(db: Session, family_id: int) -> dict[int, str]:
    members = (
        db.query(FamilyMember)
        .filter(FamilyMember.family_id == family_id)
        .all()
    )
    return {
        member.user_id: member.display_name
        for member in members
        if member.user_id is not None
    }


def _item_response(
    item: FamilyPantryItem, member_names: dict[int, str], today: date
) -> PantryItemResponse:
    days = (item.expires_at - today).days
    return PantryItemResponse(
        id=item.id,
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


def list_pantry(db: Session, user: User) -> PantryListResponse:
    membership = _require_family_membership(db, user)
    today = date.today()
    items = (
        db.query(FamilyPantryItem)
        .filter(FamilyPantryItem.family_id == membership.family_id)
        .order_by(FamilyPantryItem.expires_at.asc(), FamilyPantryItem.name.asc())
        .all()
    )
    member_names = _member_names(db, membership.family_id)
    responses = [_item_response(item, member_names, today) for item in items]
    active = sum(1 for item in responses if not item.is_expired)
    return PantryListResponse(
        family_id=membership.family_id,
        items=responses,
        active_count=active,
        expired_count=len(responses) - active,
    )


def get_active_items(db: Session, family_id: int) -> list[FamilyPantryItem]:
    today = date.today()
    return (
        db.query(FamilyPantryItem)
        .filter(
            FamilyPantryItem.family_id == family_id,
            FamilyPantryItem.expires_at >= today,
        )
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


def add_item(
    db: Session, user: User, payload: PantryItemCreate
) -> PantryItemResponse:
    membership = _require_family_membership(db, user)
    item = FamilyPantryItem(
        family_id=membership.family_id,
        name=payload.name.strip(),
        quantity=payload.quantity.strip(),
        expires_at=payload.expires_at,
        added_by_user_id=user.id,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    member_names = _member_names(db, membership.family_id)
    return _item_response(item, member_names, date.today())


def update_item(
    db: Session, user: User, item_id: int, payload: PantryItemUpdate
) -> PantryItemResponse:
    membership = _require_family_membership(db, user)
    item = (
        db.query(FamilyPantryItem)
        .filter(
            FamilyPantryItem.id == item_id,
            FamilyPantryItem.family_id == membership.family_id,
        )
        .one_or_none()
    )
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
    member_names = _member_names(db, membership.family_id)
    return _item_response(item, member_names, date.today())


def delete_item(db: Session, user: User, item_id: int) -> None:
    membership = _require_family_membership(db, user)
    item = (
        db.query(FamilyPantryItem)
        .filter(
            FamilyPantryItem.id == item_id,
            FamilyPantryItem.family_id == membership.family_id,
        )
        .one_or_none()
    )
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
