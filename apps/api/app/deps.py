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
from app.services.legal_consent import LEGAL_REQUIRED_MESSAGE, user_can_access_app
from app.services.admin_auth import require_valid_session
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
    if getattr(user, "is_deleted", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ временно ограничен",
        )
    if getattr(user, "is_blocked", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ временно ограничен",
        )
    return user


def get_verified_user(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> User:
    if getattr(user, "is_blocked", False) or getattr(user, "is_deleted", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ временно ограничен",
        )
    from app.services import family as family_service

    membership = family_service.get_user_membership(db, user)
    if membership:
        family = membership.family
        if family and getattr(family, "is_blocked", False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Доступ временно ограничен",
            )
    if not user_can_access_app(user):
        from app.services.legal_consent import user_has_legal_consent

        if not user_has_legal_consent(user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=LEGAL_REQUIRED_MESSAGE,
            )
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


def require_admin_user(
    user: User = Depends(get_current_user),
    x_admin_session: str | None = Header(default=None, alias="X-Admin-Session"),
    db: Session = Depends(get_db),
) -> User:
    if not settings.admin_panel_enabled_flag:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    if not is_admin_user(user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    require_valid_session(db, user, x_admin_session)
    return user
