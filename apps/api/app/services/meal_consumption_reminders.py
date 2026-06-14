"""Automatic Telegram reminders to log meal consumption (Phase 3A)."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.config import settings
from app.models.meal_consumption_log import MealConsumptionLog
from app.models.meal_consumption_reminder_event import MealConsumptionReminderEvent
from app.models.notification_settings import UserNotificationSettings
from app.models.user import User
from app.services import family as family_service
from app.services.app_scope import AppScope
from app.services.care import _is_quiet_hours, get_or_create_care_settings
from app.services.menu_selection import get_latest_selection, menu_from_storage
from app.services.notifications import get_or_create_settings as get_notif_settings
from app.telegram.messages import send_telegram_message

logger = logging.getLogger(__name__)

REMINDER_KIND = "meal_consumption_missing"
LOGGED_STATUSES = frozenset({"eaten", "skipped", "ate_out", "unknown"})
TERMINAL_EVENT_STATUSES = frozenset(
    {
        "sent",
        "skipped_already_logged",
        "skipped_too_late",
        "skipped_no_telegram",
        "skipped_notifications_disabled",
    }
)

DEFAULT_MEAL_TIMES: dict[str, str] = {
    "breakfast": "09:30",
    "lunch": "14:30",
    "dinner": "20:30",
    "snack": "17:30",
}

DELAY_MINUTES: dict[str, int] = {
    "breakfast": 60,
    "lunch": 60,
    "dinner": 60,
    "snack": 45,
}

MEAL_TYPE_LABELS: dict[str, str] = {
    "breakfast": "завтрака",
    "lunch": "обеда",
    "dinner": "ужина",
    "snack": "перекуса",
}

MAX_LATE_HOURS = 8


@dataclass(frozen=True)
class DueMealConsumptionReminder:
    user: User
    family_id: int | None
    menu_selection_id: int
    day_index: int | None
    planned_date: date
    meal_type: str
    due_at: datetime
    timezone_name: str


def build_meal_reminder_message(meal_type: str) -> str:
    label = MEAL_TYPE_LABELS.get(meal_type, "приёма пищи")
    return (
        f"После {label} не вижу отметки. Отметьте, что съели — "
        "это обновит «Питание сегодня»."
    )


def build_meal_reminder_web_app_path(meal_type: str) -> str:
    return f"/plan/today?openMealConsumption=1&mealType={meal_type}"


def has_meal_consumption_log(
    db: Session,
    *,
    user_id: int,
    family_id: int | None,
    menu_selection_id: int | None,
    day_index: int | None,
    planned_date: date,
    meal_type: str,
) -> bool:
    q = db.query(MealConsumptionLog).filter(
        MealConsumptionLog.user_id == user_id,
        MealConsumptionLog.meal_type == meal_type,
        MealConsumptionLog.status.in_(LOGGED_STATUSES),
    )
    if family_id is None:
        q = q.filter(MealConsumptionLog.family_id.is_(None))
    else:
        q = q.filter(MealConsumptionLog.family_id == family_id)

    if menu_selection_id is not None:
        q = q.filter(MealConsumptionLog.menu_selection_id == menu_selection_id)
    if day_index is not None:
        q = q.filter(MealConsumptionLog.day_index == day_index)
    q = q.filter(MealConsumptionLog.planned_date == planned_date)
    return q.first() is not None


def _scope_for_user(db: Session, user: User) -> AppScope:
    membership = family_service.get_user_membership(db, user)
    if membership is not None:
        return AppScope(mode="family", user_id=user.id, family_id=membership.family_id)
    return AppScope(mode="personal", user_id=user.id, family_id=None)


def _meal_time_for_user(
    notification_settings: UserNotificationSettings | None,
    meal_type: str,
) -> str:
    if notification_settings is not None:
        attr = {
            "breakfast": "cook_breakfast_time",
            "lunch": "cook_lunch_time",
            "dinner": "cook_dinner_time",
        }.get(meal_type)
        if attr:
            value = getattr(notification_settings, attr, None)
            if value:
                return value
    return DEFAULT_MEAL_TIMES.get(meal_type, "12:00")


def _parse_hhmm(value: str) -> time:
    hour, minute = value.split(":")
    return time(hour=int(hour), minute=int(minute))


def _reminder_due_at(
    planned_date: date,
    meal_type: str,
    timezone_name: str,
    notification_settings: UserNotificationSettings | None,
) -> datetime:
    meal_time = _meal_time_for_user(notification_settings, meal_type)
    delay = DELAY_MINUTES.get(meal_type, 60)
    tz = ZoneInfo(timezone_name)
    local_meal = datetime.combine(planned_date, _parse_hhmm(meal_time), tzinfo=tz)
    return local_meal + timedelta(minutes=delay)


def _find_terminal_event(
    db: Session,
    *,
    user_id: int,
    planned_date: date,
    meal_type: str,
    menu_selection_id: int | None,
    day_index: int | None,
) -> MealConsumptionReminderEvent | None:
    q = db.query(MealConsumptionReminderEvent).filter(
        MealConsumptionReminderEvent.user_id == user_id,
        MealConsumptionReminderEvent.planned_date == planned_date,
        MealConsumptionReminderEvent.meal_type == meal_type,
        MealConsumptionReminderEvent.reminder_kind == REMINDER_KIND,
        MealConsumptionReminderEvent.status.in_(TERMINAL_EVENT_STATUSES),
    )
    if menu_selection_id is not None:
        q = q.filter(
            MealConsumptionReminderEvent.menu_selection_id == menu_selection_id
        )
    if day_index is not None:
        q = q.filter(MealConsumptionReminderEvent.day_index == day_index)
    return q.order_by(MealConsumptionReminderEvent.id.desc()).first()


def _upsert_event(
    db: Session,
    *,
    user_id: int,
    family_id: int | None,
    menu_selection_id: int | None,
    day_index: int | None,
    planned_date: date,
    meal_type: str,
    status: str,
    due_at: datetime | None = None,
    skipped_reason: str | None = None,
    error_message: str | None = None,
    sent_at: datetime | None = None,
) -> MealConsumptionReminderEvent:
    existing = (
        db.query(MealConsumptionReminderEvent)
        .filter(
            MealConsumptionReminderEvent.user_id == user_id,
            MealConsumptionReminderEvent.planned_date == planned_date,
            MealConsumptionReminderEvent.meal_type == meal_type,
            MealConsumptionReminderEvent.reminder_kind == REMINDER_KIND,
            MealConsumptionReminderEvent.menu_selection_id == menu_selection_id,
            MealConsumptionReminderEvent.day_index == day_index,
        )
        .order_by(MealConsumptionReminderEvent.id.desc())
        .first()
    )
    if existing and existing.status in TERMINAL_EVENT_STATUSES:
        return existing

    if existing:
        existing.status = status
        existing.due_at = due_at
        existing.skipped_reason = skipped_reason
        existing.error_message = error_message
        existing.sent_at = sent_at
        row = existing
    else:
        row = MealConsumptionReminderEvent(
            user_id=user_id,
            family_id=family_id,
            menu_selection_id=menu_selection_id,
            day_index=day_index,
            planned_date=planned_date,
            meal_type=meal_type,
            reminder_kind=REMINDER_KIND,
            status=status,
            due_at=due_at,
            skipped_reason=skipped_reason,
            error_message=error_message,
            sent_at=sent_at,
        )
        db.add(row)
    db.flush()
    return row


def should_send_meal_consumption_reminder(
    db: Session,
    *,
    user: User,
    notification_settings: UserNotificationSettings | None,
    due: DueMealConsumptionReminder,
    now: datetime,
) -> tuple[bool, str | None]:
    if user.is_blocked or user.is_deleted:
        return False, None
    if not user.telegram_id:
        return False, "skipped_no_telegram"
    if notification_settings is not None and not notification_settings.cook_reminder_enabled:
        return False, "skipped_notifications_disabled"

    if has_meal_consumption_log(
        db,
        user_id=user.id,
        family_id=due.family_id,
        menu_selection_id=due.menu_selection_id,
        day_index=due.day_index,
        planned_date=due.planned_date,
        meal_type=due.meal_type,
    ):
        return False, "skipped_already_logged"

    if _find_terminal_event(
        db,
        user_id=user.id,
        planned_date=due.planned_date,
        meal_type=due.meal_type,
        menu_selection_id=due.menu_selection_id,
        day_index=due.day_index,
    ):
        return False, "skipped_already_sent"

    if now < due.due_at:
        return False, None

    if now > due.due_at + timedelta(hours=MAX_LATE_HOURS):
        return False, "skipped_too_late"

    care_settings = get_or_create_care_settings(db, user)
    if _is_quiet_hours(care_settings, user, db):
        return False, None

    return True, None


def find_due_meal_consumption_reminders(
    db: Session,
    now: datetime | None = None,
) -> list[DueMealConsumptionReminder]:
    if now is None:
        now = datetime.now(timezone.utc)

    due_items: list[DueMealConsumptionReminder] = []
    users = (
        db.query(User)
        .filter(User.is_blocked.is_(False), User.is_deleted.is_(False))
        .all()
    )

    for user in users:
        if not user.telegram_id:
            continue

        notif = get_notif_settings(db, user)
        scope = _scope_for_user(db, user)
        selection = get_latest_selection(db, scope)
        if selection is None:
            continue

        tz_name = notif.timezone or "Europe/Moscow"
        try:
            local_today = now.astimezone(ZoneInfo(tz_name)).date()
        except Exception:
            local_today = now.astimezone(ZoneInfo("Europe/Moscow")).date()

        menu = menu_from_storage(selection.menu_data)
        if not menu.days:
            meal_types = {
                meal.meal_type
                for meal in menu.meals
                if meal.recipe_id is not None
            }
            for meal_type in meal_types:
                due_at = _reminder_due_at(local_today, meal_type, tz_name, notif)
                due_items.append(
                    DueMealConsumptionReminder(
                        user=user,
                        family_id=selection.family_id,
                        menu_selection_id=selection.id,
                        day_index=None,
                        planned_date=local_today,
                        meal_type=meal_type,
                        due_at=due_at,
                        timezone_name=tz_name,
                    )
                )
            continue

        day_plan = next(
            (d for d in menu.days if d.date_iso == local_today.isoformat()),
            None,
        )
        if day_plan is None:
            continue

        for meal in day_plan.meals:
            if meal.recipe_id is None:
                continue
            due_at = _reminder_due_at(
                local_today, meal.meal_type, tz_name, notif
            )
            due_items.append(
                DueMealConsumptionReminder(
                    user=user,
                    family_id=selection.family_id,
                    menu_selection_id=selection.id,
                    day_index=day_plan.day_index,
                    planned_date=local_today,
                    meal_type=meal.meal_type,
                    due_at=due_at,
                    timezone_name=tz_name,
                )
            )

    return due_items


async def send_due_meal_consumption_reminders(
    db: Session,
    now: datetime | None = None,
    *,
    dry_run: bool | None = None,
    limit: int | None = None,
    force: bool = False,
) -> dict[str, int]:
    if not settings.meal_consumption_reminders_enabled and not force:
        return {"skipped_disabled": 1}

    if now is None:
        now = datetime.now(timezone.utc)

    is_dry_run = (
        settings.meal_consumption_reminders_dry_run
        if dry_run is None
        else dry_run
    )

    counts = {
        "examined": 0,
        "sent": 0,
        "dry_run": 0,
        "skipped": 0,
        "failed": 0,
    }

    due_list = find_due_meal_consumption_reminders(db, now)
    if limit is not None:
        due_list = due_list[:limit]

    for due in due_list:
        counts["examined"] += 1
        notif = get_notif_settings(db, due.user)
        ok, skip_reason = should_send_meal_consumption_reminder(
            db,
            user=due.user,
            notification_settings=notif,
            due=due,
            now=now,
        )

        if not ok:
            if skip_reason in TERMINAL_EVENT_STATUSES:
                counts["skipped"] += 1
                _upsert_event(
                    db,
                    user_id=due.user.id,
                    family_id=due.family_id,
                    menu_selection_id=due.menu_selection_id,
                    day_index=due.day_index,
                    planned_date=due.planned_date,
                    meal_type=due.meal_type,
                    status=skip_reason,
                    due_at=due.due_at,
                    skipped_reason=skip_reason,
                )
            elif skip_reason == "skipped_already_sent":
                counts["skipped"] += 1
            continue

        if is_dry_run:
            counts["dry_run"] += 1
            logger.info(
                "DRY RUN meal consumption reminder user=%s meal=%s date=%s",
                due.user.id,
                due.meal_type,
                due.planned_date,
            )
            continue

        text = build_meal_reminder_message(due.meal_type)
        path = build_meal_reminder_web_app_path(due.meal_type)
        try:
            sent = await send_telegram_message(
                due.user.telegram_id,
                text,
                web_app_path=path,
                button_text="Отметить съеденное",
            )
        except Exception as exc:
            counts["failed"] += 1
            _upsert_event(
                db,
                user_id=due.user.id,
                family_id=due.family_id,
                menu_selection_id=due.menu_selection_id,
                day_index=due.day_index,
                planned_date=due.planned_date,
                meal_type=due.meal_type,
                status="failed",
                due_at=due.due_at,
                error_message=str(exc)[:500],
            )
            logger.exception(
                "Meal consumption reminder failed user=%s", due.user.id
            )
            continue

        if sent:
            counts["sent"] += 1
            _upsert_event(
                db,
                user_id=due.user.id,
                family_id=due.family_id,
                menu_selection_id=due.menu_selection_id,
                day_index=due.day_index,
                planned_date=due.planned_date,
                meal_type=due.meal_type,
                status="sent",
                due_at=due.due_at,
                sent_at=now,
            )
            logger.info(
                "Meal consumption reminder sent user=%s meal=%s",
                due.user.id,
                due.meal_type,
            )
        else:
            counts["failed"] += 1
            _upsert_event(
                db,
                user_id=due.user.id,
                family_id=due.family_id,
                menu_selection_id=due.menu_selection_id,
                day_index=due.day_index,
                planned_date=due.planned_date,
                meal_type=due.meal_type,
                status="failed",
                due_at=due.due_at,
                error_message="send_telegram_message returned false",
            )

    return counts


async def process_meal_consumption_reminders(db: Session) -> None:
    await send_due_meal_consumption_reminders(db)
