"""Deterministic Health Intelligence foundation (Phase 4C). No real AI."""

from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from app.models.external_food_log import ExternalFoodLog
from app.models.meal_consumption_log import MealConsumptionLog
from app.models.user import User
from app.services.app_scope import AppScope
from app.services.meal_consumption import get_meal_consumption_logs
from app.services.meal_consumption_nutrition import get_meal_consumption_nutrition_summary
from app.services.nutrition.plan_aggregator import build_day_nutrition


HEALTH_STATUSES = frozenset(
    {
        "on_plan",
        "no_fact_data",
        "partially_logged",
        "off_plan_due_to_skip",
        "off_plan_due_to_external_food",
        "needs_attention",
    }
)


def _confirmed_external_logs(
    db: Session,
    *,
    user_id: int,
    planned_date: date,
    family_id: int | None,
) -> list[ExternalFoodLog]:
    q = db.query(ExternalFoodLog).filter(
        ExternalFoodLog.user_id == user_id,
        ExternalFoodLog.planned_date == planned_date,
        ExternalFoodLog.status == "confirmed",
    )
    if family_id is not None:
        q = q.filter(ExternalFoodLog.family_id == family_id)
    return q.all()


def _external_totals(logs: list[ExternalFoodLog]) -> dict[str, float]:
    acc = {"calories": 0.0, "protein": 0.0, "fat": 0.0, "carbs": 0.0}
    for row in logs:
        acc["calories"] += float(row.calories_estimated or 0)
        acc["protein"] += float(row.protein_estimated or 0)
        acc["fat"] += float(row.fat_estimated or 0)
        acc["carbs"] += float(row.carbs_estimated or 0)
    return acc


def _round_totals(totals: dict[str, float]) -> dict[str, int]:
    return {k: int(round(v)) for k, v in totals.items()}


def compute_health_day_snapshot(
    db: Session,
    *,
    caller: User,
    scope: AppScope,
    family_id: int | None = None,
    menu_selection_id: int | None = None,
    day_index: int | None = None,
    planned_date: date | None = None,
) -> dict:
    nutrition = get_meal_consumption_nutrition_summary(
        db,
        caller=caller,
        scope=scope,
        family_id=family_id,
        menu_selection_id=menu_selection_id,
        day_index=day_index,
        planned_date=planned_date,
    )

    plan_date_str = planned_date.isoformat() if planned_date else None
    day_plan = build_day_nutrition(db, caller.id, scope, plan_date_str)
    planned_meals = int(day_plan.get("coverage", {}).get("total_items", 0))

    logs: list[MealConsumptionLog] = [
        log
        for log in get_meal_consumption_logs(
            db,
            caller=caller,
            family_id=family_id,
            menu_selection_id=menu_selection_id,
            day_index=day_index,
            planned_date=planned_date,
        )
        if log.user_id == caller.id
    ]

    external_confirmed = _confirmed_external_logs(
        db,
        user_id=caller.id,
        planned_date=planned_date or date.today(),
        family_id=family_id,
    )

    has_logs = len(logs) > 0
    skipped = sum(1 for log in logs if log.status == "skipped")
    ate_out = sum(1 for log in logs if log.status == "ate_out")
    eaten = sum(1 for log in logs if log.status == "eaten")
    not_logged_meals = max(0, planned_meals - len(logs)) if planned_meals else 0

    actual = nutrition.get("actual")
    planned = nutrition.get("planned") or {}
    targets = nutrition.get("targets") or day_plan.get("targets") or {}

    status = resolve_health_status(
        has_logs=has_logs,
        skipped=skipped,
        ate_out=ate_out,
        external_confirmed=len(external_confirmed) > 0,
        logged_meals=len(logs),
        planned_meals=planned_meals,
    )

    external_totals = _external_totals(external_confirmed)
    combined_actual = None
    if has_logs or external_confirmed:
        base = {
            "calories": float((actual or {}).get("calories", 0)),
            "protein": float((actual or {}).get("protein", 0)),
            "fat": float((actual or {}).get("fat", 0)),
            "carbs": float((actual or {}).get("carbs", 0)),
        }
        for key in base:
            base[key] += external_totals[key]
        combined_actual = _round_totals(base)

    remaining_to_goal = None
    target_kcal = targets.get("kcal")
    if target_kcal and combined_actual is not None:
        remaining_to_goal = int(target_kcal) - combined_actual["calories"]

    return {
        "status": status,
        "has_fact_data": has_logs or len(external_confirmed) > 0,
        "planned_day_nutrition": planned,
        "actual_day_nutrition": combined_actual,
        "not_logged_meals": not_logged_meals,
        "skipped_meals": skipped,
        "ate_out_meals": ate_out,
        "eaten_meals": eaten,
        "external_food_logs_count": len(external_confirmed),
        "remaining_to_goal_kcal": remaining_to_goal,
        "recommendations": build_health_recommendations(
            status=status,
            skipped=skipped,
            ate_out=ate_out,
            not_logged=not_logged_meals,
            remaining_kcal=remaining_to_goal,
            protein_gap=_macro_gap(combined_actual, targets, "protein"),
        ),
    }


def _macro_gap(
    actual: dict[str, int] | None,
    targets: dict,
    macro: str,
) -> int | None:
    if not actual or not targets.get(macro):
        return None
    return int(targets[macro]) - actual.get(macro, 0)


def resolve_health_status(
    *,
    has_logs: bool,
    skipped: int,
    ate_out: int,
    external_confirmed: bool,
    logged_meals: int,
    planned_meals: int,
) -> str:
    if not has_logs and not external_confirmed:
        return "no_fact_data"
    if external_confirmed or ate_out > 0:
        return "off_plan_due_to_external_food"
    if skipped > 0:
        return "off_plan_due_to_skip"
    if planned_meals > 0 and logged_meals < planned_meals:
        return "partially_logged"
    if has_logs and skipped == 0 and ate_out == 0:
        return "on_plan"
    return "needs_attention"


def build_health_recommendations(
    *,
    status: str,
    skipped: int,
    ate_out: int,
    not_logged: int,
    remaining_kcal: int | None,
    protein_gap: int | None,
) -> list[str]:
    tips: list[str] = []
    if status == "no_fact_data":
        tips.append("Факт пока не отмечен — ориентируйтесь на план дня.")
        return tips
    if status == "on_plan":
        tips.append("Вы идёте по плану. Цель дня соблюдается.")
        return tips
    if protein_gap is not None and protein_gap > 15:
        tips.append("Белка может не хватать — добавьте белковый перекус.")
    if remaining_kcal is not None and remaining_kcal < -200:
        tips.append("Калории выше плана — можно облегчить ужин.")
    if skipped > 0:
        tips.append("Есть пропущенные приёмы пищи — скорректируйте следующий приём.")
    if ate_out > 0:
        tips.append("Была еда вне плана — пересчитайте факт дня.")
    if not_logged > 0:
        tips.append("Часть блюд не отмечена — день считается частично.")
    if not tips:
        tips.append("Следите за балансом плана и факта.")
    return tips
