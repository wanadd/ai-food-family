from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.config import settings
from app.models.care import CareEvent, CareNotification, CareSettings
from app.models.user import User
from app.schemas.care import (
    CareNotificationResponse,
    CareSettingsResponse,
    CareSettingsUpdate,
    CareTipPreview,
)
from app.services import subscription as subscription_service
from app.services.app_scope import resolve_scope
from app.services.menu_selection import get_selected_menu
from app.services.care_guard import (
    DEDUP_STATUSES,
    PROACTIVE_CARE_SEMANTIC_KEYS,
    can_send_care_notification,
    dedup_hours_for_semantic_key,
    semantic_key_for_type,
)
from app.services.notifications import get_or_create_settings as get_notif_settings_row
from app.services.onboarding import get_or_create_profile
from app.services import pantry as pantry_service
from app.services import shopping_list as shopping_list_service
from app.telegram.messages import send_telegram_message

logger = logging.getLogger(__name__)

CareLevel = str

MINIMAL_TYPES = frozenset({"menu", "shopping", "pantry"})
STANDARD_TYPES = frozenset(
    {"water", "protein", "menu", "shopping", "pantry", "progress", "family"}
)
ACTIVE_TYPES = STANDARD_TYPES | {"pro"}

COOLDOWN_HOURS: dict[str, dict[CareLevel, int]] = {
    "water": {"minimal": 999, "standard": 6, "active": 4},
    "protein": {"minimal": 999, "standard": 12, "active": 8},
    "menu": {"minimal": 24, "standard": 24, "active": 12},
    "shopping": {"minimal": 12, "standard": 12, "active": 8},
    "pantry": {"minimal": 24, "standard": 24, "active": 12},
    "progress": {"minimal": 999, "standard": 24, "active": 12},
    "family": {"minimal": 999, "standard": 12, "active": 8},
    "pro": {"minimal": 999, "standard": 24, "active": 12},
}

CARE_TEMPLATES: dict[str, dict[str, str]] = {
    "water": {
        "title": "💧 ПланАм",
        "message": "Пора выпить стакан воды.",
        "web_app_path": "/profile/nutrition",
        "button_text": "Профиль питания",
    },
    "protein": {
        "title": "🥩 ПланАм",
        "message": "Проверьте белок в рационе. Это важно для вашей цели.",
        "web_app_path": "/nutritionist",
        "button_text": "Нутрициолог",
    },
    "menu": {
        "title": "🍽 ПланАм",
        "message": "Ваш план питания готов. Открыть меню?",
        "web_app_path": "/menu",
        "button_text": "Открыть меню",
    },
    "shopping": {
        "title": "🛒 ПланАм",
        "message": "В списке покупок есть товары. Не забудьте проверить перед магазином.",
        "web_app_path": "/shopping",
        "button_text": "Список покупок",
    },
    "pantry": {
        "title": "📦 ПланАм",
        "message": "Обновите запасы, чтобы следующее меню было точнее.",
        "web_app_path": "/pantry",
        "button_text": "Запасы",
    },
    "progress": {
        "title": "📈 ПланАм",
        "message": "Загляните в прогресс — маленькие шаги складываются в результат.",
        "web_app_path": "/nutritionist",
        "button_text": "Нутрициолог",
    },
    "family": {
        "title": "👨‍👩‍👧 ПланАм",
        "message": "В семье есть обновления — проверьте участников и цели.",
        "web_app_path": "/family",
        "button_text": "Семья",
    },
    "pro": {
        "title": "✨ ПланАм PRO",
        "message": "Персональная рекомендация дня доступна в PRO-режиме.",
        "web_app_path": "/nutritionist",
        "button_text": "Нутрициолог",
    },
}


@dataclass
class CareContext:
    has_menu: bool
    menu_title: str | None
    shopping_unchecked: int
    pantry_count: int
    pantry_expiring: int
    has_nutrition_goal: bool
    nutrition_goal: str | None
    has_family: bool
    is_pro: bool


def _user_timezone(settings_row: CareSettings, user: User, db: Session) -> str:
    if settings_row.timezone:
        return settings_row.timezone
    notif = get_notif_settings_row(db, user)
    return notif.timezone or "Europe/Moscow"


def _now_local(tz_name: str) -> datetime:
    try:
        return datetime.now(ZoneInfo(tz_name))
    except Exception:
        return datetime.now(ZoneInfo("Europe/Moscow"))


def _is_quiet_hours(settings_row: CareSettings, user: User, db: Session) -> bool:
    if not settings_row.quiet_hours_start or not settings_row.quiet_hours_end:
        return False
    now = _now_local(_user_timezone(settings_row, user, db))
    current = now.strftime("%H:%M")
    start = settings_row.quiet_hours_start
    end = settings_row.quiet_hours_end
    if start <= end:
        return start <= current < end
    return current >= start or current < end


def _user_has_pro(db: Session, user: User) -> bool:
    try:
        sub, plan, _, _ = subscription_service.get_current_subscription(db, user)
        if sub.plan_code == "pro":
            return True
        features = plan.features or {}
        return bool(features.get("ai_care"))
    except Exception:
        return False


def get_or_create_care_settings(db: Session, user: User) -> CareSettings:
    row = (
        db.query(CareSettings).filter(CareSettings.user_id == user.id).one_or_none()
    )
    if row is None:
        notif = get_notif_settings_row(db, user)
        row = CareSettings(
            user_id=user.id,
            timezone=notif.timezone or "Europe/Moscow",
            menu_enabled=False,
            shopping_enabled=False,
            pantry_enabled=False,
            care_level="off",
            quiet_hours_start="22:00",
            quiet_hours_end="09:00",
        )
        db.add(row)
        db.commit()
        db.refresh(row)
    return row


def _to_settings_response(
    row: CareSettings, *, has_pro: bool
) -> CareSettingsResponse:
    return CareSettingsResponse(
        water_enabled=row.water_enabled,
        protein_enabled=row.protein_enabled,
        menu_enabled=row.menu_enabled,
        shopping_enabled=row.shopping_enabled,
        pantry_enabled=row.pantry_enabled,
        progress_enabled=row.progress_enabled,
        family_enabled=row.family_enabled,
        pro_enabled=row.pro_enabled,
        care_level=row.care_level,  # type: ignore[arg-type]
        quiet_hours_start=row.quiet_hours_start,
        quiet_hours_end=row.quiet_hours_end,
        timezone=row.timezone,
        has_pro_plan=has_pro,
        updated_at=row.updated_at,
    )


def get_care_settings(db: Session, user: User) -> CareSettingsResponse:
    row = get_or_create_care_settings(db, user)
    return _to_settings_response(row, has_pro=_user_has_pro(db, user))


def update_care_settings(
    db: Session, user: User, payload: CareSettingsUpdate
) -> CareSettingsResponse:
    row = get_or_create_care_settings(db, user)
    data = payload.model_dump(exclude_unset=True)
    previous_level = row.care_level
    for key, value in data.items():
        setattr(row, key, value)

    if data.get("care_level") == "minimal" and previous_level != "minimal":
        row.water_enabled = False
        row.protein_enabled = False
        row.progress_enabled = False
        row.family_enabled = False
        row.pro_enabled = False

    has_pro = _user_has_pro(db, user)
    if row.pro_enabled and not has_pro:
        row.pro_enabled = False

    db.commit()
    db.refresh(row)
    return _to_settings_response(row, has_pro=has_pro)


def list_care_notifications(
    db: Session, user: User, *, limit: int = 20
) -> list[CareNotificationResponse]:
    rows = (
        db.query(CareNotification)
        .filter(CareNotification.user_id == user.id)
        .order_by(desc(CareNotification.created_at))
        .limit(limit)
        .all()
    )
    return [
        CareNotificationResponse(
            id=row.id,
            type=row.type,
            title=row.title,
            message=row.message,
            status=row.status,
            sent_at=row.sent_at,
            created_at=row.created_at,
        )
        for row in rows
    ]


def _type_enabled(settings_row: CareSettings, notification_type: str) -> bool:
    return {
        "water": settings_row.water_enabled,
        "protein": settings_row.protein_enabled,
        "menu": settings_row.menu_enabled,
        "shopping": settings_row.shopping_enabled,
        "pantry": settings_row.pantry_enabled,
        "progress": settings_row.progress_enabled,
        "family": settings_row.family_enabled,
        "pro": settings_row.pro_enabled,
    }.get(notification_type, False)


def _level_allows_type(care_level: str, notification_type: str) -> bool:
    if care_level == "off":
        return False
    if care_level == "minimal":
        return notification_type in MINIMAL_TYPES
    if care_level == "standard":
        return notification_type in STANDARD_TYPES
    return notification_type in ACTIVE_TYPES


def _cooldown_hours(care_level: str, notification_type: str) -> int:
    by_type = COOLDOWN_HOURS.get(notification_type, {})
    return by_type.get(care_level, 24)


def _last_sent_at(
    db: Session, user_id: int, notification_type: str
) -> datetime | None:
    row = (
        db.query(CareNotification)
        .filter(
            CareNotification.user_id == user_id,
            CareNotification.type == notification_type,
            CareNotification.status == "sent",
        )
        .order_by(desc(CareNotification.sent_at))
        .first()
    )
    return row.sent_at if row else None


def should_send_notification(
    db: Session,
    user: User,
    notification_type: str,
    *,
    ignore_quiet_hours: bool = False,
    ignore_cooldown: bool = False,
    semantic_key: str | None = None,
) -> bool:
    sk = semantic_key or semantic_key_for_type(notification_type)
    if not can_send_care_notification(db, user, notification_type, semantic_key=sk):
        return False

    settings_row = get_or_create_care_settings(db, user)

    if not _type_enabled(settings_row, notification_type):
        return False
    if not _level_allows_type(settings_row.care_level, notification_type):
        return False
    if notification_type == "pro" and not _user_has_pro(db, user):
        return False
    if not ignore_quiet_hours and _is_quiet_hours(settings_row, user, db):
        return False

    if not ignore_cooldown:
        last = _last_sent_at(db, user.id, notification_type)
        if last is not None:
            hours = _cooldown_hours(settings_row.care_level, notification_type)
            if datetime.now(timezone.utc) - last < timedelta(hours=hours):
                return False

    return True


def create_care_notification(
    db: Session,
    user: User,
    notification_type: str,
    *,
    title: str | None = None,
    message: str | None = None,
    family_id: int | None = None,
    payload: dict[str, Any] | None = None,
    scheduled_at: datetime | None = None,
    semantic_key: str | None = None,
) -> CareNotification | None:
    sk = semantic_key or semantic_key_for_type(notification_type)
    if notification_type in PROACTIVE_CARE_SEMANTIC_KEYS and sk is None:
        logger.info(
            "Care notification blocked: missing semantic key for user %s type %s",
            user.id,
            notification_type,
        )
        return None
    if not can_send_care_notification(db, user, notification_type, semantic_key=sk):
        logger.info(
            "Care notification blocked by guard for user %s type %s",
            user.id,
            notification_type,
        )
        return None

    if sk:
        since = datetime.now(timezone.utc) - timedelta(
            hours=dedup_hours_for_semantic_key(sk)
        )
        existing = (
            db.query(CareNotification)
            .filter(
                CareNotification.user_id == user.id,
                CareNotification.type == notification_type,
                CareNotification.family_id == family_id,
                CareNotification.semantic_key == sk,
                CareNotification.status.in_(DEDUP_STATUSES),
                CareNotification.created_at >= since,
            )
            .first()
        )
        if existing is not None:
            return None

    template = CARE_TEMPLATES.get(notification_type, CARE_TEMPLATES["water"])
    row = CareNotification(
        user_id=user.id,
        family_id=family_id,
        type=notification_type,
        title=title or template["title"],
        message=message or template["message"],
        payload=payload,
        status="pending",
        scheduled_at=scheduled_at,
        semantic_key=sk,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def log_care_event(
    db: Session,
    user: User,
    event_type: str,
    *,
    source: str = "care",
    family_id: int | None = None,
    payload: dict[str, Any] | None = None,
) -> CareEvent:
    event = CareEvent(
        user_id=user.id,
        family_id=family_id,
        event_type=event_type,
        source=source,
        payload=payload,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


async def send_telegram_care_notification(
    db: Session,
    notification: CareNotification,
    user: User,
) -> bool:
    if notification.status != "pending":
        return notification.status == "sent"

    if not user.telegram_id:
        _mark_notification_failed(
            notification,
            error_type="missing_telegram_id",
            error_message="User has no telegram_id",
        )
        db.commit()
        logger.info("Care notification skipped: no telegram_id for user %s", user.id)
        return False

    claimed = (
        db.query(CareNotification)
        .filter(
            CareNotification.id == notification.id,
            CareNotification.status == "pending",
        )
        .update({"status": "sending"}, synchronize_session=False)
    )
    db.commit()
    if claimed != 1:
        db.refresh(notification)
        return notification.status == "sent"
    db.refresh(notification)

    template = CARE_TEMPLATES.get(notification.type, {})
    web_path = (notification.payload or {}).get(
        "web_app_path", template.get("web_app_path", "/")
    )
    button = (notification.payload or {}).get(
        "button_text", template.get("button_text", "Открыть приложение")
    )
    text = f"<b>{notification.title}</b>\n\n{notification.message}"

    try:
        sent = await send_telegram_message(
            user.telegram_id,
            text,
            web_app_path=web_path,
            button_text=button,
        )
    except Exception as exc:
        logger.exception(
            "Telegram care notification failed for user %s notification %s",
            user.id,
            notification.id,
        )
        _mark_notification_failed(
            notification,
            error_type=exc.__class__.__name__,
            error_message=str(exc),
        )
        db.commit()
        log_care_event(
            db,
            user,
            f"care_{notification.type}_failed",
            payload={"notification_id": notification.id},
        )
        return False

    if sent:
        notification.status = "sent"
        notification.sent_at = datetime.now(timezone.utc)
    else:
        _mark_notification_failed(
            notification,
            error_type="telegram_not_ok",
            error_message="Telegram send returned false",
        )
    db.commit()

    log_care_event(
        db,
        user,
        f"care_{notification.type}_{'sent' if sent else 'failed'}",
        payload={"notification_id": notification.id},
    )
    return sent


def _mark_notification_failed(
    notification: CareNotification,
    *,
    error_type: str,
    error_message: str,
) -> None:
    payload = notification.payload if isinstance(notification.payload, dict) else {}
    notification.payload = {
        **payload,
        "error_type": error_type,
        "error_message": error_message[:500],
        "failed_at": datetime.now(timezone.utc).isoformat(),
    }
    notification.status = "failed"
    notification.sent_at = None


def build_care_context(db: Session, user: User) -> CareContext:
    scope = resolve_scope(db, user, None)
    selected = get_selected_menu(db, scope)
    shopping = shopping_list_service.get_shopping_list(db, user, scope)
    pantry = pantry_service.list_pantry(db, user, scope)
    profile = get_or_create_profile(db, user)

    unchecked = sum(1 for item in shopping.items if not item.checked)
    expiring = sum(
        1
        for item in pantry.items
        if not item.is_expired
        and 0 <= item.days_until_expiry <= 3
    )

    from app.services import family as family_service

    membership = family_service.get_user_membership(db, user)

    return CareContext(
        has_menu=selected is not None,
        menu_title=selected.menu.title if selected else None,
        shopping_unchecked=unchecked,
        pantry_count=pantry.active_count,
        pantry_expiring=expiring,
        has_nutrition_goal=bool(profile.nutrition_goal),
        nutrition_goal=profile.nutrition_goal,
        has_family=membership is not None,
        is_pro=_user_has_pro(db, user),
    )


def generate_basic_care_tips(
    db: Session, user: User, context: CareContext | None = None
) -> list[CareTipPreview]:
    ctx = context or build_care_context(db, user)
    tips: list[CareTipPreview] = []

    if ctx.shopping_unchecked > 0 and ctx.has_menu:
        t = CARE_TEMPLATES["shopping"]
        tips.append(
            CareTipPreview(type="shopping", title=t["title"], message=t["message"])
        )
    if ctx.pantry_expiring > 0 and ctx.has_menu:
        t = CARE_TEMPLATES["pantry"]
        msg = (
            f"Скоро истекает {ctx.pantry_expiring} продуктов. "
            "Обновите запасы для точного меню."
        )
        tips.append(CareTipPreview(type="pantry", title=t["title"], message=msg))
    elif ctx.pantry_count > 0 and ctx.has_menu:
        t = CARE_TEMPLATES["pantry"]
        tips.append(CareTipPreview(type="pantry", title=t["title"], message=t["message"]))
    if ctx.has_menu:
        t = CARE_TEMPLATES["menu"]
        tips.append(CareTipPreview(type="menu", title=t["title"], message=t["message"]))
    if ctx.has_nutrition_goal and ctx.nutrition_goal in ("sport", "gain"):
        t = CARE_TEMPLATES["protein"]
        tips.append(
            CareTipPreview(type="protein", title=t["title"], message=t["message"])
        )
    t = CARE_TEMPLATES["water"]
    tips.append(CareTipPreview(type="water", title=t["title"], message=t["message"]))
    if ctx.has_family:
        t = CARE_TEMPLATES["family"]
        tips.append(CareTipPreview(type="family", title=t["title"], message=t["message"]))
    if ctx.is_pro:
        t = CARE_TEMPLATES["pro"]
        tips.append(CareTipPreview(type="pro", title=t["title"], message=t["message"]))

    return tips


async def send_care_notification_by_type(
    db: Session,
    user: User,
    notification_type: str,
    *,
    ignore_quiet_hours: bool = False,
    ignore_cooldown: bool = False,
    custom_message: str | None = None,
) -> tuple[bool, str, CareNotification | None]:
    semantic_key = semantic_key_for_type(notification_type)
    if not should_send_notification(
        db,
        user,
        notification_type,
        ignore_quiet_hours=ignore_quiet_hours,
        ignore_cooldown=ignore_cooldown,
        semantic_key=semantic_key,
    ):
        return False, "Сейчас это напоминание отправить нельзя (настройки или пауза).", None

    template = CARE_TEMPLATES[notification_type]
    notification = create_care_notification(
        db,
        user,
        notification_type,
        message=custom_message or template["message"],
        payload={
            "web_app_path": template["web_app_path"],
            "button_text": template["button_text"],
        },
        semantic_key=semantic_key,
    )
    if notification is None:
        return False, "Такое напоминание уже отправлялось недавно.", None
    sent = await send_telegram_care_notification(db, notification, user)
    if sent:
        return True, "Сообщение отправлено в Telegram.", notification
    if not settings.telegram_bot_token:
        return (
            False,
            "Бот не настроен — уведомление сохранено, но не отправлено.",
            notification,
        )
    if not user.telegram_id:
        return False, "Не найден Telegram-чат пользователя.", notification
    return False, "Не удалось отправить в Telegram. Попробуйте позже.", notification


async def maybe_notify_menu_ready(db: Session, user: User) -> None:
    if not should_send_notification(db, user, "menu"):
        return
    ctx = build_care_context(db, user)
    if not ctx.has_menu:
        return
    await send_care_notification_by_type(db, user, "menu")


async def process_care_reminders_for_user(db: Session, user: User) -> None:
    """Send at most one contextual care tip per scheduler tick."""
    from app.services.care_guard import notifications_onboarded

    if not notifications_onboarded(db, user):
        return

    settings_row = get_or_create_care_settings(db, user)
    if settings_row.care_level == "off":
        return
    if settings_row.care_level == "minimal" and not any(
        [
            settings_row.menu_enabled,
            settings_row.shopping_enabled,
            settings_row.pantry_enabled,
        ]
    ):
        return

    ctx = build_care_context(db, user)
    tips = generate_basic_care_tips(db, user, ctx)

    for tip in tips:
        if should_send_notification(db, user, tip.type):
            await send_care_notification_by_type(db, user, tip.type)
            return


async def process_all_care_reminders(db: Session) -> None:
    if not settings.care_scheduler_allowed:
        return
    if not settings.telegram_bot_token:
        return
    users = db.query(User).filter(User.phone_number.isnot(None)).all()
    for user in users:
        try:
            await process_care_reminders_for_user(db, user)
        except Exception:
            logger.exception("Care reminder failed for user %s", user.id)
