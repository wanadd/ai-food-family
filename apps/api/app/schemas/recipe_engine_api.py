"""HTTP DTOs for Recipe Engine Sprint 3 endpoints."""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.services.recipes.explainability import RecommendationReason


class RecommendationReasonResponse(BaseModel):
    code: RecommendationReason
    label: str
    kind: Literal["positive", "warning", "hard_block"] = "positive"
    weight: float = 0.0


class RecipeWhyResponse(BaseModel):
    recipe_id: int
    summary: str
    positives: list[RecommendationReasonResponse] = Field(default_factory=list)
    warnings: list[RecommendationReasonResponse] = Field(default_factory=list)
    hard_blocks: list[RecommendationReasonResponse] = Field(default_factory=list)
    score_total: float = 0.0
    uses_ai: bool = False
    uses_ama: bool = False


class MarkCookedRequest(BaseModel):
    cooked_on: date | None = None
    servings: int | None = Field(default=None, ge=1, le=50)
    notes: str | None = Field(default=None, max_length=200)
    family_member_id: int | None = None
    source: Literal["manual", "menu", "bot", "checkin"] = "manual"


class CookingEventResponse(BaseModel):
    id: int
    recipe_id: int
    cooked_on: date
    servings: int | None = None
    source: str
    notes: str | None = None
    user_id: int | None = None
    family_id: int | None = None
    family_member_id: int | None = None
    created_at: datetime | None = None


class CookingStatsResponse(BaseModel):
    recipe_id: int
    cooked_count: int = 0
    last_cooked_on: date | None = None


class RecipeHistoryListResponse(BaseModel):
    items: list[CookingEventResponse] = Field(default_factory=list)
    total: int = 0
    stats: CookingStatsResponse | None = None


class RecipeRateRequest(BaseModel):
    family_member_id: int
    liked: bool | None = None
    disliked: bool | None = None
    is_loved: bool | None = None
    rating: Literal["disliked", "liked", "loved"] | None = None
    note: str | None = Field(default=None, max_length=200)


class RecipeRateResponse(BaseModel):
    recipe_id: int
    family_member_id: int
    liked: bool
    disliked: bool
    is_loved: bool
    note: str | None = None


class ScenarioListItemResponse(BaseModel):
    scenario: str
    label: str
    recipes_count: int = 0
    active: bool = True


class RecipeScenariosListResponse(BaseModel):
    items: list[ScenarioListItemResponse] = Field(default_factory=list)


class FromPantryIngredientCoverage(BaseModel):
    name: str
    in_pantry: bool


class RecipeSummaryRef(BaseModel):
    """Slim recipe card embedded in from-pantry results."""

    id: int
    title: str
    meal_type: str
    category: str
    cooking_time_minutes: int = 30


class FromPantryRecipeItem(BaseModel):
    recipe_id: int
    title: str
    have: int
    total: int
    missing_ingredients: list[str] = Field(default_factory=list)
    coverage_ratio: float = 0.0
    summary: RecipeSummaryRef | None = None


class FromPantryListResponse(BaseModel):
    items: list[FromPantryRecipeItem] = Field(default_factory=list)
    total: int = 0
    uses_ai: bool = False
    uses_ama: bool = False
