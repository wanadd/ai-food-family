from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.family import FamilyMember
from app.models.user import User
from app.models.user_profile import UserProfile
from app.schemas.family_member_nutrition import VirtualNutritionProfile
from app.services.member_age import format_age_short_ru, normalize_age_months
from app.services.normalization.profile import normalize_member_nutrition
from app.services.nutrition_profile import is_profile_complete
from app.services.nutrition_profile_labels import (
    NUTRITION_GOAL_LABELS,
    NUTRITION_GOAL_TO_LEGACY_GOALS,
)
from app.services.onboarding import get_or_create_profile


def member_is_virtual(member: FamilyMember) -> bool:
    return member.is_virtual or member.user_id is None


def virtual_nutrition_from_member(member: FamilyMember) -> VirtualNutritionProfile:
    raw = member.nutrition_profile or {}
    allergies = list(raw.get("allergies") or [])
    custom_allergies = list(raw.get("custom_allergies") or [])
    restrictions = list(raw.get("restrictions") or [])
    custom_restrictions = list(raw.get("custom_restrictions") or [])

    age_months = normalize_age_months(
        age_months=raw.get("age_months"),
        age_years=raw.get("age_years"),
        age=raw.get("age"),
    )

    return VirtualNutritionProfile(
        age_months=age_months,
        nutrition_goal=raw.get("nutrition_goal"),
        custom_nutrition_goal=raw.get("custom_nutrition_goal"),
        allergies=allergies,
        custom_allergies=custom_allergies,
        restrictions=restrictions,
        custom_restrictions=custom_restrictions,
        favorite_foods=raw.get("favorite_foods") or "",
        disliked_foods=raw.get("disliked_foods") or "",
        notes=raw.get("notes") or "",
        age=raw.get("age"),
        age_years=raw.get("age_years"),
        diets=raw.get("diets") or [],
    )


def virtual_nutrition_complete(nutrition: VirtualNutritionProfile) -> bool:
    if nutrition.age_months is None:
        return False
    if nutrition.nutrition_goal == "other":
        return bool((nutrition.custom_nutrition_goal or "").strip())
    return bool(nutrition.nutrition_goal)


def apply_virtual_nutrition_to_member(
    member: FamilyMember, nutrition: VirtualNutritionProfile
) -> None:
    if nutrition.age_months is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Укажите возраст участника",
        )

    goal = nutrition.nutrition_goal
    if goal == "other" and not (nutrition.custom_nutrition_goal or "").strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Укажите свою цель питания",
        )
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Выберите цель питания",
        )

    stored = nutrition.model_dump(exclude={"age", "age_years", "diets"})
    stored["age_months"] = nutrition.age_months
    stored["age"] = nutrition.age_months // 12 if nutrition.age_months else None

    # Unified normalization: dedupe allergies/restrictions, trim notes.
    member.nutrition_profile = normalize_member_nutrition(stored)
    if goal and goal != "other":
        member.goals = NUTRITION_GOAL_TO_LEGACY_GOALS.get(goal, ["health"])
    else:
        member.goals = ["health"]

    all_restrictions = list(
        dict.fromkeys(
            [
                *(nutrition.restrictions or []),
                *(nutrition.custom_restrictions or []),
                *(nutrition.allergies or []),
                *(nutrition.custom_allergies or []),
            ]
        )
    )
    member.restrictions = all_restrictions


def nutrition_goal_display(nutrition: VirtualNutritionProfile) -> str | None:
    if not nutrition.nutrition_goal:
        return None
    if nutrition.nutrition_goal == "other":
        return (nutrition.custom_nutrition_goal or "Другое").strip()
    return NUTRITION_GOAL_LABELS.get(
        nutrition.nutrition_goal, nutrition.nutrition_goal
    )


def telegram_member_nutrition_complete(db: Session, member: FamilyMember) -> bool:
    if member.user_id is None:
        return False
    profile = (
        db.query(UserProfile)
        .filter(UserProfile.user_id == member.user_id)
        .one_or_none()
    )
    if profile is None:
        return False
    return is_profile_complete(profile)


def nutrition_goal_label_for_member(
    db: Session, member: FamilyMember
) -> str | None:
    if member_is_virtual(member):
        nutrition = virtual_nutrition_from_member(member)
        return nutrition_goal_display(nutrition)

    if member.user_id is None:
        return None
    profile = get_or_create_profile(
        db, db.query(User).filter(User.id == member.user_id).one()
    )
    if profile.nutrition_goal:
        return NUTRITION_GOAL_LABELS.get(
            profile.nutrition_goal, profile.nutrition_goal
        )
    return None


def member_age_label(member: FamilyMember) -> str | None:
    if not member_is_virtual(member):
        return None
    nutrition = virtual_nutrition_from_member(member)
    return format_age_short_ru(nutrition.age_months)


def nutrition_summary_for_telegram_member(
    db: Session, member: FamilyMember
) -> dict[str, str | int | bool | None]:
    if member.user_id is None:
        return {}
    user = db.query(User).filter(User.id == member.user_id).one_or_none()
    if user is None:
        return {}
    profile = get_or_create_profile(db, user)
    return {
        "nutrition_goal": profile.nutrition_goal,
        "nutrition_goal_label": NUTRITION_GOAL_LABELS.get(
            profile.nutrition_goal, profile.nutrition_goal
        )
        if profile.nutrition_goal
        else None,
        "age": profile.age,
        "allergies_count": len([a for a in (profile.allergies or []) if a != "none"]),
        "diets_count": len([d for d in (profile.diets or []) if d != "none"]),
        "profile_complete": is_profile_complete(profile),
    }
