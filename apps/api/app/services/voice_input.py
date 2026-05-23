"""Voice transcription for Telegram bot (OpenAI Whisper, optional)."""

from __future__ import annotations

import logging
import tempfile
from pathlib import Path

import httpx
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.models.user import User
from app.services import subscription as subscription_service
from app.services.app_scope import resolve_scope
from app.services.subscription_catalog import AMA_COSTS

logger = logging.getLogger(__name__)

VOICE_STUB = (
    "Голосовые команды скоро будут доступны. Сейчас можно написать текстом."
)


async def transcribe_voice(audio_bytes: bytes, *, mime: str = "audio/ogg") -> tuple[str | None, bool]:
    if not settings.openai_api_key or not audio_bytes:
        return None, False

    suffix = ".ogg" if "ogg" in mime else ".mp3"
    path = Path(tempfile.gettempdir()) / f"planam_voice{suffix}"
    path.write_bytes(audio_bytes)

    headers = {"Authorization": f"Bearer {settings.openai_api_key}"}

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            with path.open("rb") as audio_file:
                response = await client.post(
                    "https://api.openai.com/v1/audio/transcriptions",
                    headers=headers,
                    files={"file": (path.name, audio_file, mime)},
                    data={"model": "whisper-1", "language": "ru"},
                )
            response.raise_for_status()
            data = response.json()
        text = (data.get("text") or "").strip()
        return (text if text else None), True
    except Exception:
        logger.exception("Voice transcription failed")
        return None, False
    finally:
        try:
            path.unlink(missing_ok=True)
        except OSError:
            pass


async def transcribe_for_user(
    db: Session, user: User, audio_bytes: bytes
) -> tuple[str | None, str | None]:
    """
    Returns (text, error_message).
    error_message set when ams insufficient or AI unavailable stub.
    """
    scope = resolve_scope(db, user, None)
    if not settings.openai_api_key:
        return None, VOICE_STUB

    text, used_ai = await transcribe_voice(audio_bytes)
    if not used_ai or not text:
        return None, VOICE_STUB

    try:
        subscription_service.require_ai_action(
            db,
            user,
            scope,
            "voice_command",
            ama_cost=AMA_COSTS["voice_command"],
        )
    except HTTPException as exc:
        if exc.status_code == 402:
            detail = exc.detail
            if isinstance(detail, dict):
                return None, detail.get(
                    "message",
                    "Для этой AI-функции нужны Амы. Пополните баланс или перейдите на тариф выше.",
                )
            return None, str(detail)
        raise

    subscription_service.log_ai_usage(
        db,
        user_id=user.id,
        family_id=scope.family_id,
        action_type="voice_command",
        ams_spent=AMA_COSTS["voice_command"],
        model="whisper-1",
        metadata={"transcript_length": len(text)},
    )
    return text, None
