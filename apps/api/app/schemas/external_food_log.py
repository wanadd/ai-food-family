from datetime import date, datetime

from pydantic import BaseModel, Field


class ExternalFoodLogCreateIn(BaseModel):
    family_id: int | None = None
    meal_type: str | None = Field(default=None, max_length=16)
    planned_date: date
    source_type: str = Field(default="manual", max_length=32)
    input_text: str | None = Field(default=None, max_length=2000)
    parsed_title: str | None = Field(default=None, max_length=300)
    calories_estimated: float | None = Field(default=None, ge=0)
    protein_estimated: float | None = Field(default=None, ge=0)
    fat_estimated: float | None = Field(default=None, ge=0)
    carbs_estimated: float | None = Field(default=None, ge=0)
    confidence: float | None = Field(default=None, ge=0, le=1)
    status: str = Field(default="draft", max_length=32)


class ExternalFoodLogOut(BaseModel):
    id: int
    user_id: int
    family_id: int | None
    meal_type: str | None
    planned_date: date
    source_type: str
    input_text: str | None
    parsed_title: str | None
    calories_estimated: float | None
    protein_estimated: float | None
    fat_estimated: float | None
    carbs_estimated: float | None
    confidence: float | None
    status: str
    linked_meal_consumption_log_id: int | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
