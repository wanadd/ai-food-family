"""Receipt OCR via OpenAI vision (centralized ai service)."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from app.services.ai import parse_receipt_text_or_image
from app.services.ai_client import is_ai_configured
from app.services.ai_errors import AiError, AiUnavailableError

logger = logging.getLogger(__name__)

RECEIPT_STUB_MESSAGE = (
    "Чеки скоро будут распознаваться автоматически. "
    "Пока добавьте товары текстом, например: «Купил молоко и яйца»."
)


@dataclass
class ReceiptLine:
    name: str
    quantity: str
    price: str | None
    category: str | None
    is_food: bool | None


async def parse_receipt_image(image_bytes: bytes) -> tuple[list[ReceiptLine], bool]:
    """
    Returns (lines, used_ai).
    Empty list + used_ai=False when AI unavailable.
    """
    if not is_ai_configured() or not image_bytes:
        return [], False

    try:
        items = await parse_receipt_text_or_image(image_bytes=image_bytes)
    except (AiUnavailableError, AiError):
        logger.exception("Receipt OCR failed")
        return [], False

    lines: list[ReceiptLine] = []
    for item in items:
        name = (item.get("name") or "").strip()
        if not name:
            continue
        lines.append(
            ReceiptLine(
                name=name,
                quantity=str(item.get("quantity") or "1"),
                price=str(item.get("price")) if item.get("price") else None,
                category=item.get("category"),
                is_food=item.get("is_food"),
            )
        )
    return lines, bool(lines)
