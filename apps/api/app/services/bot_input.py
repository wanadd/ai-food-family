"""Execute Telegram quick-input actions (pantry, shopping, leftovers)."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.pantry import PantryItemCreate
from app.schemas.shopping_list import ShoppingItemCreateRequest, ShoppingItemUpdateRequest
from app.services import care as care_service
from app.services import pantry as pantry_service
from app.services import shopping_list as shopping_service
from app.services.shopping_category_service import resolve_category_for_item
from app.services.app_scope import AppScope, resolve_scope
from app.services.message_parser import ParsedMessage, parse_message
from app.services.receipt_ocr import ReceiptLine
from app.services.shopping_categories import infer_category, is_food_category

logger = logging.getLogger(__name__)

ITEM_EMOJI: dict[str, str] = {
    "молочное": "🥛",
    "яйца": "🥚",
    "мясо": "🥩",
    "рыба": "🐟",
    "овощи": "🥕",
    "фрукты": "🍎",
    "крупы": "🌾",
    "продукты": "🛒",
    "дом_и_химия": "🧴",
    "питомцы": "🐾",
}


@dataclass
class ActionLine:
    emoji: str
    name: str
    destination: str


def _emoji_for_category(category: str) -> str:
    return ITEM_EMOJI.get(category, "📦")


def _normalize_match(name: str) -> str:
    return re.sub(r"\s+", " ", name.strip().lower())


def _add_to_pantry(
    db: Session, user: User, scope: AppScope, name: str, category: str
) -> ActionLine:
    pantry_service.add_item(
        db,
        user,
        scope,
        PantryItemCreate(
            name=name,
            category=category,
            quantity="1",
            unit="шт",
            source="telegram",
        ),
    )
    dest = "запасы" if is_food_category(category) else "запасы дома"
    return ActionLine(
        emoji=_emoji_for_category(category),
        name=name,
        destination=dest,
    )


def _add_to_shopping(
    db: Session, user: User, scope: AppScope, name: str, category: str, is_food: bool
) -> ActionLine:
    slug, _ = resolve_category_for_item(db, scope, category, is_food=is_food)
    try:
        shopping_service.create_item(
            db,
            user,
            scope,
            ShoppingItemCreateRequest(
                name=name,
                category=slug,
                quantity="1",
                unit="шт",
                is_food=is_food,
            ),
        )
    except HTTPException as exc:
        if exc.status_code != 409:
            raise
    return ActionLine(
        emoji=_emoji_for_category(slug),
        name=name,
        destination="покупки",
    )


def _mark_shopping_bought(
    db: Session, user: User, scope: AppScope, name: str
) -> bool:
    listing = shopping_service.get_shopping_list(db, user, scope)
    key = _normalize_match(name)
    for item in listing.items:
        if _normalize_match(item.name) == key and not item.checked:
            shopping_service.update_item(
                db,
                user,
                scope,
                item.id,
                ShoppingItemUpdateRequest(checked=True),
            )
            return True
    return False


def _record_leftover(db: Session, user: User, scope: AppScope, note: str) -> ActionLine:
    care_service.log_care_event(
        db,
        user,
        "leftover_note",
        family_id=scope.family_id,
        payload={"note": note, "source": "telegram"},
    )
    return ActionLine(emoji="🍲", name=note[:60], destination="остатки")


def execute_parsed_message(
    db: Session, user: User, scope: AppScope, parsed: ParsedMessage
) -> list[ActionLine]:
    lines: list[ActionLine] = []

    if parsed.action == "leftover_note" and parsed.leftover_note:
        lines.append(_record_leftover(db, user, scope, parsed.leftover_note))
        return lines

    if not parsed.items:
        return lines

    for name, category, is_food in parsed.item_categories():
        if parsed.action == "pantry_add":
            lines.append(_add_to_pantry(db, user, scope, name, category))
        elif parsed.action in ("shopping_add", "shopping_need"):
            lines.append(_add_to_shopping(db, user, scope, name, category, is_food))

    return lines


def process_text_message(
    db: Session, user: User, text: str
) -> tuple[str, list[ActionLine]]:
    scope = resolve_scope(db, user, None)
    parsed = parse_message(text)
    if parsed.action == "unknown":
        return (
            "Не понял команду. Примеры:\n"
            "• Купил молоко и яйца\n"
            "• Добавь порошок и мешки\n"
            "• Закончилась гречка\n"
            "• Осталось 4 порции борща",
            [],
        )

    if not parsed.items and parsed.action != "leftover_note":
        return ("Не нашёл товары в сообщении. Уточните список через запятую.", [])

    results = execute_parsed_message(db, user, scope, parsed)
    if not results:
        return ("Не удалось ничего добавить.", [])

    body = "Готово, добавил:\n" + "\n".join(
        f"{r.emoji} {r.name} — {r.destination}" for r in results
    )
    return body, results


def process_receipt_lines(
    db: Session, user: User, lines: list[ReceiptLine]
) -> tuple[str, list[ActionLine]]:
    scope = resolve_scope(db, user, None)
    results: list[ActionLine] = []

    for line in lines:
        cat = infer_category(line.name, line.category)
        is_food = line.is_food if line.is_food is not None else is_food_category(cat)
        if not is_food:
            cat = infer_category(line.name, "дом_и_химия")

        results.append(_add_to_pantry(db, user, scope, line.name, cat))
        if _mark_shopping_bought(db, user, scope, line.name):
            results[-1] = ActionLine(
                emoji=results[-1].emoji,
                name=f"{line.name} (куплено)",
                destination="запасы",
            )

    if not results:
        return ("На чеке не нашёл товары.", [])

    body = "Готово по чеку:\n" + "\n".join(
        f"{r.emoji} {r.name} — {r.destination}" for r in results
    )
    return body, results


def format_action_reply(text: str) -> str:
    return text
