"""Cooking history service — recipe_history table."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum

from sqlalchemy.orm import Session

from app.config import settings
from app.models.recipe_engine import RecipeHistory
from app.models.user import User
from app.services.app_scope import AppScope
from app.services.recipes.repositories.history import RecipeHistoryRepository


class HistoryTypes(str, Enum):
    MANUAL = "manual"
    MENU = "menu"
    BOT = "bot"
    CHECKIN = "checkin"


@dataclass(frozen=True)
class CookingEvent:
    recipe_id: int
    cooked_on: date
    servings: int | None = None
    source: HistoryTypes = HistoryTypes.MANUAL
    notes: str | None = None
    user_id: int | None = None
    family_id: int | None = None
    family_member_id: int | None = None
    id: int | None = None


@dataclass(frozen=True)
class CookingStats:
    recipe_id: int
    cooked_count: int = 0
    last_cooked_on: date | None = None


class CookingHistoryService:
    def __init__(self, db: Session) -> None:
        self._db = db
        self._repo = RecipeHistoryRepository(db)

    def _scope_ids(
        self, user: User, scope: AppScope | None
    ) -> tuple[int | None, int | None]:
        user_id = user.id
        family_id = scope.family_id if scope is not None and scope.is_family else None
        return user_id, family_id

    def mark_cooked(
        self,
        *,
        event: CookingEvent,
        user: User,
        scope: AppScope | None = None,
    ) -> CookingEvent:
        if not settings.recipe_history:
            raise NotImplementedError("recipe_history feature flag is disabled")

        user_id, family_id = self._scope_ids(user, scope)
        row = RecipeHistory(
            recipe_id=event.recipe_id,
            user_id=event.user_id if event.user_id is not None else user_id,
            family_id=event.family_id if event.family_id is not None else family_id,
            family_member_id=event.family_member_id,
            servings=event.servings,
            cooked_on=event.cooked_on,
            source=event.source.value,
            notes=event.notes,
        )
        self._repo.add(row)
        self._db.commit()
        self._db.refresh(row)
        return CookingEvent(
            id=row.id,
            recipe_id=row.recipe_id,
            cooked_on=row.cooked_on,
            servings=row.servings,
            source=HistoryTypes(row.source),
            notes=row.notes,
            user_id=row.user_id,
            family_id=row.family_id,
            family_member_id=row.family_member_id,
        )

    def record_event(
        self,
        *,
        event: CookingEvent,
        user: User,
        scope: AppScope | None = None,
    ) -> None:
        self.mark_cooked(event=event, user=user, scope=scope)

    def get_stats(
        self,
        *,
        recipe_id: int,
        user: User,
        scope: AppScope | None = None,
    ) -> CookingStats:
        if not settings.recipe_history:
            return CookingStats(recipe_id=recipe_id)

        user_id, family_id = self._scope_ids(user, scope)
        count = self._repo.count_for_recipe(
            recipe_id, user_id=user_id, family_id=family_id
        )
        last = self._repo.last_cooked_on(
            recipe_id, user_id=user_id, family_id=family_id
        )
        return CookingStats(
            recipe_id=recipe_id, cooked_count=count, last_cooked_on=last
        )

    def list_events(
        self,
        *,
        recipe_id: int,
        user: User,
        scope: AppScope | None = None,
        limit: int = 10,
    ) -> list[CookingEvent]:
        if not settings.recipe_history:
            return []

        user_id, family_id = self._scope_ids(user, scope)
        rows = self._repo.list_for_recipe(
            recipe_id, user_id=user_id, family_id=family_id, limit=limit
        )
        return [
            CookingEvent(
                id=r.id,
                recipe_id=r.recipe_id,
                cooked_on=r.cooked_on,
                servings=r.servings,
                source=HistoryTypes(r.source),
                notes=r.notes,
                user_id=r.user_id,
                family_id=r.family_id,
                family_member_id=r.family_member_id,
            )
            for r in rows
        ]

    def list_scope_events(
        self,
        *,
        user: User,
        scope: AppScope | None = None,
        limit: int = 50,
    ) -> list[CookingEvent]:
        if not settings.recipe_history:
            return []

        user_id, family_id = self._scope_ids(user, scope)
        rows = self._repo.list_recent(
            user_id=user_id, family_id=family_id, limit=limit
        )
        return [
            CookingEvent(
                id=r.id,
                recipe_id=r.recipe_id,
                cooked_on=r.cooked_on,
                servings=r.servings,
                source=HistoryTypes(r.source),
                notes=r.notes,
                user_id=r.user_id,
                family_id=r.family_id,
                family_member_id=r.family_member_id,
            )
            for r in rows
        ]
