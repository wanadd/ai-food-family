from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.schemas.auth import (
    DevLoginResponse,
    TelegramAuthRequest,
    TelegramAuthResponse,
    UserResponse,
)
from app.services.dev_auth import DEV_INIT_DATA, dev_auth_enabled, get_or_create_dev_user
from app.services.legal_consent import user_can_access_app, user_has_legal_consent
from app.services.users import get_or_create_user, user_has_verified_phone
from app.telegram.validate import TelegramAuthError, validate_init_data

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/telegram", response_model=TelegramAuthResponse)
def authenticate_telegram(
    payload: TelegramAuthRequest,
    db: Session = Depends(get_db),
) -> TelegramAuthResponse:
    try:
        telegram_user = validate_init_data(payload.init_data, settings.telegram_bot_token)
    except TelegramAuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc

    user, is_new = get_or_create_user(db, telegram_user)
    return TelegramAuthResponse(
        user=UserResponse.model_validate(user),
        is_new=is_new,
        phone_verified=user_has_verified_phone(user),
        legal_accepted=user_has_legal_consent(user),
        can_use_app=user_can_access_app(user),
    )


@router.post("/dev-login", response_model=DevLoginResponse)
def authenticate_dev(
    db: Session = Depends(get_db),
) -> DevLoginResponse:
    if not dev_auth_enabled():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Dev auth is only available in development",
        )

    user, is_new = get_or_create_dev_user(db)
    return DevLoginResponse(
        user=UserResponse.model_validate(user),
        is_new=is_new,
        phone_verified=user_has_verified_phone(user),
        legal_accepted=user_has_legal_consent(user),
        can_use_app=user_can_access_app(user),
        dev_init_data=DEV_INIT_DATA,
    )
