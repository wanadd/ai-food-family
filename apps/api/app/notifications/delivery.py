from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class DeliveryResult:
    success: bool
    retryable: bool = False
    provider_message_id: str | None = None
    provider_metadata: dict[str, Any] | None = None
    error_code: str | None = None
    error_message: str | None = None


class DeliveryAdapter(Protocol):
    provider: str

    async def deliver(self, *, destination: str, payload: dict[str, Any]) -> DeliveryResult: ...


class DeliveryRouter:
    def __init__(self, adapters: dict[str, DeliveryAdapter]):
        self._adapters = dict(adapters)

    def adapter_for(self, provider: str) -> DeliveryAdapter:
        try:
            return self._adapters[provider]
        except KeyError as exc:
            raise ValueError(f"unsupported notification provider: {provider}") from exc

    async def deliver(self, *, provider: str, destination: str, payload: dict[str, Any]) -> DeliveryResult:
        return await self.adapter_for(provider).deliver(destination=destination, payload=payload)
