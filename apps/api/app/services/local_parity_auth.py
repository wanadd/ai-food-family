"""Local prod-parity authentication against a restored snapshot."""

from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.models.user import User

LOCAL_PARITY_INIT_DATA_PREFIX = "planam-local-parity-v1:"


def local_parity_auth_enabled() -> bool:
    return settings.is_local_parity


def local_parity_init_data_for_telegram_id(telegram_id: int) -> str:
    return f"{LOCAL_PARITY_INIT_DATA_PREFIX}{telegram_id}"


def is_local_parity_init_data(init_data: str | None) -> bool:
    return bool(init_data) and init_data.startswith(LOCAL_PARITY_INIT_DATA_PREFIX)


def telegram_id_from_local_parity_init_data(init_data: str) -> int | None:
    if not is_local_parity_init_data(init_data):
        return None
    raw = init_data[len(LOCAL_PARITY_INIT_DATA_PREFIX) :].strip()
    return int(raw) if raw.isdigit() else None


def _configured_telegram_id() -> int:
    if not local_parity_auth_enabled():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Local parity auth is disabled",
        )
    telegram_id = settings.local_parity_telegram_id
    if telegram_id is None or telegram_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="LOCAL_PARITY_TELEGRAM_ID is not configured",
        )
    return telegram_id


def get_local_parity_user(db: Session) -> User:
    telegram_id = _configured_telegram_id()
    user = db.query(User).filter(User.telegram_id == telegram_id).one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configured local parity user was not found in this snapshot",
        )
    if getattr(user, "is_deleted", False) or getattr(user, "is_blocked", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Configured local parity user is blocked or deleted",
        )
    return user


def get_local_parity_user_from_init_data(db: Session, init_data: str | None) -> User | None:
    if not is_local_parity_init_data(init_data):
        return None
    if not local_parity_auth_enabled():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Local parity auth is disabled",
        )
    token_telegram_id = telegram_id_from_local_parity_init_data(init_data or "")
    configured = _configured_telegram_id()
    if token_telegram_id != configured:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Local parity token does not match configured user",
        )
    return get_local_parity_user(db)
