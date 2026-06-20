"""Honest formatting of ingredient display amounts.

Single source of truth for turning (quantity, unit, to_taste flags) into the
``amount`` string shown in the UI. Never invents a ``шт`` unit:

* to_taste rows -> "по вкусу" (or quantity_text), without a unit;
* empty unit -> just the quantity (no fake "шт");
* a real "шт" unit is kept only for numeric/piece quantities.

Pure functions, no DB access. Used by recipe_storage (display + JSONB sync)
and by the audit / resync scripts.
"""

from __future__ import annotations

import re

# Phrases that mean "to taste" — they must never get a unit appended.
TO_TASTE_PHRASES = {
    "по вкусу",
    "немного",
    "щепотка",
    "на кончике ножа",
    "по желанию",
    "опционально",
}

# Legacy / dirty unit spellings -> canonical display form.
UNIT_DISPLAY_FIXES = {
    "ст. л.": "ст.л.",
    "ст.л": "ст.л.",
    "ст л": "ст.л.",
    "стл": "ст.л.",
    "ч. л.": "ч.л.",
    "ч.л": "ч.л.",
    "ч л": "ч.л.",
    "чл": "ч.л.",
    "зуб.": "зубчик",
    "зуб": "зубчик",
    "пуч.": "пучок",
    "пуч": "пучок",
    "стак.": "стакан",
    "стак": "стакан",
    "гр": "г",
    "гр.": "г",
}

# Generic "piece" units (kept only for real numeric quantities).
PIECE_UNITS = {"шт", "шт.", "штук", "штука", "штуки", "pcs", "pc"}

# Real measurement units we recognise (for sanitising legacy "<unit> шт").
KNOWN_UNITS = {
    "г", "кг", "мл", "л", "ст.л.", "ч.л.", "зубчик", "стакан", "пучок",
    "щепотка", "капля", "капель", "уп", "банка", "стебель",
}


def normalize_unit_display(unit: str | None) -> str:
    """Clean a unit for display. Empty stays empty (never becomes 'шт')."""
    u = (unit or "").strip()
    if not u:
        return ""
    return UNIT_DISPLAY_FIXES.get(u.lower(), u)


def _looks_numeric(value: str) -> bool:
    return bool(re.match(r"^\d+([.,]\d+)?$", value.strip()))


def is_to_taste(
    quantity: str | None,
    *,
    quantity_mode: str | None = None,
    is_to_taste_flag: bool = False,
) -> bool:
    if is_to_taste_flag:
        return True
    if (quantity_mode or "").strip().lower() == "to_taste":
        return True
    return (quantity or "").strip().lower() in TO_TASTE_PHRASES


def format_ingredient_amount(
    quantity: str | None,
    unit: str | None,
    *,
    quantity_mode: str | None = None,
    is_to_taste_flag: bool = False,
    quantity_text: str | None = None,
) -> str:
    """Build the display amount. Never appends a default 'шт'."""
    q = (quantity or "").strip()
    u = normalize_unit_display(unit)

    if is_to_taste(q, quantity_mode=quantity_mode, is_to_taste_flag=is_to_taste_flag):
        text = (quantity_text or "").strip()
        if text:
            return text
        if q and not _looks_numeric(q):
            return q
        return "по вкусу"

    if not q and not u:
        return ""
    if q and u:
        return f"{q} {u}"
    if q:
        return q
    return u


def sanitize_amount_text(amount: str | None) -> str:
    """Fix already-stored legacy amounts like 'по вкусу шт' / '800 г шт'.

    Strips a trailing piece unit when it was wrongly appended after a real
    unit or a to_taste phrase. Real piece amounts ('5 шт') are left intact.
    """
    s = re.sub(r"\s+", " ", (amount or "").strip())
    if not s:
        return ""
    match = re.match(r"^(.*?)\s+(шт\.?|штук[аи]?|pcs?|pc)$", s, re.IGNORECASE)
    if match:
        head = match.group(1).strip()
        head_low = head.lower()
        if head_low in TO_TASTE_PHRASES or any(
            head_low.endswith(unit) for unit in KNOWN_UNITS
        ):
            return head
    return s
