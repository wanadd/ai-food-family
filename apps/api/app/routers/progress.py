from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_app_scope, get_verified_user
from app.models.user import User
from app.schemas.progress import (
    ProgressEntryCreate,
    ProgressEntryResponse,
    ProgressOverviewResponse,
    ProgressSettingsUpdate,
    NutritionTargetsResponse,
    NutritionTargetsUpdate,
    TrainingEntryCreate,
    TrainingEntryResponse,
)
from app.services.app_scope import AppScope
from app.services import progress as progress_service

router = APIRouter(prefix="/progress", tags=["progress"])


@router.get("/me", response_model=ProgressOverviewResponse)
def get_my_progress(
    user: User = Depends(get_verified_user),
    scope: AppScope = Depends(get_app_scope),
    db: Session = Depends(get_db),
) -> ProgressOverviewResponse:
    return progress_service.get_progress_overview(db, user, scope)


@router.post("/me", response_model=ProgressEntryResponse)
def add_progress_entry(
    payload: ProgressEntryCreate,
    user: User = Depends(get_verified_user),
    scope: AppScope = Depends(get_app_scope),
    db: Session = Depends(get_db),
) -> ProgressEntryResponse:
    return progress_service.create_progress_entry(db, user, scope, payload)


@router.get("/history", response_model=list[ProgressEntryResponse])
def progress_history(
    user: User = Depends(get_verified_user),
    scope: AppScope = Depends(get_app_scope),
    db: Session = Depends(get_db),
) -> list[ProgressEntryResponse]:
    return progress_service.get_progress_history(db, user, scope)


@router.post("/training", response_model=TrainingEntryResponse)
def add_training_entry(
    payload: TrainingEntryCreate,
    user: User = Depends(get_verified_user),
    scope: AppScope = Depends(get_app_scope),
    db: Session = Depends(get_db),
) -> TrainingEntryResponse:
    return progress_service.create_training_entry(db, user, scope, payload)


@router.get("/training", response_model=list[TrainingEntryResponse])
def training_history(
    user: User = Depends(get_verified_user),
    scope: AppScope = Depends(get_app_scope),
    db: Session = Depends(get_db),
) -> list[TrainingEntryResponse]:
    return progress_service.get_training_history(db, user, scope)


@router.get("/targets", response_model=NutritionTargetsResponse)
def get_targets(
    user: User = Depends(get_verified_user),
    scope: AppScope = Depends(get_app_scope),
    db: Session = Depends(get_db),
) -> NutritionTargetsResponse:
    progress_service.require_pro(db, user)
    return progress_service.get_nutrition_targets(db, user, scope)


@router.patch("/targets", response_model=NutritionTargetsResponse)
def patch_targets(
    payload: NutritionTargetsUpdate,
    user: User = Depends(get_verified_user),
    scope: AppScope = Depends(get_app_scope),
    db: Session = Depends(get_db),
) -> NutritionTargetsResponse:
    return progress_service.update_nutrition_targets(db, user, scope, payload)


@router.patch("/settings")
def patch_progress_settings(
    payload: ProgressSettingsUpdate,
    user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
) -> dict[str, bool]:
    progress_service.require_pro(db, user)
    from app.services.onboarding import get_or_create_profile

    profile = get_or_create_profile(db, user)
    if payload.show_progress_to_family is None:
        return {
            "show_progress_to_family": progress_service.get_show_progress_to_family(
                profile
            ),
        }
    value = progress_service.set_show_progress_to_family(
        db, user, payload.show_progress_to_family
    )
    return {"show_progress_to_family": value}
