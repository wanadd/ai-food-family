from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_verified_user
from app.models.user import User
from app.schemas.meal_consumption import (
    MealConsumptionBulkIn,
    MealConsumptionBulkOut,
    MealConsumptionListOut,
)
from app.services.meal_consumption import (
    get_meal_consumption_logs,
    logs_to_entries,
    save_meal_consumption_logs,
)

router = APIRouter(prefix="/meal-consumption", tags=["meal-consumption"])


@router.get("", response_model=MealConsumptionListOut)
def list_meal_consumption(
    family_id: int = Query(...),
    menu_selection_id: int | None = Query(default=None),
    day_index: int | None = Query(default=None),
    planned_date: date | None = Query(default=None),
    user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
) -> MealConsumptionListOut:
    rows = get_meal_consumption_logs(
        db,
        caller=user,
        family_id=family_id,
        menu_selection_id=menu_selection_id,
        day_index=day_index,
        planned_date=planned_date,
    )
    return MealConsumptionListOut(entries=logs_to_entries(rows))


@router.post("/bulk", response_model=MealConsumptionBulkOut)
def bulk_save_meal_consumption(
    payload: MealConsumptionBulkIn,
    user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
) -> MealConsumptionBulkOut:
    rows = save_meal_consumption_logs(db, caller=user, payload=payload)
    entries = logs_to_entries(rows)
    return MealConsumptionBulkOut(saved=len(entries), entries=entries)
