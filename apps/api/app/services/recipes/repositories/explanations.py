"""CRUD for recipe_explanations."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.recipe_engine import RecipeExplanation


class RecipeExplanationRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get(
        self,
        recipe_id: int,
        user_id: int,
        *,
        family_id: int | None = None,
    ) -> RecipeExplanation | None:
        return (
            self._db.query(RecipeExplanation)
            .filter(
                RecipeExplanation.recipe_id == recipe_id,
                RecipeExplanation.user_id == user_id,
                RecipeExplanation.family_id == family_id,
            )
            .one_or_none()
        )

    def upsert(self, row: RecipeExplanation) -> RecipeExplanation:
        existing = self.get(
            row.recipe_id, row.user_id, family_id=row.family_id
        )
        if existing is not None:
            existing.summary = row.summary
            existing.reasons_json = row.reasons_json
            existing.score_total = row.score_total
            self._db.flush()
            return existing
        self._db.add(row)
        self._db.flush()
        return row

    def delete(
        self,
        recipe_id: int,
        user_id: int,
        *,
        family_id: int | None = None,
    ) -> bool:
        row = self.get(recipe_id, user_id, family_id=family_id)
        if row is None:
            return False
        self._db.delete(row)
        self._db.flush()
        return True
