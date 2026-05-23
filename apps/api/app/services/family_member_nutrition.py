from sqlalchemy.orm import Session

from app.models.family import FamilyMember
from app.models.user import User
from app.models.user_profile import UserProfile
from app.schemas.family_member_nutrition import VirtualNutritionProfile
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
    return VirtualNutritionProfile(
        age=raw.get("age"),
        nutrition_goal=raw.get("nutrition_goal"),
        allergies=raw.get("allergies") or [],
        restrictions=raw.get("restrictions") or [],
        diets=raw.get("diets") or [],
        favorite_foods=raw.get("favorite_foods") or "",
        disliked_foods=raw.get("disliked_foods") or "",
        notes=raw.get("notes") or "",
    )


def virtual_nutrition_complete(nutrition: VirtualNutritionProfile) -> bool:
    return bool(nutrition.nutrition_goal)


def apply_virtual_nutrition_to_member(
    member: FamilyMember, nutrition: VirtualNutritionProfile
) -> None:
    member.nutrition_profile = nutrition.model_dump()
    if nutrition.nutrition_goal:
        member.goals = NUTRITION_GOAL_TO_LEGACY_GOALS.get(
            nutrition.nutrition_goal, ["health"]
        )
    member.restrictions = list(
        dict.fromkeys(
            [
                *(nutrition.restrictions or []),
                *(nutrition.allergies or []),
            ]
        )
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
        if nutrition.nutrition_goal:
            return NUTRITION_GOAL_LABELS.get(
                nutrition.nutrition_goal, nutrition.nutrition_goal
            )
        return None

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
