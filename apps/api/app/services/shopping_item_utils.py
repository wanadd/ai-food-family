"""Normalize shopping list items (storage ↔ API)."""

from __future__ import annotations

import hashlib
import math
import re
import uuid

from app.schemas.shopping_list import ShoppingListItem
from app.services.amount_parser import format_amount, normalize_unit, parse_amount
from app.services.categories_v1 import DEFAULT_CATEGORY_SLUG
from app.services.shopping_categories import infer_category, normalize_category


def normalize_name(name: str) -> str:
    return re.sub(r"\s+", " ", name.strip().lower())


# --------------------------- shopping cleanup helpers ---------------------------

# Raw/abbreviated unit spellings -> clean display form.
_SHOPPING_UNIT_MAP: dict[str, str] = {
    "пуч.": "пучок", "пуч": "пучок",
    "зуб.": "зубчик", "зуб": "зубчик",
    "стак.": "стакан", "стак": "стакан",
    "упак.": "упаковка", "упак": "упаковка", "уп": "упаковка", "уп.": "упаковка",
    "пакет.": "пакет",
    "ст. л.": "ст.л.", "ст.л": "ст.л.", "стл": "ст.л.",
    "ч. л.": "ч.л.", "ч.л": "ч.л.", "чл": "ч.л.",
    "гр": "г", "гр.": "г",
}

# Units that represent countable pieces -> rounded up to whole numbers.
ROUND_UP_UNITS: frozenset[str] = frozenset({"шт", "пучок", "зубчик"})

# Pantry staples that should never end up on a shopping list (V1).
_PANTRY_SKIP_NAMES: frozenset[str] = frozenset({
    "соль", "вода", "перец", "перец черный", "перец чёрный",
    "перец красный жгучий", "перец душистый", "специи", "приправа",
    "приправы", "зира", "куркума", "тимьян", "шалфей", "лист лавровый",
    "лавровый лист", "ванилин",
})

_GREENS_KEYWORDS: tuple[str, ...] = (
    "укроп", "петрушк", "базилик", "кинз", "мят", "зелень",
)


def normalize_shopping_unit(unit: str | None) -> str:
    """Clean a unit for shopping display (пуч. -> пучок, ст. л. -> ст.л.)."""
    u = (unit or "").strip()
    if not u:
        return ""
    return _SHOPPING_UNIT_MAP.get(u.lower(), u)


def clean_float(value: float) -> float:
    """Strip floating-point garbage: 0.6000000000000001 -> 0.6."""
    rounded = round(float(value), 3)
    if rounded == int(rounded):
        return float(int(rounded))
    return rounded


def _quantity_to_str(value: float) -> str:
    value = clean_float(value)
    if value == int(value):
        return str(int(value))
    return ("%g" % value).replace(",", ".")


def parse_shopping_amount(amount_str: str) -> tuple[float | None, str]:
    """Parse an amount, handling fractions ("1/2 ст.л." -> 0.5 ст.л.)."""
    s = (amount_str or "").strip()
    frac = re.match(r"^(\d+)\s*/\s*(\d+)\s*(.*)$", s)
    if frac:
        num, den = int(frac.group(1)), int(frac.group(2))
        rest = frac.group(3).strip()
        value = (num / den) if den else None
        return value, normalize_shopping_unit(normalize_unit(rest) if rest else "")
    value, unit = parse_amount(s)
    return value, normalize_shopping_unit(unit)


def normalize_shopping_quantity(
    quantity: str, unit: str, name: str
) -> tuple[str, str]:
    """Clean quantity/unit: round pieces up, strip float garbage elsewhere."""
    u = normalize_shopping_unit(unit)
    q = (quantity or "").strip()
    try:
        value = float(q.replace(",", "."))
    except ValueError:
        # Non-numeric quantity (e.g. leftover text) — keep verbatim.
        return q or "1", (u or "шт")

    value = clean_float(value)
    effective_unit = u or "шт"
    if effective_unit in ROUND_UP_UNITS:
        whole = max(1, math.ceil(value - 1e-9))
        return str(whole), effective_unit
    return _quantity_to_str(value), effective_unit


def should_skip_menu_ingredient_for_shopping(
    name: str, amount_str: str, category_hint: str | None = None
) -> bool:
    """V1 rule: drop pantry staples / micro spices / "по вкусу" from shopping."""
    n = normalize_name(name)
    if not n:
        return True
    amount_lower = (amount_str or "").lower()
    if "по вкусу" in amount_lower:
        return True
    if n in _PANTRY_SKIP_NAMES:
        return True

    value, unit = parse_shopping_amount(amount_str)
    category = normalize_category(category_hint) if category_hint else None

    if category == "специи_соусы":
        if value is not None and value < 1 and unit in {"ч.л.", "ст.л.", "шт", ""}:
            return True

    if any(keyword in n for keyword in _GREENS_KEYWORDS):
        if unit == "пучок" and value is not None and value < 0.5:
            return True

    return False


# Name keyword -> forced shopping category (overrides a wrong menu hint).
_CATEGORY_OVERRIDES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("яйца", ("яйц",)),
    ("рыба_морепродукты", (
        "кальмар", "сельд", "треск", "шпрот", "лосос", "тунец", "минтай",
        "креветк", "морепродукт", "рыба", "рыб",
    )),
    ("молочные", (
        "молок", "сметан", "сливк", "сыр", "творог", "кефир", "йогурт",
        "масло слив",
    )),
    ("мясо_птица", (
        "куриц", "курин", "грудк", "фарш", "свинин", "говядин", "индейк",
        "окороч", "голень", "бедр", "котлет", "колбас", "сосиск", "мясо",
    )),
)


def normalize_shopping_category(name: str, current_category: str | None) -> str:
    """Force correct categories for common items (eggs out of meat, etc.)."""
    n = normalize_name(name)
    for category, keywords in _CATEGORY_OVERRIDES:
        if any(keyword in n for keyword in keywords):
            return category
    if current_category:
        normalized = normalize_category(current_category)
        if normalized and normalized != DEFAULT_CATEGORY_SLUG:
            return normalized
    return infer_category(name, current_category)


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


def predict_menu_item_id(name: str, amount_str: str, category_hint: str | None) -> str:
    """Compute the item id a menu ingredient would map to (for dedupe/sum)."""
    category = normalize_shopping_category(name, category_hint)
    _, unit = parse_shopping_amount(amount_str)
    _, unit = normalize_shopping_quantity("1", unit, name)
    return make_item_id(name, category, unit)


def item_from_menu_ingredient(
    name: str,
    amount_str: str,
    category_hint: str | None,
    previous: ShoppingListItem | None,
) -> ShoppingListItem:
    category = normalize_shopping_category(name, category_hint)
    parsed_val, raw_unit = parse_shopping_amount(amount_str)
    quantity_in = "1" if parsed_val is None else _quantity_to_str(parsed_val)
    quantity, unit = normalize_shopping_quantity(quantity_in, raw_unit, name)
    item_id = make_item_id(name, category, unit)
    amount = display_amount(quantity, unit)

    if previous and previous.id == item_id:
        return previous.model_copy(
            update={
                "name": name.strip(),
                "category": category,
                "quantity": quantity,
                "unit": unit,
                "amount": amount,
                "amounts": [amount_str] if amount_str else [],
                "source": "menu",
            }
        )

    return ShoppingListItem(
        id=item_id,
        name=name.strip(),
        category=category,
        quantity=quantity,
        unit=unit,
        amount=amount,
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


def sum_menu_items(existing: ShoppingListItem, added: ShoppingListItem) -> ShoppingListItem:
    """Combine two menu items with the same id (sum quantities, merge amounts)."""
    try:
        qa = float((existing.quantity or "0").replace(",", "."))
        qb = float((added.quantity or "0").replace(",", "."))
        total = clean_float(qa + qb)
        if existing.unit in ROUND_UP_UNITS:
            total = float(max(1, math.ceil(total - 1e-9)))
        quantity = _quantity_to_str(total)
    except ValueError:
        quantity = existing.quantity
    amounts = list(dict.fromkeys([*existing.amounts, *added.amounts]))
    return existing.model_copy(
        update={
            "quantity": quantity,
            "amount": display_amount(quantity, existing.unit),
            "amounts": amounts,
        }
    )
