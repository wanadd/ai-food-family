from fastapi import Depends, Header, HTTPException, Request, status
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
from app.services.admin_auth import require_valid_session, validate_admin_session_token
from app.services.users import (
    PHONE_REQUIRED_MESSAGE,
    get_or_create_user,
    user_has_verified_phone,
)
from app.telegram.validate import TelegramAuthError, validate_init_data


def get_current_user(
    request: Request,
    x_telegram_init_data: str | None = Header(default=None, alias="X-Telegram-Init-Data"),
    x_planam_audit_persona: str | None = Header(
        default=None, alias="X-Planam-Audit-Persona"
    ),
    x_planam_audit_user: str | None = Header(default=None, alias="X-Planam-Audit-User"),
    x_planam_audit_secret: str | None = Header(
        default=None, alias="X-Planam-Audit-Secret"
    ),
    db: Session = Depends(get_db),
) -> User:
    from app.services.audit_auth import get_audit_user_from_request, is_audit_init_data

    audit_user = get_audit_user_from_request(
        db,
        init_data=x_telegram_init_data,
        header_persona=x_planam_audit_persona,
        header_user=x_planam_audit_user,
        header_secret=x_planam_audit_secret,
        path=str(request.url.path),
        origin=request.headers.get("origin"),
    )
    if audit_user is not None:
        return audit_user

    if is_audit_init_data(x_telegram_init_data):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Audit auth is disabled",
        )

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
        if getattr(user, "is_deleted", False) or getattr(user, "is_blocked", False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Аккаунт ограничен. Напишите в поддержку.",
            )
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
            detail="Аккаунт архивирован. Обратитесь в поддержку для восстановления.",
        )
    if getattr(user, "is_blocked", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Аккаунт ограничен. Напишите в поддержку.",
        )
    return user


def get_verified_user(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> User:
    if getattr(user, "is_blocked", False) or getattr(user, "is_deleted", False):
        detail = (
            "Аккаунт архивирован. Обратитесь в поддержку для восстановления."
            if getattr(user, "is_deleted", False)
            else "Аккаунт ограничен. Напишите в поддержку."
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
        )
    from app.services import family as family_service

    membership = family_service.get_user_membership(db, user)
    if membership:
        family = membership.family
        if family and getattr(family, "is_blocked", False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Аккаунт ограничен. Напишите в поддержку.",
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
    x_telegram_init_data: str | None = Header(
        default=None, alias="X-Telegram-Init-Data"
    ),
    x_admin_session: str | None = Header(default=None, alias="X-Admin-Session"),
    db: Session = Depends(get_db),
) -> User:
    if not settings.admin_panel_enabled_flag:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    if x_admin_session:
        session = validate_admin_session_token(db, x_admin_session)
        if session is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        user = db.query(User).filter(User.id == session.user_id).one_or_none()
        if user is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        return user

    user = get_current_user(x_telegram_init_data=x_telegram_init_data, db=db)
    if not is_admin_user(user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    require_valid_session(db, user, x_admin_session)
    return user
