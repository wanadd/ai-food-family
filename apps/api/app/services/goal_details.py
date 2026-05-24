from fastapi import HTTPException, status

from app.models.user_profile import UserProfile
from app.schemas.goal_details import NutritionGoalDetails
from app.schemas.nutrition_profile import NutritionProfileData


def goal_details_from_profile(profile: UserProfile) -> NutritionGoalDetails:
    raw = profile.goal_details if isinstance(profile.goal_details, dict) else {}
    if not raw and profile.weight_kg:
        raw = {"current_weight_kg": profile.weight_kg}
    return NutritionGoalDetails.model_validate(raw or {})


def validate_measurable_goal(payload: NutritionProfileData) -> None:
    goal = payload.nutrition_goal
    d = payload.goal_details
    if not goal:
        return
    cw = d.current_weight_kg or payload.weight_kg
    if goal in ("lose", "gain"):
        if cw is None or d.target_weight_kg is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Укажите текущий и целевой вес",
            )
        if not d.target_date and not d.goal_pace:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Укажите срок или темп достижения цели",
            )
    if goal == "maintain" and cw is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Укажите текущий вес",
        )


def format_measurable_goal_summary(profile: UserProfile) -> str | None:
    goal = profile.nutrition_goal
    if not goal:
        return None
    d = goal_details_from_profile(profile)
    from app.services.nutrition_profile_labels import NUTRITION_GOAL_LABELS

    label = NUTRITION_GOAL_LABELS.get(goal, goal)
    cw = d.current_weight_kg or profile.weight_kg
    if goal == "lose" and cw and d.target_weight_kg:
        pace = d.goal_pace or "стандартный"
        left = max(0.0, float(cw) - float(d.target_weight_kg))
        return (
            f"{label}: с {cw} кг до {d.target_weight_kg} кг "
            f"(осталось {left:.1f} кг, темп {pace})"
        )
    if goal == "gain" and cw and d.target_weight_kg:
        return f"{label}: с {cw} кг до {d.target_weight_kg} кг"
    if goal == "maintain" and cw:
        if d.target_weight_min_kg and d.target_weight_max_kg:
            return (
                f"{label}: {cw} кг, диапазон "
                f"{d.target_weight_min_kg}–{d.target_weight_max_kg} кг"
            )
        return f"{label}: {cw} кг"
    return label
