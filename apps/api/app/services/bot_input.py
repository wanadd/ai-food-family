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
from app.services import pantry as pantry_service
from app.services import shopping_list as shopping_service
from app.services.shopping_category_service import resolve_category_for_item
from app.services.app_scope import AppScope, resolve_scope
from app.services.message_parser import ParsedMessage, parse_message
from app.services.receipt_ocr import ReceiptLine
from app.services.shopping_categories import infer_category, is_food_category
from app.services.ai import parse_shopping_text
from app.services.ai_context import build_ai_user_context
from app.services.ai_client import is_ai_configured, current_model_name
from app.services.ai_errors import AiError, AiUnavailableError, MSG_AI_UNAVAILABLE
from app.services import subscription as subscription_service
from app.services.subscription_catalog import AMA_COSTS

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

INTENT_TO_ACTION = {
    "add_to_pantry": "pantry_add",
    "add_to_shopping": "shopping_add",
    "add_leftover": "leftover_note",
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


def _parsed_from_ai(bot_result) -> ParsedMessage | None:
    from app.services.ai import BotParseResult

    if not isinstance(bot_result, BotParseResult):
        return None
    action = INTENT_TO_ACTION.get(bot_result.intent)
    if bot_result.intent in ("ask_nutritionist", "generate_menu", "show_summary"):
        return ParsedMessage(action="unknown", raw_text=bot_result.raw_text)
    if bot_result.intent == "unknown" and not bot_result.items:
        return None
    if action == "leftover_note" and bot_result.leftover:
        dish = bot_result.leftover.get("dish_name", "")
        portions = bot_result.leftover.get("portions", "")
        note = f"{dish} {portions} порции".strip()
        return ParsedMessage(action="leftover_note", leftover_note=note, raw_text=bot_result.raw_text)
    items = [row["name"] for row in bot_result.items if row.get("name")]
    if not items and action != "leftover_note":
        return None
    return ParsedMessage(action=action or "unknown", items=items, raw_text=bot_result.raw_text)


async def _parse_with_ai(db: Session, user: User, scope: AppScope, text: str) -> ParsedMessage | None:
    if not is_ai_configured():
        return None
    try:
        subscription_service.require_ai_action(
            db,
            user,
            scope,
            "bot_parse_text",
            ama_cost=AMA_COSTS["bot_parse_text"],
        )
        ai_ctx = build_ai_user_context(db, user, scope)
        bot_result = await parse_shopping_text(text, ai_ctx)
        subscription_service.log_ai_usage(
            db,
            user_id=user.id,
            family_id=scope.family_id,
            action_type="bot_parse_text",
            ams_spent=AMA_COSTS["bot_parse_text"],
            model=current_model_name(),
        )
        return _parsed_from_ai(bot_result)
    except HTTPException:
        raise
    except (AiUnavailableError, AiError):
        logger.exception("Bot AI parse failed")
        return None


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
    from app.schemas.meal_leftover import MealLeftoverCreate
    from app.services import meal_leftovers as meal_leftovers_service

    dish = note[:200]
    portions = 1
    m = re.search(r"(\d+)\s*порц", note.lower())
    if m:
        portions = int(m.group(1))
    meal_leftovers_service.create_leftover(
        db,
        user,
        scope,
        MealLeftoverCreate(dish_name=dish, portions_remaining=portions),
    )
    return ActionLine(emoji="🍲", name=dish[:60], destination="остатки")


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


async def process_text_message(
    db: Session, user: User, text: str
) -> tuple[str, list[ActionLine]]:
    scope = resolve_scope(db, user, None)
    parsed = parse_message(text)

    if parsed.action == "unknown":
        ai_parsed = await _parse_with_ai(db, user, scope, text)
        if ai_parsed:
            parsed = ai_parsed

    if parsed.action == "unknown":
        if not is_ai_configured():
            hint = MSG_AI_UNAVAILABLE
        else:
            hint = (
                "Не понял команду. Примеры:\n"
                "• Купил молоко и яйца\n"
                "• Добавь порошок и мешки\n"
                "• Закончилась гречка\n"
                "• Осталось 4 порции борща"
            )
        return (hint, [])

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
