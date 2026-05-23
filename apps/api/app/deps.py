from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.user import User
from app.services.app_scope import AppScope, resolve_scope
from app.services.dev_auth import (
    dev_auth_enabled,
    get_or_create_dev_user,
    is_dev_init_data,
)
from app.services.users import (
    PHONE_REQUIRED_MESSAGE,
    get_or_create_user,
    user_has_verified_phone,
)
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

    if is_dev_init_data(x_telegram_init_data):
        if not dev_auth_enabled():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Dev auth is disabled",
            )
        user, _ = get_or_create_dev_user(db)
        return user

    try:
        telegram_user = validate_init_data(x_telegram_init_data, settings.telegram_bot_token)
    except TelegramAuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc

    user, _ = get_or_create_user(db, telegram_user)
    return user


def get_verified_user(user: User = Depends(get_current_user)) -> User:
    if not user_has_verified_phone(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=PHONE_REQUIRED_MESSAGE,
        )
    return user


def get_app_scope(
    x_app_mode: str | None = Header(default=None, alias="X-App-Mode"),
    user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
) -> AppScope:
    return resolve_scope(db, user, x_app_mode)


def is_admin_user(user: User) -> bool:
    admin_ids = settings.admin_telegram_id_set()
    return bool(admin_ids) and user.telegram_id in admin_ids


def require_admin_user(user: User = Depends(get_current_user)) -> User:
    if not is_admin_user(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ только для администратора проекта",
        )
    return user
