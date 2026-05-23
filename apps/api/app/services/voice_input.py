"""Voice transcription for Telegram bot (OpenAI Whisper via ai service)."""

from __future__ import annotations

import logging

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.user import User
from app.services import subscription as subscription_service
from app.services.ai import transcribe_voice
from app.services.ai_errors import AiError, AiUnavailableError, MSG_AI_UNAVAILABLE
from app.services.ai_client import is_ai_configured, current_model_name
from app.services.app_scope import resolve_scope
from app.services.subscription_catalog import AMA_COSTS

logger = logging.getLogger(__name__)

VOICE_STUB = (
    "Голосовые команды скоро будут доступны. Сейчас можно написать текстом."
)


async def transcribe_for_user(
    db: Session, user: User, audio_bytes: bytes
) -> tuple[str | None, str | None]:
    """
    Returns (text, error_message).
    error_message set when ams insufficient or AI unavailable.
    """
    scope = resolve_scope(db, user, None)
    if not is_ai_configured():
        return None, MSG_AI_UNAVAILABLE

    try:
        text = await transcribe_voice(audio_bytes)
    except AiUnavailableError:
        return None, MSG_AI_UNAVAILABLE
    except AiError:
        logger.exception("Voice transcription failed")
        return None, "ПланАм временно не смог обработать запрос. Попробуйте ещё раз."

    if not text:
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
