"""Scenario framework foundation (Sprint 7).

Sprint 7 constraint:
  - No UI.
  - No DB changes.
  - Only introduce types + matcher + service interfaces.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from sqlalchemy.orm import Session

from app.models.user import User
from app.services.app_scope import AppScope


class ScenarioType(str, Enum):
    QUICK = "quick"
    ULTRA_QUICK = "ultra_quick"
    CHEAP = "cheap"
    KIDS_LIKED = "kids_loved"  # keep exact code from task
    LOSE_WEIGHT = "lose_weight"
    GAIN_WEIGHT = "gain_weight"
    GUESTS = "guests"
    HOLIDAY = "holiday"
    WORK_LUNCH = "work_lunch"
    TRAVEL = "travel"
    FROM_PANTRY = "from_pantry"
    ALMOST_NO_COOKING = "almost_no_cooking"


@dataclass(frozen=True)
class ScenarioMatchResult:
    scenario: ScenarioType
    matched: bool = False
    note: str | None = None


class ScenarioMatcher:
    """Matches recipes against scenarios (stub in Sprint 7)."""

    def match(
        self,
        *,
        scenario: ScenarioType,
        recipe_id: int,
        user: User,
        scope: AppScope | None = None,
    ) -> ScenarioMatchResult:
        _ = (recipe_id, user, scope)
        return ScenarioMatchResult(scenario=scenario, matched=False)


class ScenarioService:
    """Scenario orchestration (stub in Sprint 7)."""

    def __init__(self, db: Session, matcher: ScenarioMatcher | None = None) -> None:
        self._db = db
        self._matcher = matcher or ScenarioMatcher()

    def match_any(
        self,
        *,
        recipe_id: int,
        scenarios: list[ScenarioType],
        user: User,
        scope: AppScope | None = None,
    ) -> list[ScenarioMatchResult]:
        _ = self._db
        return [
            self._matcher.match(
                scenario=sc,
                recipe_id=recipe_id,
                user=user,
                scope=scope,
            )
            for sc in scenarios
        ]

