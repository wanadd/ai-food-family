"""Receipt OCR via OpenAI vision (optional)."""

from __future__ import annotations

import base64
import json
import logging
from dataclasses import dataclass

import httpx

from app.config import settings

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
    if not settings.openai_api_key or not image_bytes:
        return [], False

    b64 = base64.standard_b64encode(image_bytes).decode("ascii")
    prompt = (
        "Это фото чека из магазина. Извлеки список товаров. "
        "Ответь ТОЛЬКО JSON: {\"items\": [{\"name\": \"...\", \"quantity\": \"1\", "
        "\"price\": \"99.90\", \"category\": \"молочное\", \"is_food\": true}]}. "
        "name на русском, category — короткий slug из: продукты, овощи, молочное, "
        "мясо, дом_и_химия, питомцы, другое. is_food false для бытовой химии."
    )

    payload = {
        "model": settings.openai_model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{b64}",
                        },
                    },
                ],
            }
        ],
        "response_format": {"type": "json_object"},
        "max_tokens": 1200,
    }

    headers = {
        "Authorization": f"Bearer {settings.openai_api_key}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=90.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            body = response.json()
        content = body["choices"][0]["message"]["content"]
        data = json.loads(content)
        lines: list[ReceiptLine] = []
        for item in data.get("items", []):
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
        return lines, True
    except Exception:
        logger.exception("Receipt OCR failed")
        return [], False
