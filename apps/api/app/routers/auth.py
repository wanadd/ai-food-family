from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.schemas.auth import TelegramAuthRequest, TelegramAuthResponse, UserResponse
from app.services.users import get_or_create_user
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
    )
