"""Family preference foundation (Sprint 6).

Sprint 6 constraint:
  - No DB changes.
  - No new API routes.
  - Only introduce models + service interface for family-aware scoring.

Weights requested by task:
  - loved = +3
  - liked = +1
  - disliked = -2

Hard exclude reasons (only these three categories):
  - allergy
  - medical restriction
  - religious restriction
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from sqlalchemy.orm import Session

from app.models.user import User
from app.services.app_scope import AppScope


LOVED_WEIGHT = 3.0
LIKED_WEIGHT = 1.0
DISLIKED_WEIGHT = -2.0


class HardExcludeReason(str, Enum):
    ALLERGY = "allergy"
    MEDICAL_RESTRICTION = "medical_restriction"
    RELIGIOUS_RESTRICTION = "religious_restriction"


@dataclass(frozen=True)
class FamilyPreferenceScore:
    total: float = 0.0
    liked_delta: float = 0.0
    disliked_delta: float = 0.0
    loved_delta: float = 0.0
    # Reserved for per-member breakdown in Sprint 6.1+.
    per_member_breakdown: tuple[float, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class FamilyCompatibilityResult:
    recipe_id: int
    score: FamilyPreferenceScore = FamilyPreferenceScore()
    hard_exclude: bool = False
    hard_reasons: tuple[HardExcludeReason, ...] = field(default_factory=tuple)


class FamilyPreferenceService:
    """Family-aware compatibility interface (stub in Sprint 6).

    In Sprint 6 we intentionally do not wire this service into existing
    endpoints. The goal is to establish a stable type surface and
    constants so subsequent commits can implement the actual evaluation.
    """

    def __init__(self, db: Session) -> None:
        self._db = db

    def evaluate(
        self,
        *,
        recipe_id: int,
        user: User,
        scope: AppScope | None = None,
    ) -> FamilyCompatibilityResult:
        _ = (user, scope)
        return FamilyCompatibilityResult(recipe_id=recipe_id)

