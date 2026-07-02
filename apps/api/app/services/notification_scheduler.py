import asyncio
import logging
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

from app.config import settings
from app.database import SessionLocal
from app.models.notification_settings import UserNotificationSettings
from app.models.user import User
from app.services.care_guard import can_send_scheduled_reminder
from app.services.notification_messages import (
    build_buy_reminder_text,
    build_meal_cook_reminder_text,
)
from app.services.scheduler_lock import notification_scheduler_lock
from app.telegram.messages import send_telegram_message

logger = logging.getLogger(__name__)

POLL_INTERVAL_SECONDS = 30
MEAL_CONSUMPTION_REMINDER_INTERVAL_SECONDS = 15 * 60

_last_meal_consumption_reminder_run: datetime | None = None

MEAL_REMINDERS = (
    ("breakfast", "cook_breakfast_enabled", "cook_breakfast_time", "last_breakfast_sent_date"),
    ("lunch", "cook_lunch_enabled", "cook_lunch_time", "last_lunch_sent_date"),
    ("dinner", "cook_dinner_enabled", "cook_dinner_time", "last_dinner_sent_date"),
)


async def run_notification_scheduler() -> None:
    if not settings.notification_scheduler_allowed:
        logger.info("Notification scheduler disabled by environment flags")
        return
    logger.info("Notification scheduler started (interval %ss)", POLL_INTERVAL_SECONDS)
    while True:
        await asyncio.sleep(POLL_INTERVAL_SECONDS)
        try:
            await _process_due_reminders()
        except Exception:
            logger.exception("Notification scheduler tick failed")


async def _process_due_reminders() -> None:
    if not settings.notification_scheduler_allowed:
        return
    if not settings.telegram_bot_token:
        return

    db = SessionLocal()
    try:
        with notification_scheduler_lock(db) as locked:
            if not locked:
                return

            rows = (
                db.query(UserNotificationSettings, User)
                .join(User, User.id == UserNotificationSettings.user_id)
                .filter(User.is_blocked.is_(False), User.is_deleted.is_(False))
                .all()
            )

            for notification_settings, user in rows:
                if not can_send_scheduled_reminder(db, user):
                    continue
                await _maybe_send_buy(db, notification_settings, user)
                for meal_type, enabled_key, time_key, sent_key in MEAL_REMINDERS:
                    await _maybe_send_meal_cook(
                        db,
                        notification_settings,
                        user,
                        meal_type,
                        enabled_key,
                        time_key,
                        sent_key,
                    )

            from app.services.care import process_all_care_reminders

            await process_all_care_reminders(db)

            global _last_meal_consumption_reminder_run
            now_utc = datetime.now(timezone.utc)
            if (
                _last_meal_consumption_reminder_run is None
                or (now_utc - _last_meal_consumption_reminder_run).total_seconds()
                >= MEAL_CONSUMPTION_REMINDER_INTERVAL_SECONDS
            ):
                from app.services.meal_consumption_reminders import (
                    process_meal_consumption_reminders,
                )

                await process_meal_consumption_reminders(db)
                _last_meal_consumption_reminder_run = now_utc

            db.commit()
    finally:
        db.close()


async def _maybe_send_buy(
    db,
    notification_settings: UserNotificationSettings,
    user: User,
) -> None:
    if not notification_settings.buy_reminder_enabled:
        return

    today, current_time = _now_in_timezone(notification_settings.timezone)
    if notification_settings.buy_reminder_time != current_time:
        return
    if notification_settings.last_buy_sent_date == today:
        return

    text = build_buy_reminder_text(db, user)
    sent = await send_telegram_message(
        user.telegram_id,
        text,
        web_app_path="/shopping",
        button_text="Список покупок",
    )
    if sent:
        notification_settings.last_buy_sent_date = today
        logger.info("Buy reminder sent to user %s", user.id)


async def _maybe_send_meal_cook(
    db,
    notification_settings: UserNotificationSettings,
    user: User,
    meal_type: str,
    enabled_attr: str,
    time_attr: str,
    sent_attr: str,
) -> None:
    if not getattr(notification_settings, enabled_attr, False):
        return
    if not notification_settings.cook_reminder_enabled:
        return

    today, current_time = _now_in_timezone(notification_settings.timezone)
    if getattr(notification_settings, time_attr) != current_time:
        return
    if getattr(notification_settings, sent_attr) == today:
        return

    text = build_meal_cook_reminder_text(db, user, meal_type)
    if not text:
        return

    sent = await send_telegram_message(
        user.telegram_id,
        text,
        web_app_path="/menu",
        button_text="Открыть меню",
    )
    if sent:
        setattr(notification_settings, sent_attr, today)
        notification_settings.last_cook_sent_date = today
        logger.info("%s cook reminder sent to user %s", meal_type, user.id)


def _now_in_timezone(timezone_name: str) -> tuple[date, str]:
    try:
        tz = ZoneInfo(timezone_name)
    except Exception:
        tz = ZoneInfo("Europe/Moscow")
    now = datetime.now(tz)
    return now.date(), now.strftime("%H:%M")
