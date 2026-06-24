"""API helpers for meal check-ins (enriched responses)."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.meal_checkin import MealCheckin
from app.models.user import User
from app.schemas.meal_checkin import MealCheckinResponse
from app.services import family as family_service
from app.services.app_scope import AppScope


def checkin_to_response(
    db: Session,
    user: User,
    scope: AppScope,
    row: MealCheckin,
) -> MealCheckinResponse:
    member_name: str | None = None
    if row.family_member_id and scope.is_family:
        family = family_service.get_family_for_user(db, user)
        if family:
            for m in family.members:
                if m.id == row.family_member_id:
                    member_name = m.display_name
                    break

    return MealCheckinResponse(
        id=row.id,
        meal_type=row.meal_type,
        planned_date=row.planned_date,
        actual_status=row.actual_status,
        actual_description=row.actual_description,
        leftover_servings_delta=row.leftover_servings_delta,
        recipe_id=row.recipe_id,
        family_member_id=row.family_member_id,
        member_name=member_name,
        created_at=row.created_at,
    )
