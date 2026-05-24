from datetime import date, datetime

from pydantic import BaseModel, Field


class MealCheckinCreate(BaseModel):
    meal_type: str = Field(max_length=16)
    actual_status: str = Field(max_length=32)
    planned_date: date | None = None
    family_member_id: int | None = None
    actual_description: str | None = Field(default=None, max_length=500)
    leftover_servings_delta: int | None = None
    leftover_status: str | None = Field(default=None, max_length=32)
    recipe_id: int | None = None


class MealCheckinResponse(BaseModel):
    id: int
    meal_type: str
    planned_date: date
    actual_status: str
    actual_description: str | None
    leftover_servings_delta: int | None
    family_member_id: int | None = None
    member_name: str | None = None
    created_at: datetime
