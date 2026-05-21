from sqlalchemy.orm import Session

from app.models.notification_settings import UserNotificationSettings
from app.models.user import User
from app.schemas.notifications import (
    NotificationSettingsResponse,
    NotificationSettingsUpdate,
)


def get_or_create_settings(db: Session, user: User) -> UserNotificationSettings:
    settings_row = (
        db.query(UserNotificationSettings)
        .filter(UserNotificationSettings.user_id == user.id)
        .one_or_none()
    )
    if settings_row is None:
        settings_row = UserNotificationSettings(user_id=user.id)
        db.add(settings_row)
        db.commit()
        db.refresh(settings_row)
    return settings_row


def get_settings(db: Session, user: User) -> NotificationSettingsResponse:
    row = get_or_create_settings(db, user)
    return _to_response(row)


def update_settings(
    db: Session, user: User, payload: NotificationSettingsUpdate
) -> NotificationSettingsResponse:
    row = get_or_create_settings(db, user)

    if payload.buy_reminder_enabled is not None:
        row.buy_reminder_enabled = payload.buy_reminder_enabled
    if payload.cook_reminder_enabled is not None:
        row.cook_reminder_enabled = payload.cook_reminder_enabled
    if payload.buy_reminder_time is not None:
        row.buy_reminder_time = payload.buy_reminder_time
    if payload.cook_reminder_time is not None:
        row.cook_reminder_time = payload.cook_reminder_time
    if payload.timezone is not None:
        row.timezone = payload.timezone

    db.commit()
    db.refresh(row)
    return _to_response(row)


def _to_response(row: UserNotificationSettings) -> NotificationSettingsResponse:
    return NotificationSettingsResponse(
        buy_reminder_enabled=row.buy_reminder_enabled,
        cook_reminder_enabled=row.cook_reminder_enabled,
        buy_reminder_time=row.buy_reminder_time,
        cook_reminder_time=row.cook_reminder_time,
        timezone=row.timezone,
        updated_at=row.updated_at,
    )
