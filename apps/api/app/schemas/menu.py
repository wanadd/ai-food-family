from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

MenuVariantType = Literal["quick", "economy", "balanced"]
MealType = Literal["breakfast", "lunch", "dinner", "snack"]


class MenuMeal(BaseModel):
    meal_type: MealType
    name: str = Field(min_length=1, max_length=200)
    description: str = ""
    prep_time_minutes: int = Field(ge=0, le=300)
    calories_estimate: int | None = Field(default=None, ge=0)
    recipe_id: int | None = None
    slot_id: str | None = Field(default=None, max_length=64)
    servings: int | None = Field(default=None, ge=1, le=50)
    image_url: str | None = None
    hero_image_url: str | None = None
    thumbnail_url: str | None = None


class MenuDayPlan(BaseModel):
    day_index: int = Field(ge=1, le=30)
    label: str = ""
    date_iso: str | None = None
    meals: list[MenuMeal] = Field(min_length=1)


class MenuIngredient(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    amount: str = Field(min_length=1, max_length=80)
    category: str | None = None


class MenuVariant(BaseModel):
    variant: MenuVariantType
    title: str
    tagline: str = ""
    explanation: str
    estimated_daily_cost: str | None = None
    total_prep_minutes: int = Field(ge=0)
    meals: list[MenuMeal] = Field(min_length=1)
    ingredients: list[MenuIngredient] = Field(min_length=1)
    plan_days: int | None = Field(default=None, ge=1, le=30)
    days: list[MenuDayPlan] | None = None


class MenuGenerateResponse(BaseModel):
    menus: list[MenuVariant] = Field(min_length=3, max_length=3)
    scope_mode: str = "personal"
    context_label: str = ""
    family_name: str | None = None
    members_count: int = 0
    generated_with_ai: bool = False


class ReplaceDishRequest(BaseModel):
    menu: MenuVariant
    meal_index: int = Field(ge=0)
    day_index: int | None = Field(default=None, ge=1, le=30)
    hint: str | None = Field(default=None, max_length=300)


DrinkMenuMode = Literal[
    "none",
    "non_alcoholic",
    "sport",
    "tea_coffee",
    "cocktail",
    "custom",
]


class MenuGenerateRequest(BaseModel):
    persons_count: int | None = Field(default=None, ge=1, le=20)
    plan_mode: str | None = Field(default=None, max_length=64)
    plan_days: int | None = Field(default=None, ge=1, le=30)
    nutrition_goal: str | None = Field(default=None, max_length=32)
    drink_mode: DrinkMenuMode | None = None
    allow_alcohol: bool = False


class SelectMenuRequest(BaseModel):
    menu: MenuVariant


class SelectedMenuResponse(BaseModel):
    id: int
    scope_mode: str
    user_id: int
    family_id: int | None
    variant: MenuVariantType
    menu: MenuVariant
    selected_at: datetime

    model_config = {"from_attributes": True}
