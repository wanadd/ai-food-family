"""Explainability foundation for recipe recommendations (Sprint 3).

Sprint 3 scope:
  - Define reason codes as an enum ``RecommendationReason``.
  - Provide DTO-like dataclasses for ``ExplainabilityResult``.
  - Introduce ``ExplainabilityService`` to build an explanation.

No new API routes are added in this sprint (per task constraints).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Literal

from sqlalchemy.orm import Session

from app.config import settings
from app.models.user import User
from app.services.app_scope import AppScope


class RecommendationReason(str, Enum):
    IN_PANTRY = "in_pantry"
    KIDS_LIKE = "kids_like"
    GOAL_MATCH = "goal_match"
    QUICK_COOKING = "quick_cooking"
    BUDGET_FRIENDLY = "budget_friendly"
    HIGH_PROTEIN = "high_protein"
    LOW_CALORIE = "low_calorie"
    FAMILY_APPROVED = "family_approved"


ReasonKind = Literal["positive", "warning", "hard_block"]


@dataclass(frozen=True)
class RecommendationReasonEntry:
    reason: RecommendationReason
    kind: ReasonKind = "positive"
    label: str = ""
    icon: str = ""
    weight: float = 0.0


@dataclass(frozen=True)
class ExplainabilityResult:
    recipe_id: int
    summary: str
    positives: tuple[RecommendationReasonEntry, ...] = field(default_factory=tuple)
    warnings: tuple[RecommendationReasonEntry, ...] = field(default_factory=tuple)
    hard_blocks: tuple[RecommendationReasonEntry, ...] = field(default_factory=tuple)
    score_total: float = 0.0


class ExplainabilityService:
    """Build an explanation for a given recipe.

    Sprint 3 behaviour: return a neutral placeholder explanation.
    Subsequent commits will wire in fact collectors and map each scoring
    contribution into the corresponding ``RecommendationReason`` entry.
    """

    NEUTRAL_SUMMARY = "Подходит по каталогу"

    def __init__(self, db: Session) -> None:
        self._db = db

    def explain(
        self,
        recipe_id: int,
        *,
        user: User,
        scope: AppScope | None = None,
    ) -> ExplainabilityResult:
        if not settings.recipe_explainability:
            _ = (user, scope)
            return ExplainabilityResult(
                recipe_id=recipe_id,
                summary=self.NEUTRAL_SUMMARY,
            )

        _ = (user, scope)
        return ExplainabilityResult(recipe_id=recipe_id, summary=self.NEUTRAL_SUMMARY)

