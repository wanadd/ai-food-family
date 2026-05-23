"""Heuristic text parser for Telegram quick commands (MVP, no LLM)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Literal

from app.services.shopping_categories import infer_category, is_food_category

ActionType = Literal[
    "pantry_add",
    "shopping_add",
    "shopping_need",
    "leftover_note",
    "unknown",
]

NON_FOOD_HINTS = (
    "порошок",
    "стиральн",
    "мыло",
    "шампун",
    "мешк",
    "корм",
    "кот",
    "собак",
    "памперс",
    "салфет",
    "губк",
    "химия",
    "аптек",
)


@dataclass
class ParsedMessage:
    action: ActionType
    items: list[str] = field(default_factory=list)
    leftover_note: str | None = None
    raw_text: str = ""

    def item_categories(self) -> list[tuple[str, str, bool]]:
        """name, category slug, is_food."""
        result: list[tuple[str, str, bool]] = []
        for name in self.items:
            cat = infer_category(name, None)
            if any(h in name.lower() for h in NON_FOOD_HINTS):
                cat = infer_category(name, "дом_и_химия")
            result.append((name, cat, is_food_category(cat)))
        return result


def _normalize_item_name(raw: str) -> str:
    name = raw.strip()
    name = re.sub(r"^(в|во|на)\s+", "", name, flags=re.IGNORECASE)
    name = name.strip(" .-—")
    if len(name) > 1:
        name = name[0].upper() + name[1:]
    return name


def _extract_tail(text: str, keyword: str) -> str:
    lower = text.lower()
    idx = lower.find(keyword)
    if idx < 0:
        return text
    return text[idx + len(keyword) :].strip(" :—–-")


def _split_items(fragment: str) -> list[str]:
    if not fragment.strip():
        return []
    parts = re.split(r"[,;]|\s+и\s+|\s+and\s+", fragment, flags=re.IGNORECASE)
    items: list[str] = []
    for part in parts:
        cleaned = _normalize_item_name(part)
        if len(cleaned) >= 2:
            items.append(cleaned)
    return items


def parse_message(text: str) -> ParsedMessage:
    raw = (text or "").strip()
    if not raw:
        return ParsedMessage(action="unknown", raw_text=raw)

    lower = raw.lower()

    if "осталось" in lower or "остались" in lower or "остался" in lower:
        note = _extract_tail(raw, "остал")
        if not note:
            note = raw
        return ParsedMessage(
            action="leftover_note",
            leftover_note=note,
            raw_text=raw,
        )

    if "купил" in lower or "купила" in lower or "купили" in lower:
        tail = _extract_tail(raw, "купил")
        if "купила" in lower and tail == raw:
            tail = _extract_tail(raw, "купила")
        if "купили" in lower and tail == raw:
            tail = _extract_tail(raw, "купили")
        items = _split_items(tail) if tail != raw else _split_items(raw)
        return ParsedMessage(action="pantry_add", items=items, raw_text=raw)

    if lower.startswith("добавь") or lower.startswith("добавить"):
        tail = _extract_tail(raw, "добавь")
        if tail == raw:
            tail = _extract_tail(raw, "добавить")
        items = _split_items(tail)
        return ParsedMessage(action="shopping_add", items=items, raw_text=raw)

    if "закончил" in lower or "закончилась" in lower or "закончилось" in lower:
        tail = _extract_tail(raw, "законч")
        items = _split_items(tail) if tail != raw else _split_items(raw)
        return ParsedMessage(action="shopping_need", items=items, raw_text=raw)

    return ParsedMessage(action="unknown", raw_text=raw)
