"""Recipe Engine search DTOs (Sprint 2 abstraction).

Sprint 1 / current router does not expose search query params as a dedicated
endpoint; Sprint 2 introduces a service + DTO layer only, without changing
existing API contracts.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.recipe import RecipeSummary


RecipeSortLiteral = Literal["title", "relevance", "popularity", "score"]


class RecipeSearchQuery(BaseModel):
    q: str | None = Field(default=None, max_length=200)
    meal_type: str | None = None
    category: str | None = None
    diet: str | None = None
    difficulty: str | None = None
    max_prep_time: int | None = Field(default=None, ge=5, le=300)

    favorites_only: bool = False
    for_children: bool = False
    for_sport: bool = False
    for_event: bool = False
    drinks_only: bool = False
    non_alcoholic: bool = False
    alcoholic_only: bool = False
    protein_only: bool = False
    smoothie_only: bool = False
    tea_coffee_only: bool = False
    exclude_allergens: str | None = None

    # Reserved dimensions for later wiring (collections/scenarios/family).
    scenarios: list[str] = Field(default_factory=list)
    collection_ids: list[int] = Field(default_factory=list)
    family_member_ids: list[int] = Field(default_factory=list)
    not_disliked: bool = False
    cooked_recently_days: int | None = Field(default=None, ge=1, le=365)

    limit: int = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)
    sort: RecipeSortLiteral = "title"


class RecipeSearchHit(BaseModel):
    recipe: RecipeSummary
    score: float | None = None
    reason_codes: list[str] = Field(default_factory=list)


class RecipeSearchResponse(BaseModel):
    items: list[RecipeSearchHit]
    total: int
    limit: int
    offset: int
    sort: RecipeSortLiteral = "title"

