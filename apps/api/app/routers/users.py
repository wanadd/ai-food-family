from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_verified_user
from app.models.user import User
from app.schemas.app_context import AppContextResponse, AppContextUpdate
from app.services import app_scope as app_scope_service
from app.services import family as family_service

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me/app-context", response_model=AppContextResponse)
def get_app_context(
    user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
) -> AppContextResponse:
    prefs = app_scope_service.get_or_create_preferences(db, user)
    family = family_service.get_my_family(db, user)
    has_family = family is not None
    mode = prefs.active_mode
    if mode == "family" and not has_family:
        mode = "personal"
        prefs.active_mode = "personal"
        db.commit()
    return AppContextResponse(
        active_mode=mode,  # type: ignore[arg-type]
        has_family=has_family,
        can_use_family_mode=has_family,
        family=family,
    )


@router.patch("/me/app-context", response_model=AppContextResponse)
def update_app_context(
    payload: AppContextUpdate,
    user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
) -> AppContextResponse:
    app_scope_service.set_active_mode(db, user, payload.active_mode)
    return get_app_context(user=user, db=db)
