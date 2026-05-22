"""Add shopping list items to pantry when marked purchased."""

from __future__ import annotations

import re
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.models.pantry import FamilyPantryItem
from app.models.user import User
from app.schemas.shopping_list import ShoppingListItem
from app.services.amount_parser import format_amount, merge_amount_strings, normalize_unit
from app.services.app_scope import AppScope
from app.services.pantry import _pantry_query
from app.services.shopping_categories import normalize_category
from app.services.shopping_item_utils import display_amount


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
    unit_norm = normalize_unit(unit).strip().lower()
    for item in _pantry_query(db, scope).all():
        if _normalize_name(item.name) != normalized:
            continue
        item_unit = normalize_unit(item.unit or "").strip().lower()
        if item_unit == unit_norm:
            return item
    return None


def add_or_merge_from_shopping(
    db: Session,
    user: User,
    scope: AppScope,
    shopping_item: ShoppingListItem,
) -> FamilyPantryItem:
    unit = normalize_unit(shopping_item.unit) or "шт"
    qty_display = display_amount(
        shopping_item.quantity,
        unit,
        shopping_item.amount,
    )

    existing = find_matching_pantry_item(db, scope, shopping_item.name, unit)
    if existing is not None:
        existing.quantity = merge_amount_strings(existing.quantity, qty_display, unit)
        existing.unit = unit
        existing.source = "shopping_list"
        existing.category = normalize_category(shopping_item.category)
        if shopping_item.note:
            existing.note = shopping_item.note
        db.commit()
        db.refresh(existing)
        return existing

    item = FamilyPantryItem(
        user_id=scope.user_id if scope.is_personal else None,
        family_id=scope.family_id if scope.is_family else None,
        name=shopping_item.name.strip(),
        category=normalize_category(shopping_item.category),
        quantity=qty_display,
        unit=unit,
        source="shopping_list",
        note=shopping_item.note,
        expires_at=_default_expiry(),
        added_by_user_id=user.id,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item
