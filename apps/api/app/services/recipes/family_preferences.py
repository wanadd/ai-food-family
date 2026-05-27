"""Family preference scoring — family_recipe_preferences table."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from sqlalchemy.orm import Session

from app.config import settings
from app.models.recipe import Recipe
from app.models.recipe_engine import FamilyRecipePreference
from app.models.user import User
from app.services import family as family_service
from app.services.app_scope import AppScope
from app.services.onboarding import get_or_create_profile
from app.services.recipe_analysis import (
    ALLERGEN_KEYWORDS,
    _ingredient_text,
    _member_allergies,
)
from app.services.recipe_storage import get_allergens, get_restrictions
from app.services.recipes.repositories.preferences import FamilyRecipePreferenceRepository


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
    per_member_breakdown: tuple[float, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class FamilyCompatibilityResult:
    recipe_id: int
    score: FamilyPreferenceScore = field(default_factory=FamilyPreferenceScore)
    hard_exclude: bool = False
    hard_reasons: tuple[HardExcludeReason, ...] = field(default_factory=tuple)


class FamilyPreferenceService:
    def __init__(self, db: Session) -> None:
        self._db = db
        self._repo = FamilyRecipePreferenceRepository(db)

    def set_preference(
        self,
        *,
        recipe_id: int,
        family_id: int,
        family_member_id: int,
        liked: bool = False,
        disliked: bool = False,
        is_loved: bool = False,
        note: str | None = None,
    ) -> FamilyRecipePreference:
        if not settings.family_recipe_preferences:
            raise NotImplementedError(
                "family_recipe_preferences feature flag is disabled"
            )

        if is_loved:
            liked = True
        if liked and disliked:
            disliked = False

        row = FamilyRecipePreference(
            recipe_id=recipe_id,
            family_id=family_id,
            family_member_id=family_member_id,
            liked=liked,
            disliked=disliked,
            is_loved=is_loved,
            note=note,
        )
        saved = self._repo.upsert(row)
        self._db.commit()
        self._db.refresh(saved)
        return saved

    def _hard_exclude_reasons(
        self, db: Session, user: User, recipe: Recipe, scope: AppScope
    ) -> list[HardExcludeReason]:
        reasons: list[HardExcludeReason] = []
        if scope.family_id is None:
            return reasons

        family = family_service.get_family_for_user(db, user)
        members = family.members if family else []
        text = _ingredient_text(recipe).lower()
        allergen_set = {a.lower() for a in get_allergens(recipe)}
        restriction_set = {r.lower() for r in get_restrictions(recipe)}

        profile = get_or_create_profile(db, user)
        medical_user = (profile.medical_restrictions or "").lower()

        for member in members:
            allergies = _member_allergies(db, member)

            for allergen in allergies:
                allergen_l = str(allergen).lower()
                if allergen_l in allergen_set or allergen_l in text:
                    reasons.append(HardExcludeReason.ALLERGY)
                    break
                for kw, code in ALLERGEN_KEYWORDS.items():
                    if allergen_l in code or allergen_l in kw:
                        if kw in text:
                            reasons.append(HardExcludeReason.ALLERGY)
                            break

        for token in ("диабет", "гипертон", "целиак", "подагр"):
            if token in medical_user and (
                token in restriction_set or token in text
            ):
                reasons.append(HardExcludeReason.MEDICAL_RESTRICTION)
                break

        return list(dict.fromkeys(reasons))

    def evaluate(
        self,
        *,
        recipe_id: int,
        user: User,
        scope: AppScope | None = None,
    ) -> FamilyCompatibilityResult:
        if not settings.family_recipe_preferences:
            return FamilyCompatibilityResult(recipe_id=recipe_id)

        recipe = self._db.get(Recipe, recipe_id)
        if recipe is None:
            return FamilyCompatibilityResult(recipe_id=recipe_id)

        hard_reasons: list[HardExcludeReason] = []
        if scope is not None and scope.family_id is not None:
            hard_reasons = self._hard_exclude_reasons(self._db, user, recipe, scope)

        loved_delta = 0.0
        liked_delta = 0.0
        disliked_delta = 0.0
        breakdown: list[float] = []

        if scope is not None and scope.family_id is not None:
            prefs = self._repo.list_for_recipe(recipe_id, scope.family_id)
            for pref in prefs:
                member_score = 0.0
                if pref.is_loved:
                    member_score += LOVED_WEIGHT
                    loved_delta += LOVED_WEIGHT
                elif pref.liked:
                    member_score += LIKED_WEIGHT
                    liked_delta += LIKED_WEIGHT
                elif pref.disliked:
                    member_score += DISLIKED_WEIGHT
                    disliked_delta += DISLIKED_WEIGHT
                breakdown.append(member_score)

        total = loved_delta + liked_delta + disliked_delta
        return FamilyCompatibilityResult(
            recipe_id=recipe_id,
            score=FamilyPreferenceScore(
                total=total,
                loved_delta=loved_delta,
                liked_delta=liked_delta,
                disliked_delta=disliked_delta,
                per_member_breakdown=tuple(breakdown),
            ),
            hard_exclude=bool(hard_reasons),
            hard_reasons=tuple(hard_reasons),
        )
