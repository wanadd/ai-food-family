"""Recommendations — current heuristic.

Sprint 1 constraint: structural refactor only; behaviour preserved from the
legacy ``app.services.recipes`` implementation.

No new API routes are added in this sprint.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.recipe import Recipe
from app.models.user import User
from app.schemas.recipe import (
    RecipeRecommendationItem,
    RecipeRecommendationsResponse,
)
from app.services.app_scope import AppScope
from app.services.onboarding import get_or_create_profile


def get_recommendations(
    db: Session,
    user: User,
    scope: AppScope,
    *,
    limit: int = 10,
) -> RecipeRecommendationsResponse:
    _ = scope
    profile = get_or_create_profile(db, user)
    recipes = (
        db.query(Recipe)
        .filter(Recipe.is_active.is_(True), Recipe.is_alcoholic.is_(False))
        .limit(80)
        .all()
    )

    goal = profile.goal or "healthy"
    items: list[RecipeRecommendationItem] = []
    for recipe in recipes:
        score = 0.5
        reason = "Подходит по каталогу"
        if goal in ("sport", "mass", "cut") and recipe.suitable_for_sport:
            score += 0.3
            reason = "Подходит для спортивной цели"
        if recipe.meal_type == "protein_shake" and goal in ("sport", "mass"):
            score += 0.2
            reason = "Протеиновый напиток для вашей цели"
        items.append(
            RecipeRecommendationItem(
                id=recipe.id,
                title=recipe.title,
                meal_type=recipe.meal_type,
                score=score,
                reason=reason,
            )
        )

    items.sort(key=lambda x: x.score, reverse=True)
    return RecipeRecommendationsResponse(items=items[:limit])

