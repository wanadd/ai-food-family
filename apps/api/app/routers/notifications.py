from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_verified_user
from app.models.user import User
from app.schemas.notifications import (
    NotificationSettingsResponse,
    NotificationSettingsUpdate,
)
from app.services import notifications as notifications_service

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/settings", response_model=NotificationSettingsResponse)
def get_notification_settings(
    user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
) -> NotificationSettingsResponse:
    return notifications_service.get_settings(db, user)


@router.put("/settings", response_model=NotificationSettingsResponse)
def update_notification_settings(
    payload: NotificationSettingsUpdate,
    user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
) -> NotificationSettingsResponse:
    return notifications_service.update_settings(db, user, payload)
