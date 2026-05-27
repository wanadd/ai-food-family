"""CRUD for recipe_history."""

from __future__ import annotations

from datetime import date

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.recipe_engine import RecipeHistory


class RecipeHistoryRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def add(self, row: RecipeHistory) -> RecipeHistory:
        self._db.add(row)
        self._db.flush()
        return row

    def list_for_recipe(
        self,
        recipe_id: int,
        *,
        user_id: int | None = None,
        family_id: int | None = None,
        limit: int = 50,
    ) -> list[RecipeHistory]:
        q = self._db.query(RecipeHistory).filter(RecipeHistory.recipe_id == recipe_id)
        if user_id is not None:
            q = q.filter(RecipeHistory.user_id == user_id)
        if family_id is not None:
            q = q.filter(RecipeHistory.family_id == family_id)
        return (
            q.order_by(RecipeHistory.cooked_on.desc(), RecipeHistory.id.desc())
            .limit(limit)
            .all()
        )

    def count_for_recipe(
        self,
        recipe_id: int,
        *,
        user_id: int | None = None,
        family_id: int | None = None,
    ) -> int:
        q = self._db.query(func.count(RecipeHistory.id)).filter(
            RecipeHistory.recipe_id == recipe_id
        )
        if user_id is not None:
            q = q.filter(RecipeHistory.user_id == user_id)
        if family_id is not None:
            q = q.filter(RecipeHistory.family_id == family_id)
        return int(q.scalar() or 0)

    def last_cooked_on(
        self,
        recipe_id: int,
        *,
        user_id: int | None = None,
        family_id: int | None = None,
    ) -> date | None:
        q = self._db.query(func.max(RecipeHistory.cooked_on)).filter(
            RecipeHistory.recipe_id == recipe_id
        )
        if user_id is not None:
            q = q.filter(RecipeHistory.user_id == user_id)
        if family_id is not None:
            q = q.filter(RecipeHistory.family_id == family_id)
        value = q.scalar()
        return value

    def list_recent(
        self,
        *,
        user_id: int | None = None,
        family_id: int | None = None,
        limit: int = 50,
    ) -> list[RecipeHistory]:
        q = self._db.query(RecipeHistory)
        if family_id is not None:
            q = q.filter(RecipeHistory.family_id == family_id)
        elif user_id is not None:
            q = q.filter(RecipeHistory.user_id == user_id)
        return (
            q.order_by(RecipeHistory.cooked_on.desc(), RecipeHistory.id.desc())
            .limit(limit)
            .all()
        )
