"""Nutrition summary from personal meal consumption logs (Phase 2B)."""

from __future__ import annotations

from datetime import date

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.meal_consumption_log import MealConsumptionLog
from app.models.user import User
from app.services.app_scope import AppScope
from app.services.meal_consumption import (
    FAMILY_ACCESS_DENIED,
    _caller_membership,
    _estimate_nutrition,
    get_meal_consumption_logs,
)
from app.services.nutrition.plan_aggregator import build_day_nutrition


def _totals_dict(
    *,
    calories: float = 0.0,
    protein: float = 0.0,
    fat: float = 0.0,
    carbs: float = 0.0,
) -> dict[str, int]:
    return {
        "calories": int(round(calories)),
        "protein": int(round(protein)),
        "fat": int(round(fat)),
        "carbs": int(round(carbs)),
    }


def _planned_from_day(day: dict) -> dict[str, int]:
    totals = day.get("totals") or {}
    return _totals_dict(
        calories=totals.get("kcal", 0),
        protein=totals.get("protein", 0),
        fat=totals.get("fat", 0),
        carbs=totals.get("carbs", 0),
    )


def _nutrition_for_eaten_log(db: Session, log: MealConsumptionLog) -> dict[str, float]:
    if log.calories_estimated is not None:
        return {
            "calories": float(log.calories_estimated or 0),
            "protein": float(log.protein_estimated or 0),
            "fat": float(log.fat_estimated or 0),
            "carbs": float(log.carbs_estimated or 0),
        }

    cal, protein, fat, carbs = _estimate_nutrition(
        db,
        status="eaten",
        portion=float(log.portion_multiplier or 1.0),
        recipe_id=log.recipe_id,
    )
    return {
        "calories": float(cal or 0),
        "protein": float(protein or 0),
        "fat": float(fat or 0),
        "carbs": float(carbs or 0),
    }


def _filter_logs_for_user(
    logs: list[MealConsumptionLog],
    user_id: int,
) -> list[MealConsumptionLog]:
    return [log for log in logs if log.user_id == user_id]


def get_meal_consumption_nutrition_summary(
    db: Session,
    *,
    caller: User,
    scope: AppScope,
    family_id: int | None = None,
    menu_selection_id: int | None = None,
    day_index: int | None = None,
    planned_date: date | None = None,
) -> dict:
    if family_id is not None:
        membership = _caller_membership(db, caller)
        if membership is None or membership.family_id != family_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=FAMILY_ACCESS_DENIED,
            )

    plan_date_str = planned_date.isoformat() if planned_date else None
    day_plan = build_day_nutrition(db, caller.id, scope, plan_date_str)
    planned = _planned_from_day(day_plan)
    planned_meals = int(day_plan.get("coverage", {}).get("total_items", 0))

    logs = _filter_logs_for_user(
        get_meal_consumption_logs(
            db,
            caller=caller,
            family_id=family_id,
            menu_selection_id=menu_selection_id,
            day_index=day_index,
            planned_date=planned_date,
        ),
        caller.id,
    )

    has_logs = len(logs) > 0
    eaten = skipped = ate_out = 0
    actual_acc = {"calories": 0.0, "protein": 0.0, "fat": 0.0, "carbs": 0.0}

    for log in logs:
        status_val = log.status or "unknown"
        if status_val == "eaten":
            eaten += 1
            contrib = _nutrition_for_eaten_log(db, log)
            for key in actual_acc:
                actual_acc[key] += contrib[key]
        elif status_val == "skipped":
            skipped += 1
        elif status_val == "ate_out":
            ate_out += 1

    counts = {
        "planned_meals": planned_meals,
        "logged_meals": len(logs),
        "eaten": eaten,
        "skipped": skipped,
        "ate_out": ate_out,
    }

    return {
        "mode": "actual" if has_logs else "planned",
        "has_consumption_logs": has_logs,
        "planned": planned,
        "actual": _totals_dict(**actual_acc) if has_logs else None,
        "counts": counts,
        "targets": day_plan.get("targets"),
    }
