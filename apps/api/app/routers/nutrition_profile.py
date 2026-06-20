from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from app.database import SessionLocal, get_db
from app.deps import get_verified_user
from app.models.user import User
from app.schemas.nutrition_profile import NutritionProfileData, NutritionProfileResponse
from app.services.nutrition_profile import (
    migrate_legacy_profile,
    notify_family_admins_profile_updated,
    profile_to_nutrition_schema,
    save_nutrition_profile,
)
from app.services import family as family_service
from app.nutrition.restrictions_catalog import list_restrictions_for_ui
from app.services.onboarding import get_or_create_profile

router = APIRouter(prefix="/nutrition-profile", tags=["nutrition-profile"])


async def _notify_admin_background(user_id: int) -> None:
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).one_or_none()
        if user is None:
            return
        await notify_family_admins_profile_updated(db, user)
    finally:
        db.close()


@router.get("/restrictions-catalog")
def get_restrictions_catalog() -> list[dict]:
    """Canonical restriction keys for onboarding/profile UI (read-only)."""
    return list_restrictions_for_ui()


@router.get("/me", response_model=NutritionProfileResponse)
def get_nutrition_profile(
    user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
) -> NutritionProfileResponse:
    profile = get_or_create_profile(db, user)
    migrate_legacy_profile(db, profile)
    data = profile_to_nutrition_schema(profile)
    return NutritionProfileResponse(**data.model_dump(), updated_at=profile.updated_at)


@router.put("/me", response_model=NutritionProfileResponse)
def save_nutrition_profile_endpoint(
    payload: NutritionProfileData,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
) -> NutritionProfileResponse:
    membership = family_service.get_user_membership(db, user)
    existing = get_or_create_profile(db, user)
    had_prior_profile = bool(existing.nutrition_goal)
    notify_admins = membership is not None and had_prior_profile

    profile = save_nutrition_profile(db, user, payload)
    data = profile_to_nutrition_schema(profile)

    if notify_admins:
        background_tasks.add_task(_notify_admin_background, user.id)

    return NutritionProfileResponse(**data.model_dump(), updated_at=profile.updated_at)
