import logging

from sqlalchemy.orm import Session

from app.models.family import FamilyRole
from app.models.user import User
from app.models.user_profile import UserProfile
from app.schemas.goal_details import NutritionGoalDetails
from app.schemas.nutrition_profile import NutritionProfileData, NutritionProData
from app.services.goal_details import goal_details_from_profile, validate_measurable_goal
from app.services import family as family_service
from app.nutrition.restrictions_catalog import normalize_restrictions
from app.services.normalization.profile import normalize_profile_payload
from app.services.nutrition_profile_labels import NUTRITION_GOAL_TO_LEGACY_GOALS
from app.services.onboarding import get_or_create_profile

logger = logging.getLogger(__name__)


def _pro_from_db(raw: dict | None) -> NutritionProData:
    if not raw:
        return NutritionProData()
    return NutritionProData(
        workouts_enabled=bool(raw.get("workouts_enabled")),
        workout_goal=str(raw.get("workout_goal") or ""),
        workout_frequency=raw.get("workout_frequency"),
        body_measurements=str(raw.get("body_measurements") or ""),
        water_liters=raw.get("water_liters"),
        track_macros=bool(raw.get("track_macros")),
    )


def is_profile_complete(profile: UserProfile) -> bool:
    return bool(profile.nutrition_goal)


def migrate_legacy_profile(db: Session, profile: UserProfile) -> bool:
    """Map old onboarding fields into nutrition profile on first open."""
    changed = False
    if not profile.nutrition_goal and profile.goals:
        goals = profile.goals or []
        if "weight" in goals:
            profile.nutrition_goal = "lose"
        elif "budget" in goals:
            profile.nutrition_goal = "maintain"
        else:
            profile.nutrition_goal = "healthy"
        changed = True
    if not profile.activity_level and profile.completed:
        profile.activity_level = "medium"
        changed = True
    if changed:
        sync_legacy_menu_fields(profile)
        db.commit()
        db.refresh(profile)
    return changed


def profile_to_nutrition_schema(profile: UserProfile) -> NutritionProfileData:
    return NutritionProfileData(
        age=profile.age,
        gender=profile.gender,
        height_cm=profile.height_cm,
        weight_kg=profile.weight_kg,
        nutrition_goal=profile.nutrition_goal,
        activity_level=profile.activity_level,
        allergies=profile.allergies or [],
        restrictions=normalize_restrictions(profile.restrictions or []),
        medical_restrictions=profile.medical_restrictions or "",
        banned_foods=profile.banned_foods or "",
        diets=profile.diets or [],
        favorite_foods=profile.favorite_foods or "",
        disliked_foods=profile.disliked_foods or "",
        budget=profile.budget,
        cooking_time=profile.cooking_time,
        dish_complexity=profile.dish_complexity,
        pro=_pro_from_db(profile.pro_data),
        goal_details=goal_details_from_profile(profile),
        completed=is_profile_complete(profile),
    )


def sync_legacy_menu_fields(profile: UserProfile) -> None:
    """Keep onboarding/menu fields aligned with nutrition profile."""
    if profile.nutrition_goal:
        profile.goals = NUTRITION_GOAL_TO_LEGACY_GOALS.get(
            profile.nutrition_goal, ["health"]
        )
    profile.completed = is_profile_complete(profile)
    if profile.completed:
        profile.current_step = 8


def save_nutrition_profile(
    db: Session, user: User, payload: NutritionProfileData
) -> UserProfile:
    # Unified profile write-path normalization: trim text, dedupe allergies/diets.
    payload = normalize_profile_payload(payload)
    validate_measurable_goal(payload)
    profile = get_or_create_profile(db, user)
    profile.age = payload.age
    profile.gender = payload.gender
    profile.height_cm = payload.height_cm
    profile.weight_kg = payload.weight_kg
    profile.nutrition_goal = payload.nutrition_goal
    profile.activity_level = payload.activity_level
    profile.allergies = payload.allergies
    profile.restrictions = normalize_restrictions(payload.restrictions)
    profile.medical_restrictions = payload.medical_restrictions
    profile.banned_foods = payload.banned_foods
    profile.diets = payload.diets
    profile.favorite_foods = payload.favorite_foods
    profile.disliked_foods = payload.disliked_foods
    profile.budget = payload.budget
    profile.cooking_time = payload.cooking_time
    profile.dish_complexity = payload.dish_complexity
    profile.pro_data = payload.pro.model_dump()
    profile.goal_details = payload.goal_details.model_dump(exclude_none=True)
    if payload.goal_details.current_weight_kg is not None:
        profile.weight_kg = payload.goal_details.current_weight_kg
    sync_legacy_menu_fields(profile)
    db.commit()
    db.refresh(profile)
    return profile


def should_notify_family_admin(user: User, membership) -> bool:
    if membership is None:
        return False
    return membership.role != FamilyRole.ADMIN.value


async def notify_family_admins_profile_updated(db: Session, user: User) -> None:
    from app.services.telegram_bot import send_telegram_message

    membership = family_service.get_user_membership(db, user)
    if membership is None:
        return

    family = membership.family
    display = (user.first_name or "").strip() or membership.display_name or "Участник"
    text = (
        f"🥗 {display} обновил(а) профиль питания в семье «{family.name}».\n\n"
        "Откройте ПланАм — меню и покупки учтут новые предпочтения."
    )

    notified: set[int] = set()
    for admin_member in family.members:
        if admin_member.role != FamilyRole.ADMIN.value or not admin_member.user_id:
            continue
        if admin_member.user_id == user.id:
            continue
        admin_user = (
            db.query(User).filter(User.id == admin_member.user_id).one_or_none()
        )
        if admin_user is None or not admin_user.telegram_id:
            continue
        if admin_user.telegram_id in notified:
            continue
        notified.add(admin_user.telegram_id)
        await send_telegram_message(admin_user.telegram_id, text)
