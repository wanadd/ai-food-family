"""Add shopping list items to pantry when marked purchased."""

from __future__ import annotations

import re
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.models.pantry import FamilyPantryItem
from app.models.user import User
from app.schemas.shopping_list import ShoppingListItem
from app.services.amount_parser import format_amount, merge_amount_strings, parse_amount
from app.services.app_scope import AppScope
from app.services.pantry import _pantry_query


def _normalize_name(name: str) -> str:
    return re.sub(r"\s+", " ", name.strip().lower())


def _default_expiry() -> date:
    return date.today() + timedelta(days=7)


def find_matching_pantry_item(
    db: Session,
    scope: AppScope,
    name: str,
    unit: str,
) -> FamilyPantryItem | None:
    normalized = _normalize_name(name)
    unit_norm = unit.strip().lower()
    for item in _pantry_query(db, scope).all():
        if _normalize_name(item.name) != normalized:
            continue
        item_unit = (item.unit or "").strip().lower()
        if item_unit == unit_norm:
            return item
    return None


def add_or_merge_from_shopping(
    db: Session,
    user: User,
    scope: AppScope,
    shopping_item: ShoppingListItem,
) -> FamilyPantryItem:
    _, unit = parse_amount(shopping_item.amount)
    if not unit:
        unit = "шт"

    existing = find_matching_pantry_item(db, scope, shopping_item.name, unit)
    if existing is not None:
        merged_qty = merge_amount_strings(
            existing.quantity,
            shopping_item.amount,
            unit,
        )
        existing.quantity = merged_qty
        existing.unit = unit
        if existing.source != "shopping_list":
            existing.source = "shopping_list"
        db.commit()
        db.refresh(existing)
        return existing

    item = FamilyPantryItem(
        user_id=scope.user_id if scope.is_personal else None,
        family_id=scope.family_id if scope.is_family else None,
        name=shopping_item.name.strip(),
        quantity=shopping_item.amount.strip() or format_amount(1, unit),
        unit=unit,
        source="shopping_list",
        expires_at=_default_expiry(),
        added_by_user_id=user.id,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item
