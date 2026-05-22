from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_verified_user
from app.models.user import User
from app.schemas.onboarding import OnboardingData, OnboardingResponse
from app.services.onboarding import get_or_create_profile, profile_to_schema, save_profile

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


@router.get("/me", response_model=OnboardingResponse)
def get_onboarding(
    user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
) -> OnboardingResponse:
    profile = get_or_create_profile(db, user)
    data = profile_to_schema(profile)
    return OnboardingResponse(**data.model_dump(), updated_at=profile.updated_at)


@router.put("/me", response_model=OnboardingResponse)
def save_onboarding(
    payload: OnboardingData,
    user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
) -> OnboardingResponse:
    profile = save_profile(db, user, payload)
    data = profile_to_schema(profile)
    return OnboardingResponse(**data.model_dump(), updated_at=profile.updated_at)
