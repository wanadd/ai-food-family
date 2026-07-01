"""Guards for proactive care / reminder notifications."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.care import CareSettings
from app.models.notification_settings import UserNotificationSettings
from app.models.user import User
from app.services.menu_selection import get_selected_menu
from app.services.notifications import get_or_create_settings
from app.services.onboarding import get_or_create_profile
from app.services.app_scope import resolve_scope

PROACTIVE_CARE_SEMANTIC_KEYS: dict[str, str] = {
    "water": "water_reminder",
    "protein": "protein_reminder",
    "menu": "menu_reminder",
    "shopping": "shopping_reminder",
    "pantry": "pantry_update_nudge",
    "progress": "progress_reminder",
    "family": "family_reminder",
}
PANTRY_SEMANTIC_KEY = PROACTIVE_CARE_SEMANTIC_KEYS["pantry"]
PROACTIVE_CARE_DEDUP_HOURS: dict[str, int] = {
    "water_reminder": 2,
    "protein_reminder": 6,
    "menu_reminder": 24,
    "shopping_reminder": 24,
    "pantry_update_nudge": 24,
    "progress_reminder": 24,
    "family_reminder": 24,
}
DEDUP_STATUSES = ("pending", "sending", "sent", "failed")

TYPE_TO_CARE_FLAG: dict[str, str] = {
    "water": "water_enabled",
    "protein": "protein_enabled",
    "menu": "menu_enabled",
    "shopping": "shopping_enabled",
    "pantry": "pantry_enabled",
    "progress": "progress_enabled",
    "family": "family_enabled",
    "pro": "pro_enabled",
}
TYPE_TO_ENABLED_ALIASES: dict[str, set[str]] = {
    "protein": {"protein", "health"},
}


def _care_settings_row(db: Session, user: User) -> CareSettings | None:
    from app.models.care import CareSettings

    return (
        db.query(CareSettings).filter(CareSettings.user_id == user.id).one_or_none()
    )


def notifications_onboarded(db: Session, user: User) -> bool:
    row = get_or_create_settings(db, user)
    return bool(getattr(row, "notifications_onboarded", False))


def care_mode(db: Session, user: User) -> str:
    row = get_or_create_settings(db, user)
    return getattr(row, "care_mode", "off") or "off"


def _enabled_types(row: UserNotificationSettings) -> set[str]:
    raw = getattr(row, "enabled_notification_types", None) or []
    if isinstance(raw, list):
        return {str(x) for x in raw}
    return set()


def semantic_key_for_type(notification_type: str) -> str | None:
    return PROACTIVE_CARE_SEMANTIC_KEYS.get(notification_type)


def dedup_hours_for_semantic_key(semantic_key: str | None) -> int:
    if semantic_key is None:
        return 24
    return PROACTIVE_CARE_DEDUP_HOURS.get(semantic_key, 24)


def _type_explicitly_enabled(
    notif: UserNotificationSettings, care: CareSettings | None, notification_type: str
) -> bool:
    enabled = _enabled_types(notif)
    enabled_aliases = TYPE_TO_ENABLED_ALIASES.get(notification_type, {notification_type})
    if enabled.isdisjoint(enabled_aliases):
        return False
    flag = TYPE_TO_CARE_FLAG.get(notification_type)
    if not flag:
        return False
    if care is None:
        return False
    return bool(getattr(care, flag, False))


def user_has_menu(db: Session, user: User) -> bool:
    scope = resolve_scope(db, user, None)
    return get_selected_menu(db, scope) is not None


def user_profile_completed(db: Session, user: User) -> bool:
    profile = get_or_create_profile(db, user)
    return bool(profile.completed)


def can_send_care_notification(
    db: Session,
    user: User,
    notification_type: str,
    *,
    semantic_key: str | None = None,
    require_menu: bool | None = None,
) -> bool:
    """Return True if proactive care of this type may be created/sent."""
    notif = get_or_create_settings(db, user)

    if not getattr(notif, "notifications_onboarded", False):
        return False

    mode = getattr(notif, "care_mode", "off") or "off"
    if mode == "off":
        return False

    care = _care_settings_row(db, user)
    if not _type_explicitly_enabled(notif, care, notification_type):
        return False

    if care and not getattr(care, TYPE_TO_CARE_FLAG.get(notification_type, ""), False):
        return False

    if notification_type in ("menu", "shopping", "pantry", "progress", "family"):
        if not user_profile_completed(db, user):
            return False

    needs_menu = require_menu
    if needs_menu is None:
        needs_menu = notification_type in ("menu", "shopping", "pantry")

    if needs_menu and not user_has_menu(db, user):
        if notification_type == "pantry":
            from app.services import pantry as pantry_service

            scope = resolve_scope(db, user, None)
            pantry = pantry_service.list_pantry(db, user, scope)
            if pantry.active_count <= 0:
                return False
        else:
            return False

    sk = semantic_key or semantic_key_for_type(notification_type)
    if sk:
        if _recent_duplicate(db, user, notification_type, sk):
            return False

    return True


def can_send_scheduled_reminder(db: Session, user: User) -> bool:
    """Buy/cook schedule reminders require onboarding + non-off care mode."""
    notif = get_or_create_settings(db, user)
    if not getattr(notif, "notifications_onboarded", False):
        return False
    if (getattr(notif, "care_mode", "off") or "off") == "off":
        return False
    return True


def _recent_duplicate(
    db: Session,
    user: User,
    notification_type: str,
    semantic_key: str,
) -> bool:
    from app.models.care import CareNotification

    since = datetime.now(timezone.utc) - timedelta(
        hours=dedup_hours_for_semantic_key(semantic_key)
    )
    q = (
        db.query(CareNotification)
        .filter(
            CareNotification.user_id == user.id,
            CareNotification.type == notification_type,
            CareNotification.status.in_(DEDUP_STATUSES),
            CareNotification.created_at >= since,
        )
    )
    if hasattr(CareNotification, "semantic_key"):
        q = q.filter(CareNotification.semantic_key == semantic_key)
    return q.first() is not None
