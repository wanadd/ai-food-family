from datetime import date

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_app_scope, get_verified_user
from app.models.user import User
from app.schemas.meal_checkin import MealCheckinCreate, MealCheckinResponse
from app.services.app_scope import AppScope, resolve_scope
from app.services.meal_attendance import upsert_meal_checkin
from app.services.meal_checkin_api import checkin_to_response
from app.services.meal_daily_nutrition import list_checkins_for_date
from app.services.meal_nutrition import resolve_meal_nutrition
from app.services.menu_selection import get_selected_menu
from app.services.meal_leftovers import create_leftover
from app.schemas.meal_leftover import MealLeftoverCreate

router = APIRouter(prefix="/meal-checkins", tags=["meal-checkins"])


@router.get("/today", response_model=list[MealCheckinResponse])
def list_today_meal_checkins(
    user: User = Depends(get_verified_user),
    scope: AppScope = Depends(get_app_scope),
    db: Session = Depends(get_db),
    on_date: date | None = Query(default=None),
) -> list[MealCheckinResponse]:
    rows = list_checkins_for_date(db, scope, on_date or date.today())
    return [checkin_to_response(db, user, scope, row) for row in rows]


@router.post("", response_model=MealCheckinResponse, status_code=status.HTTP_201_CREATED)
def post_meal_checkin(
    payload: MealCheckinCreate,
    user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
) -> MealCheckinResponse:
    scope = resolve_scope(db, user)
    selected = get_selected_menu(db, scope)
    menu = selected.menu if selected else None
    planned = payload.planned_date or date.today()
    cal, protein, fat, carbs = resolve_meal_nutrition(
        db,
        meal_type=payload.meal_type,
        actual_status=payload.actual_status,
        menu=menu,
        recipe_id=payload.recipe_id,
        planned_date=planned,
    )
    row = upsert_meal_checkin(
        db,
        user,
        scope,
        meal_type=payload.meal_type,
        actual_status=payload.actual_status,
        planned_date=planned,
        family_member_id=payload.family_member_id,
        actual_description=payload.actual_description,
        leftover_servings_delta=payload.leftover_servings_delta,
        actual_calories=cal,
        actual_protein_g=protein,
        actual_fat_g=fat,
        actual_carbs_g=carbs,
        recipe_id=payload.recipe_id,
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

    return checkin_to_response(db, user, scope, row)
