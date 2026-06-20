"""Low-level OpenAI client (key only on backend, never logged)."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from app.config import settings
from app.services.ai_errors import AiResponseError, AiUnavailableError

logger = logging.getLogger(__name__)

_client: Any | None = None
_init_attempted = False


def _effective_model() -> str:
    model = (settings.openai_model or "").strip()
    return model or "gpt-4o-mini"


def is_ai_configured() -> bool:
    return bool((settings.openai_api_key or "").strip())


def get_openai_client() -> Any | None:
    """Lazy AsyncOpenAI instance; None if no API key."""
    global _client, _init_attempted
    if _init_attempted:
        return _client
    _init_attempted = True
    if not is_ai_configured():
        return None
    try:
        from openai import AsyncOpenAI

        _client = AsyncOpenAI(api_key=settings.openai_api_key.strip())
    except Exception:
        logger.exception("Failed to initialize OpenAI client")
        _client = None
    return _client


def _strip_json_fence(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return text.strip()


async def chat_text(
    *,
    system: str,
    user: str,
    temperature: float = 0.6,
    max_tokens: int | None = 1024,
) -> str:
    client = get_openai_client()
    if client is None:
        raise AiUnavailableError()

    try:
        response = await client.chat.completions.create(
            model=_effective_model(),
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        content = response.choices[0].message.content
        if not content:
            raise AiResponseError("Empty model response")
        return content.strip()
    except AiUnavailableError:
        raise
    except Exception as exc:
        logger.warning("OpenAI chat failed: %s", type(exc).__name__)
        raise AiResponseError() from exc


async def chat_json(
    *,
    system: str,
    user: str,
    temperature: float = 0.5,
    max_tokens: int | None = 4096,
    retries: int = 1,
    model: str | None = None,
) -> dict[str, Any]:
    client = get_openai_client()
    if client is None:
        raise AiUnavailableError()

    effective_model = (model or "").strip() or _effective_model()
    prompt = user
    last_error: Exception | None = None

    for attempt in range(retries + 1):
        try:
            response = await client.chat.completions.create(
                model=effective_model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                response_format={"type": "json_object"},
            )
            raw = response.choices[0].message.content or ""
            raw = _strip_json_fence(raw)
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            last_error = exc
            logger.warning("OpenAI JSON parse failed (attempt %s)", attempt + 1)
            prompt = (
                f"{user}\n\nВажно: ответь ТОЛЬКО одним валидным JSON-объектом, "
                "без markdown и пояснений."
            )
        except AiUnavailableError:
            raise
        except Exception as exc:
            logger.warning("OpenAI chat_json failed: %s", type(exc).__name__)
            raise AiResponseError() from exc

    raise AiResponseError("Invalid JSON from model") from last_error


async def transcribe_audio(
    audio_bytes: bytes,
    *,
    filename: str = "voice.ogg",
    mime: str = "audio/ogg",
) -> str:
    client = get_openai_client()
    if client is None or not audio_bytes:
        raise AiUnavailableError()

    try:
        import io

        file_obj = io.BytesIO(audio_bytes)
        file_obj.name = filename
        response = await client.audio.transcriptions.create(
            model="whisper-1",
            file=file_obj,
            language="ru",
        )
        text = (response.text or "").strip()
        if not text:
            raise AiResponseError("Empty transcription")
        return text
    except AiUnavailableError:
        raise
    except Exception as exc:
        logger.warning("OpenAI transcription failed: %s", type(exc).__name__)
        raise AiResponseError() from exc


async def vision_json(
    *,
    prompt: str,
    image_bytes: bytes,
    mime: str = "image/jpeg",
    max_tokens: int = 1200,
) -> dict[str, Any]:
    import base64

    client = get_openai_client()
    if client is None or not image_bytes:
        raise AiUnavailableError()

    b64 = base64.standard_b64encode(image_bytes).decode("ascii")
    data_url = f"data:{mime};base64,{b64}"

    system = (
        "Ты помощник приложения ПланАм. Отвечай только валидным JSON на русском."
    )
    try:
        response = await client.chat.completions.create(
            model=_effective_model(),
            messages=[
                {"role": "system", "content": system},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": data_url}},
                    ],
                },
            ],
            response_format={"type": "json_object"},
            max_tokens=max_tokens,
        )
        raw = _strip_json_fence(response.choices[0].message.content or "")
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        logger.warning("OpenAI vision JSON invalid")
        raise AiResponseError() from exc
    except AiUnavailableError:
        raise
    except Exception as exc:
        logger.warning("OpenAI vision failed: %s", type(exc).__name__)
        raise AiResponseError() from exc


def current_model_name() -> str | None:
    return _effective_model() if is_ai_configured() else None
