from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

MealTypeFilter = Literal["breakfast", "lunch", "dinner", "snack", ""]
CategoryFilter = Literal[
    "soup",
    "main",
    "salad",
    "dessert",
    "quick",
    "kids",
    "",
]
DifficultyFilter = Literal["easy", "medium", "hard", ""]


class RecipeIngredient(BaseModel):
    name: str
    amount: str


class RecipeSummary(BaseModel):
    id: int
    title: str
    description: str
    meal_type: str
    category: str
    prep_time_minutes: int
    servings: int
    difficulty: str
    diets: list[str]
    tags: list[str]
    is_favorited: bool = False


class RecipeDetail(RecipeSummary):
    ingredients: list[RecipeIngredient]
    steps: list[str]
    created_at: datetime


class RecipeListResponse(BaseModel):
    items: list[RecipeSummary]
    total: int


class RecipeFiltersResponse(BaseModel):
    meal_types: list[dict[str, str]]
    categories: list[dict[str, str]]
    diets: list[dict[str, str]]
    difficulties: list[dict[str, str]]
    max_prep_time: int


class FavoriteToggleResponse(BaseModel):
    recipe_id: int
    is_favorited: bool
