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


class MenuGenerateResponse(BaseModel):
    menus: list[MenuVariant] = Field(min_length=3, max_length=3)
    family_name: str | None = None
    members_count: int = 0
    generated_with_ai: bool = False


class ReplaceDishRequest(BaseModel):
    menu: MenuVariant
    meal_index: int = Field(ge=0)
    hint: str | None = Field(default=None, max_length=300)


class SelectMenuRequest(BaseModel):
    menu: MenuVariant


class SelectedMenuResponse(BaseModel):
    id: int
    family_id: int
    variant: MenuVariantType
    menu: MenuVariant
    selected_at: datetime

    model_config = {"from_attributes": True}
