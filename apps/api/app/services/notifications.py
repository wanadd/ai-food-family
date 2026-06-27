from sqlalchemy.orm import Session

from app.models.care import CareSettings
from app.models.notification_settings import UserNotificationSettings
from app.models.user import User
from app.schemas.notifications import (
    NotificationOnboardingRequest,
    NotificationSettingsResponse,
    NotificationSettingsUpdate,
)
from app.services.normalization.notifications import normalize_time, normalize_timezone

CARE_MODE_TO_LEVEL: dict[str, str] = {
    "off": "off",
    "minimal": "minimal",
    "normal": "standard",
    "active": "active",
}

TYPE_TO_FLAGS: dict[str, tuple[str, str]] = {
    "menu": ("cook_reminder_enabled", "menu_enabled"),
    "shopping": ("buy_reminder_enabled", "shopping_enabled"),
    "pantry": ("buy_reminder_enabled", "pantry_enabled"),
    "water": ("cook_reminder_enabled", "water_enabled"),
    "health": ("cook_reminder_enabled", "protein_enabled"),
    "family": ("cook_reminder_enabled", "family_enabled"),
}


def _default_settings_row(user_id: int) -> UserNotificationSettings:
    return UserNotificationSettings(
        user_id=user_id,
        notifications_onboarded=False,
        care_mode="off",
        enabled_notification_types=[],
        buy_reminder_enabled=False,
        cook_reminder_enabled=False,
        cook_breakfast_enabled=False,
        cook_lunch_enabled=False,
        cook_dinner_enabled=False,
        timezone="Europe/Moscow",
    )


def get_or_create_settings(db: Session, user: User) -> UserNotificationSettings:
    settings_row = (
        db.query(UserNotificationSettings)
        .filter(UserNotificationSettings.user_id == user.id)
        .one_or_none()
    )
    if settings_row is None:
        settings_row = _default_settings_row(user.id)
        db.add(settings_row)
        db.commit()
        db.refresh(settings_row)
    return settings_row


def get_settings(db: Session, user: User) -> NotificationSettingsResponse:
    row = get_or_create_settings(db, user)
    return _to_response(row)


def _sync_care_settings(db: Session, user: User, row: UserNotificationSettings) -> None:
    care = (
        db.query(CareSettings).filter(CareSettings.user_id == user.id).one_or_none()
    )
    if care is None:
        care = CareSettings(
            user_id=user.id,
            timezone=row.timezone,
            care_level=CARE_MODE_TO_LEVEL.get(row.care_mode, "off"),
            quiet_hours_start="22:00",
            quiet_hours_end="09:00",
        )
        db.add(care)

    care.care_level = CARE_MODE_TO_LEVEL.get(row.care_mode, "off")
    care.timezone = row.timezone
    care.menu_enabled = "menu" in (row.enabled_notification_types or [])
    care.shopping_enabled = "shopping" in (row.enabled_notification_types or [])
    care.pantry_enabled = "pantry" in (row.enabled_notification_types or [])
    care.water_enabled = "water" in (row.enabled_notification_types or [])
    care.protein_enabled = "health" in (row.enabled_notification_types or [])
    care.family_enabled = "family" in (row.enabled_notification_types or [])
    care.progress_enabled = False
    care.pro_enabled = False

    if row.care_mode == "off":
        care.menu_enabled = False
        care.shopping_enabled = False
        care.pantry_enabled = False
        care.water_enabled = False
        care.protein_enabled = False
        care.family_enabled = False


def apply_onboarding(
    db: Session, user: User, payload: NotificationOnboardingRequest
) -> NotificationSettingsResponse:
    row = get_or_create_settings(db, user)
    row.notifications_onboarded = True
    row.care_mode = payload.care_mode
    row.enabled_notification_types = list(payload.enabled_notification_types or [])

    row.buy_reminder_enabled = False
    row.cook_reminder_enabled = False
    row.cook_breakfast_enabled = False
    row.cook_lunch_enabled = False
    row.cook_dinner_enabled = False

    if payload.care_mode != "off":
        types = set(row.enabled_notification_types or [])
        row.buy_reminder_enabled = "shopping" in types or "pantry" in types
        row.cook_reminder_enabled = (
            "menu" in types or "water" in types or "health" in types or "family" in types
        )
        row.cook_breakfast_enabled = "menu" in types
        row.cook_lunch_enabled = "menu" in types
        row.cook_dinner_enabled = "menu" in types

    if payload.quiet_hours_start:
        row_quiet_start = payload.quiet_hours_start
    else:
        row_quiet_start = "22:00"
    if payload.quiet_hours_end:
        row_quiet_end = payload.quiet_hours_end
    else:
        row_quiet_end = "09:00"

    if payload.timezone:
        row.timezone = normalize_timezone(payload.timezone)

    _sync_care_settings(db, user, row)
    care = db.query(CareSettings).filter(CareSettings.user_id == user.id).one()
    care.quiet_hours_start = row_quiet_start
    care.quiet_hours_end = row_quiet_end

    db.commit()
    db.refresh(row)
    return _to_response(row)


def update_settings(
    db: Session, user: User, payload: NotificationSettingsUpdate
) -> NotificationSettingsResponse:
    row = get_or_create_settings(db, user)

    if payload.buy_reminder_enabled is not None:
        row.buy_reminder_enabled = payload.buy_reminder_enabled
    if payload.cook_breakfast_enabled is not None:
        row.cook_breakfast_enabled = payload.cook_breakfast_enabled
    if payload.cook_lunch_enabled is not None:
        row.cook_lunch_enabled = payload.cook_lunch_enabled
    if payload.cook_dinner_enabled is not None:
        row.cook_dinner_enabled = payload.cook_dinner_enabled
    if payload.cook_reminder_enabled is not None:
        row.cook_reminder_enabled = payload.cook_reminder_enabled
        if not payload.cook_reminder_enabled:
            row.cook_breakfast_enabled = False
            row.cook_lunch_enabled = False
            row.cook_dinner_enabled = False
    if payload.buy_reminder_time is not None:
        row.buy_reminder_time = normalize_time(
            payload.buy_reminder_time, row.buy_reminder_time
        )
    if payload.cook_reminder_time is not None:
        row.cook_reminder_time = normalize_time(
            payload.cook_reminder_time, row.cook_reminder_time
        )
    if payload.cook_breakfast_time is not None:
        row.cook_breakfast_time = normalize_time(
            payload.cook_breakfast_time, row.cook_breakfast_time
        )
    if payload.cook_lunch_time is not None:
        row.cook_lunch_time = normalize_time(
            payload.cook_lunch_time, row.cook_lunch_time
        )
    if payload.cook_dinner_time is not None:
        row.cook_dinner_time = normalize_time(
            payload.cook_dinner_time, row.cook_dinner_time
        )
    if payload.timezone is not None:
        row.timezone = normalize_timezone(payload.timezone)

    row.cook_reminder_enabled = (
        row.cook_breakfast_enabled
        or row.cook_lunch_enabled
        or row.cook_dinner_enabled
    )

    db.commit()
    db.refresh(row)
    return _to_response(row)


def _to_response(row: UserNotificationSettings) -> NotificationSettingsResponse:
    return NotificationSettingsResponse(
        notifications_onboarded=bool(getattr(row, "notifications_onboarded", False)),
        care_mode=getattr(row, "care_mode", "off") or "off",
        enabled_notification_types=list(
            getattr(row, "enabled_notification_types", None) or []
        ),
        buy_reminder_enabled=row.buy_reminder_enabled,
        cook_reminder_enabled=row.cook_reminder_enabled,
        cook_breakfast_enabled=row.cook_breakfast_enabled,
        cook_lunch_enabled=row.cook_lunch_enabled,
        cook_dinner_enabled=row.cook_dinner_enabled,
        buy_reminder_time=row.buy_reminder_time,
        cook_reminder_time=row.cook_reminder_time,
        cook_breakfast_time=row.cook_breakfast_time,
        cook_lunch_time=row.cook_lunch_time,
        cook_dinner_time=row.cook_dinner_time,
        timezone=row.timezone,
        updated_at=row.updated_at,
    )
