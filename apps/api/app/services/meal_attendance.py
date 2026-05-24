"""Home meal participation: schedules, check-ins, portion counts."""

from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from app.models.family import FamilyMember
from app.models.meal_checkin import MealCheckin
from app.models.meal_eating_schedule import MealEatingSchedule
from app.models.user import User
from app.schemas.menu_overview import MenuHomeAttendance, MenuTodayMeal
from app.services import family as family_service
from app.services.app_scope import AppScope

MEAL_LABELS = {
    "breakfast": "Завтрак",
    "lunch": "Обед",
    "dinner": "Ужин",
    "snack": "Перекус",
}

WEEKDAY_KEYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]


def _weekday_key(d: date) -> str:
    return WEEKDAY_KEYS[d.weekday()]


def _schedule_eats_home(schedule: MealEatingSchedule | None, meal_type: str, weekday: str) -> bool:
    if schedule is None:
        return True
    data = schedule.schedule_json or {}
    meal_cfg = data.get(meal_type)
    if not isinstance(meal_cfg, dict):
        return bool(data.get("default_home", True))
    if weekday in meal_cfg:
        return meal_cfg[weekday] == "home"
    return meal_cfg.get("default", "home") == "home"


def count_home_eaters(
    db: Session,
    scope: AppScope,
    *,
    meal_type: str,
    on_date: date | None = None,
) -> tuple[int, int]:
    """Return (home_eaters, total_members) for scope on date."""
    on_date = on_date or date.today()
    weekday = _weekday_key(on_date)

    if scope.is_personal:
        return 1, 1

    from app.models.family import Family
    from sqlalchemy.orm import joinedload

    family = None
    if scope.family_id:
        family = (
            db.query(Family)
            .options(joinedload(Family.members))
            .filter(Family.id == scope.family_id)
            .one_or_none()
        )
    if family is None or not family.members:
        return 1, 1

    total = len(family.members)
    home = 0
    for member in family.members:
        sched = (
            db.query(MealEatingSchedule)
            .filter(MealEatingSchedule.family_member_id == member.id)
            .one_or_none()
        )
        if _schedule_eats_home(sched, meal_type, weekday):
            home += 1
    return home, total


def build_home_attendance_summary(
    db: Session, user: User, scope: AppScope, on_date: date | None = None
) -> MenuHomeAttendance:
    on_date = on_date or date.today()
    b_home, total = count_home_eaters(db, scope, meal_type="breakfast", on_date=on_date)
    l_home, _ = count_home_eaters(db, scope, meal_type="lunch", on_date=on_date)
    d_home, _ = count_home_eaters(db, scope, meal_type="dinner", on_date=on_date)
    return MenuHomeAttendance(
        breakfast_home=b_home,
        lunch_home=l_home,
        dinner_home=d_home,
        total_members=total,
    )


def extract_today_meals(menu_data: dict | None) -> list[MenuTodayMeal]:
    if not menu_data or not isinstance(menu_data, dict):
        return []
    meals = menu_data.get("meals")
    if not isinstance(meals, list):
        return []
    result: list[MenuTodayMeal] = []
    for item in meals:
        if not isinstance(item, dict):
            continue
        meal_type = str(item.get("meal_type") or "lunch")
        name = item.get("name")
        if isinstance(name, str) and name.strip():
            result.append(
                MenuTodayMeal(
                    meal_type=meal_type,
                    label=MEAL_LABELS.get(meal_type, meal_type),
                    name=name.strip(),
                )
            )
    return result[:6]


def resolve_persons_count_for_meal(
    db: Session,
    user: User,
    scope: AppScope,
    meal_type: str,
    *,
    fallback: int | None = None,
) -> int:
    home, _total = count_home_eaters(db, scope, meal_type=meal_type)
    if home > 0:
        return home
    return fallback or 1


def upsert_member_schedule(
    db: Session,
    member: FamilyMember,
    schedule_json: dict,
) -> MealEatingSchedule:
    row = (
        db.query(MealEatingSchedule)
        .filter(MealEatingSchedule.family_member_id == member.id)
        .one_or_none()
    )
    if row is None:
        row = MealEatingSchedule(
            family_member_id=member.id,
            family_id=member.family_id,
            schedule_json=schedule_json,
        )
        db.add(row)
    else:
        row.schedule_json = schedule_json
    db.commit()
    db.refresh(row)
    return row


def create_meal_checkin(
    db: Session,
    user: User,
    scope: AppScope,
    *,
    meal_type: str,
    actual_status: str,
    planned_date: date | None = None,
    family_member_id: int | None = None,
    actual_description: str | None = None,
    leftover_servings_delta: int | None = None,
) -> MealCheckin:
    row = MealCheckin(
        user_id=user.id if not scope.is_family else None,
        family_id=scope.family_id if scope.is_family else None,
        family_member_id=family_member_id,
        meal_type=meal_type,
        planned_date=planned_date or date.today(),
        actual_status=actual_status,
        actual_description=actual_description,
        leftover_servings_delta=leftover_servings_delta,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row
