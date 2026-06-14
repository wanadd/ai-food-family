from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

VALID_STATUSES = frozenset({"eaten", "skipped", "ate_out", "unknown"})
VALID_PORTIONS = frozenset({0.0, 0.5, 1.0, 1.5, 2.0})


class MealConsumptionEntryIn(BaseModel):
    user_id: int | None = None
    family_member_id: int | None = None
    meal_type: str
    recipe_id: int | None = None
    recipe_title: str | None = None
    status: str
    portion_multiplier: float = 1.0
    note: str | None = None


class MealConsumptionBulkIn(BaseModel):
    family_id: int
    menu_selection_id: int | None = None
    day_index: int | None = None
    planned_date: date | None = None
    entries: list[MealConsumptionEntryIn] = Field(default_factory=list)


class MealConsumptionEntryOut(BaseModel):
    id: int
    user_id: int | None
    family_member_id: int | None = None
    meal_type: str | None
    recipe_id: int | None
    recipe_title: str | None = None
    status: str
    portion_multiplier: float

    model_config = {"from_attributes": True}


class MealConsumptionBulkOut(BaseModel):
    ok: bool = True
    saved: int
    entries: list[MealConsumptionEntryOut]


class MealConsumptionListOut(BaseModel):
    entries: list[MealConsumptionEntryOut]


class NutritionTotalsOut(BaseModel):
    calories: int
    protein: int
    fat: int
    carbs: int


class ConsumptionNutritionCountsOut(BaseModel):
    planned_meals: int
    logged_meals: int
    eaten: int
    skipped: int
    ate_out: int


class MealConsumptionNutritionSummaryOut(BaseModel):
    mode: Literal["planned", "actual"]
    has_consumption_logs: bool
    planned: NutritionTotalsOut
    actual: NutritionTotalsOut | None = None
    counts: ConsumptionNutritionCountsOut
    targets: dict[str, int | None] | None = None
