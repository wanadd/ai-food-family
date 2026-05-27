"""Recipe search abstraction (Sprint 2 scaffolding).

No new API routes are added in this sprint; this module only introduces a
service and internal abstractions so later commits can wire a dedicated
search endpoint and advanced filtering/sorting without rewriting the
domain logic.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.config import settings
from app.models.user import User
from app.schemas.recipe_search import (
    RecipeSearchHit,
    RecipeSearchQuery,
    RecipeSearchResponse,
)
from app.services.app_scope import AppScope
from app.services.recipes import catalog
from app.services.recipes.types import RecipeSortOrder


class SearchService:
    """Search facade.

    Sprint 2 behavioural note:
    - We do not introduce tsvector/FTS yet.
    - We reuse the existing ``catalog.list_recipes`` filtering logic.
    - Collections/scenarios/family compatibility fields from
      ``RecipeSearchQuery`` are accepted as part of the contract but not
      applied until subsequent commits.
    """

    def __init__(self, db: Session) -> None:
        self._db = db

    def search(
        self,
        query: RecipeSearchQuery,
        *,
        user: User,
        scope: AppScope | None = None,
    ) -> RecipeSearchResponse:
        if not settings.recipe_engine_v1:
            return RecipeSearchResponse(
                items=[],
                total=0,
                limit=query.limit,
                offset=query.offset,
                sort=query.sort,
            )

        resp = catalog.list_recipes(
            self._db,
            user,
            q=query.q,
            meal_type=query.meal_type,
            category=query.category,
            diet=query.diet,
            difficulty=query.difficulty,
            max_prep_time=query.max_prep_time,
            favorites_only=query.favorites_only,
            from_pantry=False,
            for_children=query.for_children,
            for_sport=query.for_sport,
            for_event=query.for_event,
            drinks_only=query.drinks_only,
            non_alcoholic=query.non_alcoholic,
            alcoholic_only=query.alcoholic_only,
            protein_only=query.protein_only,
            smoothie_only=query.smoothie_only,
            tea_coffee_only=query.tea_coffee_only,
            exclude_allergens=query.exclude_allergens,
            goal=None,
            scope=scope,
        )

        total = resp.total
        items = resp.items[query.offset : query.offset + query.limit]

        hits = [
            RecipeSearchHit(recipe=item, score=None, reason_codes=[])
            for item in items
        ]

        # Keep DTO contract stable for later upgrades.
        sort_value = query.sort
        _ = RecipeSortOrder  # reserved for future sort wiring

        return RecipeSearchResponse(
            items=hits,
            total=total,
            limit=query.limit,
            offset=query.offset,
            sort=sort_value,
        )

