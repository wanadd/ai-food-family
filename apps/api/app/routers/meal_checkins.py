from datetime import date

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_verified_user
from app.models.user import User
from app.schemas.meal_checkin import MealCheckinCreate, MealCheckinResponse
from app.services.app_scope import resolve_scope
from app.services.meal_attendance import create_meal_checkin
from app.services.meal_leftovers import create_leftover
from app.schemas.meal_leftover import MealLeftoverCreate

router = APIRouter(prefix="/meal-checkins", tags=["meal-checkins"])


@router.post("", response_model=MealCheckinResponse, status_code=status.HTTP_201_CREATED)
def post_meal_checkin(
    payload: MealCheckinCreate,
    user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
) -> MealCheckinResponse:
    scope = resolve_scope(db, user)
    row = create_meal_checkin(
        db,
        user,
        scope,
        meal_type=payload.meal_type,
        actual_status=payload.actual_status,
        planned_date=payload.planned_date or date.today(),
        family_member_id=payload.family_member_id,
        actual_description=payload.actual_description,
        leftover_servings_delta=payload.leftover_servings_delta,
    )
    if (
        payload.actual_status == "saved_as_leftover"
        and payload.leftover_servings_delta
        and payload.leftover_servings_delta > 0
    ):
        status_val = payload.leftover_status or "active"
        create_leftover(
            db,
            user,
            scope,
            MealLeftoverCreate(
                dish_name=payload.actual_description or f"Остаток ({payload.meal_type})",
                portions_remaining=payload.leftover_servings_delta,
            ),
        )
        from app.models.meal_leftover import MealLeftover

        latest = (
            db.query(MealLeftover)
            .filter(MealLeftover.added_by_user_id == user.id)
            .order_by(MealLeftover.id.desc())
            .first()
        )
        if latest:
            latest.leftover_status = status_val
            db.commit()

    return MealCheckinResponse(
        id=row.id,
        meal_type=row.meal_type,
        planned_date=row.planned_date,
        actual_status=row.actual_status,
        actual_description=row.actual_description,
        leftover_servings_delta=row.leftover_servings_delta,
        created_at=row.created_at,
    )
