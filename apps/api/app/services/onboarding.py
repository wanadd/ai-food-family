from sqlalchemy.orm import Session

from app.models.user import User
from app.models.user_profile import UserProfile
from app.schemas.onboarding import OnboardingData


def get_or_create_profile(db: Session, user: User) -> UserProfile:
    profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).one_or_none()
    if profile is None:
        profile = UserProfile(user_id=user.id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


def profile_to_schema(profile: UserProfile) -> OnboardingData:
    return OnboardingData(
        current_step=profile.current_step,
        completed=profile.completed,
        goals=profile.goals or [],
        diets=profile.diets or [],
        allergies=profile.allergies or [],
        restrictions=profile.restrictions or [],
        favorite_foods=profile.favorite_foods or "",
        disliked_foods=profile.disliked_foods or "",
        budget=profile.budget,
        cooking_time=profile.cooking_time,
    )


def save_profile(db: Session, user: User, payload: OnboardingData) -> UserProfile:
    profile = get_or_create_profile(db, user)
    profile.current_step = payload.current_step
    profile.completed = payload.completed
    profile.goals = payload.goals
    profile.diets = payload.diets
    profile.allergies = payload.allergies
    profile.restrictions = payload.restrictions
    profile.favorite_foods = payload.favorite_foods
    profile.disliked_foods = payload.disliked_foods
    profile.budget = payload.budget
    profile.cooking_time = payload.cooking_time
    db.commit()
    db.refresh(profile)
    return profile
