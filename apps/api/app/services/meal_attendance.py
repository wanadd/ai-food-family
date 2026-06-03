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
    today_iso = date.today().isoformat()
    days = menu_data.get("days")
    if isinstance(days, list):
        for block in days:
            if not isinstance(block, dict):
                continue
            if block.get("date_iso") == today_iso:
                meals = block.get("meals")
                break
        else:
            meals = None
            if days and isinstance(days[0], dict):
                meals = days[0].get("meals")
    else:
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
            recipe_id: int | None = None
            raw_rid = item.get("recipe_id")
            if raw_rid is not None:
                try:
                    recipe_id = int(raw_rid)
                except (TypeError, ValueError):
                    recipe_id = None
            result.append(
                MenuTodayMeal(
                    meal_type=meal_type,
                    label=MEAL_LABELS.get(meal_type, meal_type),
                    name=name.strip(),
                    recipe_id=recipe_id,
                )
            )
    return result[:6]


def enrich_today_meals_images(db: Session, meals: list[MenuTodayMeal]) -> list[MenuTodayMeal]:
    """Attach image_url from recipes table (PLANAM 2026 Home rail)."""
    from app.models.recipe import Recipe

    enriched: list[MenuTodayMeal] = []
    for meal in meals:
        image_url: str | None = None
        if meal.recipe_id is not None:
            recipe = db.get(Recipe, meal.recipe_id)
            if recipe and recipe.image_url:
                image_url = recipe.image_url
        enriched.append(meal.model_copy(update={"image_url": image_url}))
    return enriched


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


def _checkin_query(
    db: Session,
    scope: AppScope,
    meal_type: str,
    on_date: date,
    family_member_id: int | None = None,
):
    q = db.query(MealCheckin).filter(
        MealCheckin.meal_type == meal_type,
        MealCheckin.planned_date == on_date,
    )
    if scope.is_family and scope.family_id:
        q = q.filter(MealCheckin.family_id == scope.family_id)
        if family_member_id is not None:
            q = q.filter(MealCheckin.family_member_id == family_member_id)
        else:
            q = q.filter(MealCheckin.family_member_id.is_(None))
        return q
    q = q.filter(
        MealCheckin.user_id == scope.user_id,
        MealCheckin.family_id.is_(None),
    )
    if family_member_id is not None:
        q = q.filter(MealCheckin.family_member_id == family_member_id)
    else:
        q = q.filter(MealCheckin.family_member_id.is_(None))
    return q


def upsert_meal_checkin(
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
    actual_calories: float | None = None,
    actual_protein_g: float | None = None,
    actual_fat_g: float | None = None,
    actual_carbs_g: float | None = None,
    recipe_id: int | None = None,
) -> MealCheckin:
    on_date = planned_date or date.today()
    row = _checkin_query(
        db, scope, meal_type, on_date, family_member_id
    ).first()
    if row is None:
        row = MealCheckin(
            user_id=user.id if not scope.is_family else None,
            family_id=scope.family_id if scope.is_family else None,
            family_member_id=family_member_id,
            meal_type=meal_type,
            planned_date=on_date,
        )
        db.add(row)
    row.actual_status = actual_status
    row.actual_description = actual_description
    row.leftover_servings_delta = leftover_servings_delta
    row.recipe_id = recipe_id
    if actual_calories is not None:
        row.actual_calories = actual_calories
    if actual_protein_g is not None:
        row.actual_protein_g = actual_protein_g
    if actual_fat_g is not None:
        row.actual_fat_g = actual_fat_g
    if actual_carbs_g is not None:
        row.actual_carbs_g = actual_carbs_g
    db.commit()
    db.refresh(row)
    return row


def create_meal_checkin(
    db: Session,
    user: User,
    scope: AppScope,
    **kwargs,
) -> MealCheckin:
    return upsert_meal_checkin(db, user, scope, **kwargs)
