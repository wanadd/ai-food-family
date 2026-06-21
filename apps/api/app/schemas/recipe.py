from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

MealTypeFilter = Literal[
    "breakfast",
    "lunch",
    "dinner",
    "snack",
    "dessert",
    "drink",
    "cocktail",
    "smoothie",
    "protein_shake",
    "tea",
    "coffee",
    "",
]
CategoryFilter = Literal[
    "soup",
    "main",
    "salad",
    "dessert",
    "quick",
    "kids",
    "drink",
    "event",
    "bbq",
    "",
]
DifficultyFilter = Literal["easy", "medium", "hard", ""]


class RecipeIngredient(BaseModel):
    name: str
    amount: str
    quantity: str | None = None
    unit: str | None = None
    category: str | None = None
    is_optional: bool = False


class NutritionSummary(BaseModel):
    """Recipe-level KБЖУ summary (additive; null when not yet calculated)."""

    kcal_total: float | None = None
    protein_total: float | None = None
    fat_total: float | None = None
    carbs_total: float | None = None
    kcal_per_serving: float | None = None
    protein_per_serving: float | None = None
    fat_per_serving: float | None = None
    carbs_per_serving: float | None = None
    servings: float | None = None
    serving_size_text: str | None = None
    confidence: Literal["exact", "estimated", "low_confidence", "unavailable"] | None = None
    needs_review: bool = False
    review_reason: str | None = None
    calculated_at: datetime | None = None


class RecipeSummary(BaseModel):
    id: int
    title: str
    display_title: str | None = None
    full_title: str | None = None
    description: str
    meal_type: str
    category: str
    prep_time_minutes: int
    cooking_time_minutes: int = 30
    servings: int
    difficulty: str
    diets: list[str]
    tags: list[str]
    is_favorited: bool = False
    is_drink: bool = False
    is_alcoholic: bool = False
    calories_per_serving: float | None = None
    protein_g: float | None = None
    fat_g: float | None = None
    carbs_g: float | None = None
    suitable_for_children: bool = True
    suitable_for_sport: bool = False
    suitable_for_event: bool = False
    fit_level: Literal["good", "partial", "not_recommended"] | None = None
    image_url: str | None = None
    hero_image_url: str | None = None
    thumbnail_url: str | None = None
    is_gold_v3: bool = False
    recipe_schema: str | None = None
    image_ready: bool = False
    nutrition_summary: NutritionSummary | None = None


class RecipeDetail(RecipeSummary):
    original_title: str | None = None
    ingredients: list[RecipeIngredient]
    steps: list[str]
    allergens: list[str] = []
    restrictions: list[str] = []
    sugar_g: float | None = None
    caffeine_mg: float | None = None
    alcohol_percent: float | None = None
    cuisine: str | None = None
    source_type: str = "manual"
    created_at: datetime
    updated_at: datetime | None = None


class RecipeListResponse(BaseModel):
    items: list[RecipeSummary]
    total: int


class RecipeFiltersResponse(BaseModel):
    meal_types: list[dict[str, str]]
    categories: list[dict[str, str]]
    diets: list[dict[str, str]]
    difficulties: list[dict[str, str]]
    max_prep_time: int
    drink_modes: list[dict[str, str]] = []


class FavoriteToggleResponse(BaseModel):
    recipe_id: int
    is_favorited: bool


class RecipeCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = ""
    meal_type: str
    category: str = "main"
    cooking_time_minutes: int = 30
    servings: int = Field(default=4, ge=1, le=50)
    difficulty: str = "easy"
    ingredients: list[RecipeIngredient] = Field(min_length=1)
    steps: list[str] = Field(min_length=1)
    tags: list[str] = []
    allergens: list[str] = []
    restrictions: list[str] = []
    is_drink: bool = False
    is_alcoholic: bool = False
    source_type: str = "manual"


class RecipeUpdateRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    is_active: bool | None = None


class AddRecipeToShoppingRequest(BaseModel):
    servings: int | None = Field(default=None, ge=1, le=50)


class RecipeRecommendationItem(BaseModel):
    id: int
    title: str
    meal_type: str
    score: float
    reason: str


class RecipeRecommendationsResponse(BaseModel):
    items: list[RecipeRecommendationItem]
