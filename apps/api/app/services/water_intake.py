from datetime import date

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.water_intake import WaterIntakeLog
from app.schemas.water_intake import WaterIntakeCreate, WaterIntakeTodayResponse
from app.services.app_scope import AppScope
from app.services.progress import get_nutrition_targets


def add_water(
    db: Session, user: User, scope: AppScope, payload: WaterIntakeCreate
) -> WaterIntakeTodayResponse:
    today = date.today()
    row = WaterIntakeLog(
        user_id=user.id,
        family_id=scope.family_id if scope.is_family else None,
        log_date=today,
        amount_ml=payload.amount_ml,
    )
    db.add(row)
    db.commit()
    return get_today_total(db, user, scope)


def get_today_total(
    db: Session, user: User, scope: AppScope
) -> WaterIntakeTodayResponse:
    today = date.today()
    q = db.query(func.coalesce(func.sum(WaterIntakeLog.amount_ml), 0)).filter(
        WaterIntakeLog.user_id == user.id,
        WaterIntakeLog.log_date == today,
    )
    if scope.is_family and scope.family_id:
        q = q.filter(WaterIntakeLog.family_id == scope.family_id)
    else:
        q = q.filter(WaterIntakeLog.family_id.is_(None))
    total = int(q.scalar() or 0)
    targets = get_nutrition_targets(db, user, scope)
    return WaterIntakeTodayResponse(
        total_ml=total,
        target_ml=targets.water_target_ml if targets else None,
    )


def sum_water_for_date(db: Session, user: User, scope: AppScope, on_date: date) -> int:
    q = db.query(func.coalesce(func.sum(WaterIntakeLog.amount_ml), 0)).filter(
        WaterIntakeLog.user_id == user.id,
        WaterIntakeLog.log_date == on_date,
    )
    if scope.is_family and scope.family_id:
        q = q.filter(WaterIntakeLog.family_id == scope.family_id)
    else:
        q = q.filter(WaterIntakeLog.family_id.is_(None))
    return int(q.scalar() or 0)
