from __future__ import annotations

from typing import Any

import httpx

from app.config import settings
from app.notifications.delivery import DeliveryResult
from app.telegram.api_urls import telegram_bot_api_url


class TelegramDeliveryAdapter:
    provider = "telegram"

    async def deliver(self, *, destination: str, payload: dict[str, Any]) -> DeliveryResult:
        if not settings.telegram_outbound_allowed or not settings.telegram_bot_token:
            return DeliveryResult(success=False, retryable=False, error_code="provider_disabled")
        request_payload = {"chat_id": destination, "text": str(payload.get("text", ""))}
        if payload.get("reply_markup") is not None:
            request_payload["reply_markup"] = payload["reply_markup"]
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(telegram_bot_api_url("sendMessage"), json=request_payload)
                data = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            return DeliveryResult(success=False, retryable=True, error_code="provider_unavailable", error_message=str(exc))
        if not data.get("ok"):
            error_code = str(data.get("error_code") or "provider_error")
            retryable = int(data.get("error_code") or 0) in {429, 500, 502, 503, 504}
            return DeliveryResult(success=False, retryable=retryable, error_code=error_code, error_message="Telegram delivery failed")
        result = data.get("result") or {}
        return DeliveryResult(success=True, provider_message_id=str(result.get("message_id")) if result.get("message_id") is not None else None, provider_metadata={"provider": "telegram"})
