from sqlalchemy.orm import Session

from app.models.pantry import FamilyPantryItem
from app.services.app_scope import AppScope


def pantry_query(db: Session, scope: AppScope):
    query = db.query(FamilyPantryItem)
    if scope.is_family:
        return query.filter(FamilyPantryItem.family_id == scope.family_id)
    return query.filter(
        FamilyPantryItem.user_id == scope.user_id,
        FamilyPantryItem.family_id.is_(None),
    )
