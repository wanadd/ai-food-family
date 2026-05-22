"""Parse shopping amounts into numeric quantity and unit for pantry merge."""

from __future__ import annotations

import re

_UNIT_ALIASES: dict[str, str] = {
    "g": "г",
    "гр": "г",
    "г": "г",
    "kg": "кг",
    "кг": "кг",
    "ml": "мл",
    "мл": "мл",
    "l": "л",
    "л": "л",
    "шт": "шт",
    "штук": "шт",
    "штука": "шт",
    "pcs": "шт",
    "pc": "шт",
    "уп": "уп",
    "упак": "уп",
    "пач": "уп",
    "пачка": "уп",
}


def normalize_unit(raw: str) -> str:
    cleaned = raw.strip().lower()
    if not cleaned:
        return ""
    return _UNIT_ALIASES.get(cleaned, cleaned)


def parse_amount(amount: str) -> tuple[float | None, str]:
    text = re.sub(r"\s+", " ", (amount or "").strip())
    if not text:
        return None, ""

    match = re.match(
        r"^([\d]+(?:[.,]\d+)?)\s*(.*)$",
        text,
        re.IGNORECASE,
    )
    if not match:
        return None, normalize_unit(text)

    num_raw, unit_raw = match.group(1), match.group(2).strip()
    try:
        value = float(num_raw.replace(",", "."))
    except ValueError:
        return None, normalize_unit(text)

    unit = normalize_unit(unit_raw) if unit_raw else "шт"
    return value, unit


def format_amount(value: float, unit: str) -> str:
    if value == int(value):
        num = str(int(value))
    else:
        num = f"{value:g}".replace(".", ",")
    if unit:
        return f"{num} {unit}"
    return num


def merge_amount_strings(existing: str, added: str, unit: str) -> str:
    v1, u1 = parse_amount(existing)
    v2, u2 = parse_amount(added)
    if (
        v1 is not None
        and v2 is not None
        and u1
        and u2
        and u1 == u2 == unit
    ):
        return format_amount(v1 + v2, unit)
    if existing and added and existing != added:
        return f"{existing} + {added}"
    return added or existing
