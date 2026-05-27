"""CRUD for family_recipe_preferences."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.recipe_engine import FamilyRecipePreference


class FamilyRecipePreferenceRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get_for_member(
        self, family_member_id: int, recipe_id: int
    ) -> FamilyRecipePreference | None:
        return (
            self._db.query(FamilyRecipePreference)
            .filter(
                FamilyRecipePreference.family_member_id == family_member_id,
                FamilyRecipePreference.recipe_id == recipe_id,
            )
            .one_or_none()
        )

    def list_for_recipe(
        self, recipe_id: int, family_id: int
    ) -> list[FamilyRecipePreference]:
        return (
            self._db.query(FamilyRecipePreference)
            .filter(
                FamilyRecipePreference.recipe_id == recipe_id,
                FamilyRecipePreference.family_id == family_id,
            )
            .all()
        )

    def list_for_family(self, family_id: int) -> list[FamilyRecipePreference]:
        return (
            self._db.query(FamilyRecipePreference)
            .filter(FamilyRecipePreference.family_id == family_id)
            .all()
        )

    def upsert(self, row: FamilyRecipePreference) -> FamilyRecipePreference:
        existing = self.get_for_member(row.family_member_id, row.recipe_id)
        if existing is not None:
            existing.liked = row.liked
            existing.disliked = row.disliked
            existing.is_loved = row.is_loved
            existing.note = row.note
            self._db.flush()
            return existing
        self._db.add(row)
        self._db.flush()
        return row

    def delete(self, row: FamilyRecipePreference) -> None:
        self._db.delete(row)
        self._db.flush()
