"""Today's consumed macros from meal check-ins + selected menu."""

from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from app.models.meal_checkin import MealCheckin
from app.models.meal_consumption_log import MealConsumptionLog
from app.models.user import User
from app.schemas.progress import NutritionActualResponse
from app.services.app_scope import AppScope
from app.services.menu_selection import get_selected_menu
from app.services.water_intake import sum_water_for_date

EATEN_STATUSES = frozenset(
    {
        "ate_home",
        "ate_work",
        "ate_cafe",
        "ate_restaurant",
        "ate_delivery",
        "ate_other",
        "completed",
    }
)


def _scope_checkin_filter(db: Session, scope: AppScope, on_date: date):
    q = db.query(MealCheckin).filter(MealCheckin.planned_date == on_date)
    if scope.is_family and scope.family_id:
        return q.filter(MealCheckin.family_id == scope.family_id)
    return q.filter(
        MealCheckin.user_id == scope.user_id,
        MealCheckin.family_id.is_(None),
    )


def list_checkins_for_date(
    db: Session, scope: AppScope, on_date: date | None = None
) -> list[MealCheckin]:
    on_date = on_date or date.today()
    return (
        _scope_checkin_filter(db, scope, on_date)
        .order_by(MealCheckin.updated_at.desc())
        .all()
    )


def _latest_checkins_by_meal(checkins: list[MealCheckin]) -> dict[str, MealCheckin]:
    """Latest check-in per (member, meal_type) — keys 'memberId:meal_type'."""
    out: dict[str, MealCheckin] = {}
    for row in checkins:
        key = f"{row.family_member_id or 0}:{row.meal_type}"
        if key not in out:
            out[key] = row
    return out


def _scope_consumption_filter(db: Session, scope: AppScope, on_date: date):
    q = db.query(MealConsumptionLog).filter(MealConsumptionLog.planned_date == on_date)
    if scope.is_family and scope.family_id:
        return q.filter(MealConsumptionLog.family_id == scope.family_id)
    return q.filter(
        MealConsumptionLog.user_id == scope.user_id,
        MealConsumptionLog.family_id.is_(None),
    )


def _latest_consumption_by_meal(
    logs: list[MealConsumptionLog],
) -> dict[str, MealConsumptionLog]:
    out: dict[str, MealConsumptionLog] = {}
    for row in logs:
        key = f"{row.family_member_id or 0}:{row.meal_type or ''}"
        if key not in out:
            out[key] = row
    return out


def compute_today_nutrition_actual(
    db: Session, user: User, scope: AppScope
) -> NutritionActualResponse:
    today = date.today()
    checkins = list_checkins_for_date(db, scope, today)
    by_meal = _latest_checkins_by_meal(checkins)
    consumption_logs = (
        _scope_consumption_filter(db, scope, today)
        .order_by(MealConsumptionLog.updated_at.desc(), MealConsumptionLog.id.desc())
        .all()
    )
    by_consumption_meal = _latest_consumption_by_meal(consumption_logs)

    calories = 0
    protein = 0
    fat = 0
    carbs = 0
    meals_logged = 0

    for row in by_consumption_meal.values():
        if row.status != "eaten":
            continue
        if row.calories_estimated is None or row.calories_estimated <= 0:
            continue
        cal = int(row.calories_estimated)
        calories += cal
        protein += int(row.protein_estimated or 0)
        fat += int(row.fat_estimated or 0)
        carbs += int(row.carbs_estimated or 0)
        meals_logged += 1

    for row in by_meal.values():
        key = f"{row.family_member_id or 0}:{row.meal_type}"
        if key in by_consumption_meal:
            continue
        if row.actual_status not in EATEN_STATUSES:
            continue
        if row.actual_calories and row.actual_calories > 0:
            cal = int(row.actual_calories)
            p = int(row.actual_protein_g or 0)
            f = int(row.actual_fat_g or 0)
            c = int(row.actual_carbs_g or 0)
            if p == 0 and f == 0 and c == 0:
                p = int(cal * 0.25 / 4)
                f = int(cal * 0.30 / 9)
                c = int(cal * 0.45 / 4)
        else:
            continue
        calories += cal
        protein += p
        fat += f
        carbs += c
        meals_logged += 1

    water_ml = sum_water_for_date(db, user, scope, today)

    return NutritionActualResponse(
        calories_consumed=calories if meals_logged else 0,
        protein_consumed_g=protein if meals_logged else 0,
        fat_consumed_g=fat if meals_logged else 0,
        carbs_consumed_g=carbs if meals_logged else 0,
        water_consumed_ml=water_ml,
        meals_logged=meals_logged,
    )
