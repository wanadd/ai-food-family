from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_app_scope, get_verified_user
from app.models.user import User
from app.services.app_scope import AppScope
from app.services import health_intelligence as health_service

router = APIRouter(prefix="/health-intelligence", tags=["health-intelligence"])


@router.get("/day")
def get_health_day_snapshot(
    family_id: int | None = Query(default=None),
    menu_selection_id: int | None = Query(default=None),
    day_index: int | None = Query(default=None),
    planned_date: date | None = Query(default=None),
    user: User = Depends(get_verified_user),
    scope: AppScope = Depends(get_app_scope),
    db: Session = Depends(get_db),
) -> dict:
    return health_service.compute_health_day_snapshot(
        db,
        caller=user,
        scope=scope,
        family_id=family_id,
        menu_selection_id=menu_selection_id,
        day_index=day_index,
        planned_date=planned_date,
    )
