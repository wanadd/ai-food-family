"""User-safe AI errors (no secrets in messages)."""

from __future__ import annotations

MSG_AI_UNAVAILABLE = "AI-функции временно недоступны."
MSG_AI_FAILED = "ПланАм временно не смог обработать запрос. Попробуйте ещё раз."


class AiError(Exception):
    """Base AI service error."""

    user_message: str = MSG_AI_FAILED

    def __init__(self, message: str | None = None, *, user_message: str | None = None):
        super().__init__(message or self.user_message)
        if user_message:
            self.user_message = user_message


class AiUnavailableError(AiError):
    user_message = MSG_AI_UNAVAILABLE


class AiResponseError(AiError):
    user_message = MSG_AI_FAILED
