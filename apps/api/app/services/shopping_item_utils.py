"""Normalize shopping list items (storage ↔ API)."""

from __future__ import annotations

import hashlib
import re
import uuid
from datetime import datetime, timezone

from app.schemas.shopping_list import ShoppingListItem
from app.services.amount_parser import format_amount, normalize_unit, parse_amount
from app.services.shopping_categories import normalize_category


def normalize_name(name: str) -> str:
    return re.sub(r"\s+", " ", name.strip().lower())


def make_item_id(name: str, category: str, unit: str) -> str:
    key = f"{category}:{normalize_name(name)}:{normalize_unit(unit)}"
    return hashlib.sha256(key.encode()).hexdigest()[:16]


def new_manual_item_id() -> str:
    return uuid.uuid4().hex[:16]


def display_amount(quantity: str, unit: str, fallback: str = "") -> str:
    if fallback.strip():
        return fallback.strip()
    q = quantity.strip()
    u = normalize_unit(unit) or "шт"
    if not q:
        return format_amount(1, u)
    try:
        value = float(q.replace(",", "."))
        return format_amount(value, u)
    except ValueError:
        return f"{q} {u}".strip()


def normalize_item(raw: dict | ShoppingListItem) -> ShoppingListItem:
    if isinstance(raw, ShoppingListItem):
        item = raw
    else:
        item = ShoppingListItem.model_validate(raw)

    unit = normalize_unit(item.unit) if item.unit else ""
    quantity = item.quantity.strip() if item.quantity else ""

    if not quantity and not unit and item.amount:
        parsed_val, parsed_unit = parse_amount(item.amount)
        if parsed_val is not None:
            quantity = str(int(parsed_val)) if parsed_val == int(parsed_val) else str(parsed_val)
        unit = parsed_unit or "шт"

    if not unit:
        unit = "шт"
    if not quantity:
        quantity = "1"

    amount = display_amount(quantity, unit, item.amount)
    category = normalize_category(item.category)

    item_id = item.id
    if not item_id or len(item_id) < 8:
        item_id = make_item_id(item.name, category, unit)
    elif not unit and not item.quantity:
        item_id = make_item_id(item.name, category, unit)

    return item.model_copy(
        update={
            "id": item_id,
            "category": category,
            "quantity": quantity,
            "unit": unit,
            "amount": amount,
            "source": item.source or "menu",
        }
    )


def item_from_menu_ingredient(
    name: str,
    amount_str: str,
    category_hint: str | None,
    previous: ShoppingListItem | None,
) -> ShoppingListItem:
    from app.services.shopping_categories import infer_category

    category = infer_category(name, category_hint)
    parsed_val, unit = parse_amount(amount_str)
    quantity = "1"
    if parsed_val is not None:
        quantity = (
            str(int(parsed_val))
            if parsed_val == int(parsed_val)
            else str(parsed_val)
        )
    unit = unit or "шт"
    item_id = make_item_id(name, category, unit)

    if previous and previous.id == item_id:
        return previous.model_copy(
            update={
                "name": name,
                "category": category,
                "quantity": quantity,
                "unit": unit,
                "amount": display_amount(quantity, unit),
                "source": "menu",
            }
        )

    return ShoppingListItem(
        id=item_id,
        name=name.strip(),
        category=category,
        quantity=quantity,
        unit=unit,
        amount=display_amount(quantity, unit),
        amounts=[amount_str] if amount_str else [],
        source="menu",
        checked=previous.checked if previous else False,
        checked_by_user_id=previous.checked_by_user_id if previous else None,
        checked_by_name=previous.checked_by_name if previous else None,
        checked_at=previous.checked_at if previous else None,
        linked_pantry_item_id=previous.linked_pantry_item_id if previous else None,
        added_to_pantry=bool(previous.linked_pantry_item_id) if previous else False,
        created_by_user_id=previous.created_by_user_id if previous else None,
    )
