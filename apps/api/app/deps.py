from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.user import User
from app.services.app_scope import AppScope, resolve_scope
from app.services.users import get_or_create_user
from app.telegram.validate import TelegramAuthError, validate_init_data


def get_current_user(
    x_telegram_init_data: str | None = Header(default=None, alias="X-Telegram-Init-Data"),
    db: Session = Depends(get_db),
) -> User:
    if not x_telegram_init_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-Telegram-Init-Data header is required",
        )

    try:
        telegram_user = validate_init_data(x_telegram_init_data, settings.telegram_bot_token)
    except TelegramAuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc

    user, _ = get_or_create_user(db, telegram_user)
    return user


def get_app_scope(
    x_app_mode: str | None = Header(default=None, alias="X-App-Mode"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AppScope:
    return resolve_scope(db, user, x_app_mode)
