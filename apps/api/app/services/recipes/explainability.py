"""Explainability engine — deterministic recommendation reasons (no AI)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Literal

from sqlalchemy.orm import Session

from app.config import settings
from app.models.recipe import Recipe
from app.models.recipe_engine import RecipeExplanation
from app.models.user import User
from app.services.app_scope import AppScope
from app.services.onboarding import get_or_create_profile
from app.services.pantry import get_active_items_for_scope
from app.services.recipe_storage import get_structured_ingredients
from app.services.recipes.family_preferences import FamilyPreferenceService
from app.services.recipes.repositories.explanations import RecipeExplanationRepository
from app.services.recipes.repositories.scenarios import RecipeScenarioRepository
from app.services.recipes.scenarios import ScenarioType


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

_REASON_LABELS: dict[RecommendationReason, str] = {
    RecommendationReason.IN_PANTRY: "Часть ингредиентов уже есть в запасах",
    RecommendationReason.KIDS_LIKE: "Подходит детям",
    RecommendationReason.GOAL_MATCH: "Подходит вашей цели питания",
    RecommendationReason.QUICK_COOKING: "Готовится быстро",
    RecommendationReason.BUDGET_FRIENDLY: "Бюджетный рецепт",
    RecommendationReason.HIGH_PROTEIN: "Высокое содержание белка",
    RecommendationReason.LOW_CALORIE: "Низкая калорийность",
    RecommendationReason.FAMILY_APPROVED: "Семья оценила положительно",
}


@dataclass(frozen=True)
class RecommendationReasonEntry:
    reason: RecommendationReason
    kind: ReasonKind = "positive"
    label: str = ""
    icon: str = ""
    weight: float = 0.0

    @classmethod
    def of(
        cls,
        reason: RecommendationReason,
        *,
        weight: float = 0.0,
        kind: ReasonKind = "positive",
    ) -> "RecommendationReasonEntry":
        return cls(
            reason=reason,
            label=_REASON_LABELS.get(reason, reason.value),
            weight=weight,
            kind=kind,
        )


@dataclass(frozen=True)
class ExplainabilityResult:
    recipe_id: int
    summary: str
    positives: tuple[RecommendationReasonEntry, ...] = field(default_factory=tuple)
    warnings: tuple[RecommendationReasonEntry, ...] = field(default_factory=tuple)
    hard_blocks: tuple[RecommendationReasonEntry, ...] = field(default_factory=tuple)
    score_total: float = 0.0


class ExplainabilityService:
    NEUTRAL_SUMMARY = "Подходит по каталогу"

    def __init__(self, db: Session) -> None:
        self._db = db
        self._explanations = RecipeExplanationRepository(db)
        self._scenarios = RecipeScenarioRepository(db)
        self._family = FamilyPreferenceService(db)

    def _collect_reasons(
        self,
        recipe: Recipe,
        *,
        user: User,
        scope: AppScope | None,
    ) -> tuple[list[RecommendationReasonEntry], float]:
        positives: list[RecommendationReasonEntry] = []
        score = 0.0

        if scope is not None:
            pantry = {p.name.lower() for p in get_active_items_for_scope(self._db, scope)}
            if pantry:
                for ing in get_structured_ingredients(recipe):
                    name = ing["name"].lower()
                    if any(p in name or name in p for p in pantry):
                        positives.append(
                            RecommendationReasonEntry.of(
                                RecommendationReason.IN_PANTRY, weight=2.0
                            )
                        )
                        score += 2.0
                        break

        if recipe.suitable_for_children:
            positives.append(
                RecommendationReasonEntry.of(
                    RecommendationReason.KIDS_LIKE, weight=1.0
                )
            )
            score += 1.0

        profile = get_or_create_profile(self._db, user)
        goal = (profile.nutrition_goal or "healthy").lower()
        minutes = recipe.cooking_time_minutes or 30

        if minutes <= 25:
            positives.append(
                RecommendationReasonEntry.of(
                    RecommendationReason.QUICK_COOKING, weight=1.0
                )
            )
            score += 1.0

        diets = [str(d).lower() for d in (recipe.diets or [])]
        if "budget" in diets or (profile.budget or "").lower() in ("low", "economy", "эконом"):
            positives.append(
                RecommendationReasonEntry.of(
                    RecommendationReason.BUDGET_FRIENDLY, weight=1.0
                )
            )
            score += 1.0

        protein = recipe.protein_g or 0
        if protein >= 20 or goal in ("sport", "gain", "mass"):
            if protein >= 20:
                positives.append(
                    RecommendationReasonEntry.of(
                        RecommendationReason.HIGH_PROTEIN, weight=1.0
                    )
                )
                score += 1.0

        calories = recipe.calories_per_serving
        if calories is not None and calories <= 400 and goal in ("lose", "weight_loss"):
            positives.append(
                RecommendationReasonEntry.of(
                    RecommendationReason.LOW_CALORIE, weight=1.0
                )
            )
            score += 1.0

        if goal in ("lose", "weight_loss") and calories and calories <= 500:
            positives.append(
                RecommendationReasonEntry.of(RecommendationReason.GOAL_MATCH, weight=2.0)
            )
            score += 2.0
        elif goal in ("sport", "gain", "mass") and (
            recipe.suitable_for_sport or protein >= 20
        ):
            positives.append(
                RecommendationReasonEntry.of(RecommendationReason.GOAL_MATCH, weight=2.0)
            )
            score += 2.0

        compat = self._family.evaluate(recipe_id=recipe.id, user=user, scope=scope)
        if compat.score.loved_delta > 0 or compat.score.liked_delta > 0:
            weight = compat.score.loved_delta + compat.score.liked_delta
            positives.append(
                RecommendationReasonEntry.of(
                    RecommendationReason.FAMILY_APPROVED, weight=weight
                )
            )
            score += weight

        scenario_rows = self._scenarios.list_for_recipe(recipe.id)
        if any(r.scenario == ScenarioType.QUICK.value for r in scenario_rows):
            if not any(p.reason == RecommendationReason.QUICK_COOKING for p in positives):
                positives.append(
                    RecommendationReasonEntry.of(
                        RecommendationReason.QUICK_COOKING, weight=0.5
                    )
                )
                score += 0.5

        return positives, score

    def explain(
        self,
        recipe_id: int,
        *,
        user: User,
        scope: AppScope | None = None,
    ) -> ExplainabilityResult:
        if not settings.recipe_explainability:
            return ExplainabilityResult(
                recipe_id=recipe_id, summary=self.NEUTRAL_SUMMARY
            )

        recipe = self._db.get(Recipe, recipe_id)
        if recipe is None:
            return ExplainabilityResult(
                recipe_id=recipe_id, summary=self.NEUTRAL_SUMMARY
            )

        positives, score = self._collect_reasons(recipe, user=user, scope=scope)
        summary = positives[0].label if positives else self.NEUTRAL_SUMMARY

        family_id = scope.family_id if scope is not None and scope.is_family else None
        reasons_payload = {
            "positives": [
                {"code": p.reason.value, "label": p.label, "weight": p.weight}
                for p in positives
            ]
        }
        self._explanations.upsert(
            RecipeExplanation(
                recipe_id=recipe_id,
                user_id=user.id,
                family_id=family_id,
                summary=summary,
                reasons_json=reasons_payload,
                score_total=score,
            )
        )
        self._db.commit()

        return ExplainabilityResult(
            recipe_id=recipe_id,
            summary=summary,
            positives=tuple(positives),
            score_total=score,
        )
