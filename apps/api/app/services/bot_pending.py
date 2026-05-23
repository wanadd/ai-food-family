"""Pending voice/receipt confirmation in Telegram bot."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.models.user import User
from app.services import bot_input as bot_input_service
from app.services import bot_session as bot_session_service
from app.services.receipt_ocr import ReceiptLine
from app.telegram.messaging import send_telegram_message
from app.services.bot_menu import main_menu_keyboard

CONFIRM_PREFIX = "pending:"
EDIT_PREFIX = "pending_edit:"
CANCEL_CALLBACK = "pending:cancel"


def _format_items(items: list[dict]) -> str:
    lines = ["Найдено:"]
    for item in items:
        name = item.get("name", "?")
        qty = item.get("amount") or item.get("quantity") or ""
        extra = f" ({qty})" if qty else ""
        lines.append(f"• {name}{extra}")
    return "\n".join(lines)


def _confirm_keyboard() -> dict[str, Any]:
    return {
        "inline_keyboard": [
            [
                {"text": "Подтвердить", "callback_data": f"{CONFIRM_PREFIX}ok"},
                {"text": "Исправить", "callback_data": f"{CONFIRM_PREFIX}edit"},
            ],
            [{"text": "Отмена", "callback_data": CANCEL_CALLBACK}],
        ],
    }


async def store_voice_pending(
    db: Session, user: User, chat_id: int, transcript: str, items: list[dict]
) -> None:
    bot_session_service.set_session_state(
        db,
        user.telegram_id,
        bot_session_service.STATE_PENDING_CONFIRM,
        payload={
            "pending": {
                "type": "voice",
                "transcript": transcript,
                "items": items,
            }
        },
    )
    await send_telegram_message(
        chat_id,
        f"Услышал: «{transcript}»\n\n{_format_items(items)}",
        reply_markup=_confirm_keyboard(),
    )


async def store_receipt_pending(
    db: Session,
    user: User,
    chat_id: int,
    receipt_lines: list[ReceiptLine],
) -> None:
    items = [
        {
            "name": line.name,
            "amount": line.quantity,
            "price": line.price,
            "category": line.category,
        }
        for line in receipt_lines
    ]
    total = 0.0
    for line in receipt_lines:
        if line.price:
            try:
                total += float(str(line.price).replace(",", ".").replace(" ", ""))
            except ValueError:
                pass
    bot_session_service.set_session_state(
        db,
        user.telegram_id,
        bot_session_service.STATE_PENDING_CONFIRM,
        payload={"pending": {"type": "receipt", "items": items, "total": total}},
    )
    body = _format_items(items)
    if total:
        body += f"\n\nСумма чека: ~{total:.0f} ₽"
    await send_telegram_message(chat_id, body, reply_markup=_confirm_keyboard())


async def handle_pending_callback(
    db: Session, user: User, chat_id: int, data: str
) -> bool:
    if data == CANCEL_CALLBACK:
        bot_session_service.clear_session_state(db, user.telegram_id)
        await send_telegram_message(
            chat_id, "Отменено.", reply_markup=main_menu_keyboard()
        )
        return True

    if data == f"{CONFIRM_PREFIX}edit":
        bot_session_service.patch_payload(db, user.telegram_id, pending_edit=True)
        await send_telegram_message(
            chat_id,
            "Напишите исправленный список текстом, например:\n"
            "молоко 2 л, яйца 10 шт, творог 2 пачки",
            reply_markup=main_menu_keyboard(),
        )
        return True

    if data != f"{CONFIRM_PREFIX}ok":
        return False

    session = bot_session_service.get_session(db, user.telegram_id)
    payload = bot_session_service.get_payload(session)
    pending = payload.get("pending") or {}
    if not pending:
        bot_session_service.clear_session_state(db, user.telegram_id)
        return True

    ptype = pending.get("type")
    if ptype == "receipt":
        lines = [
            ReceiptLine(
                name=i["name"],
                quantity=i.get("amount") or i.get("quantity") or "1",
                price=i.get("price"),
                category=i.get("category"),
                is_food=True,
            )
            for i in pending.get("items") or []
        ]
        reply, _ = bot_input_service.process_receipt_lines(db, user, lines)
    else:
        transcript = pending.get("transcript") or ""
        reply, _ = bot_input_service.process_text_message(db, user, transcript)

    bot_session_service.clear_session_state(db, user.telegram_id)
    await send_telegram_message(
        chat_id, reply, reply_markup=main_menu_keyboard()
    )
    return True


async def handle_pending_text_edit(
    db: Session, user: User, chat_id: int, text: str
) -> bool:
    session = bot_session_service.get_session(db, user.telegram_id)
    if not session or session.state != bot_session_service.STATE_PENDING_CONFIRM:
        return False
    payload = bot_session_service.get_payload(session)
    if not payload.get("pending_edit"):
        return False
    reply, _ = bot_input_service.process_text_message(db, user, text)
    bot_session_service.clear_session_state(db, user.telegram_id)
    await send_telegram_message(
        chat_id, reply, reply_markup=main_menu_keyboard()
    )
    return True
