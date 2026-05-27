"""Cooking history foundation (Sprint 5).

Sprint 5 constraint:
  - No DB changes.
  - No UI.
  - Only introduce models + service interfaces so subsequent commits
    can wire existing cooking events and feed explainability/scoring.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum

from sqlalchemy.orm import Session

from app.config import settings
from app.models.user import User
from app.services.app_scope import AppScope


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

    # Scope identifiers (left optional until DB schema is introduced).
    user_id: int | None = None
    family_id: int | None = None
    family_member_id: int | None = None


@dataclass(frozen=True)
class CookingStats:
    recipe_id: int
    cooked_count: int = 0
    last_cooked_on: date | None = None


class CookingHistoryService:
    """Service interface for cooking history.

    Sprint 5 behaviour: stub / neutral implementation.
    """

    def __init__(self, db: Session) -> None:
        self._db = db

    def record_event(
        self,
        *,
        event: CookingEvent,
        user: User,
        scope: AppScope | None = None,
    ) -> None:
        _ = (event, user, scope)
        if not settings.recipe_history:
            raise NotImplementedError(
                "Cooking history is disabled (recipe_history feature flag)."
            )
        raise NotImplementedError(
            "Cooking history write is reserved for Sprint 6+ when DB wiring is introduced."
        )

    def get_stats(
        self,
        *,
        recipe_id: int,
        user: User,
        scope: AppScope | None = None,
    ) -> CookingStats:
        _ = (recipe_id, user, scope)
        return CookingStats(recipe_id=recipe_id)

    def list_events(
        self,
        *,
        recipe_id: int,
        user: User,
        scope: AppScope | None = None,
        limit: int = 10,
    ) -> list[CookingEvent]:
        _ = (recipe_id, user, scope, limit)
        return []

