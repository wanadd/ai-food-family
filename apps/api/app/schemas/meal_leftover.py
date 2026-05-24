from datetime import date, datetime

from pydantic import BaseModel, Field


class MealLeftoverCreate(BaseModel):
    dish_name: str = Field(min_length=1, max_length=200)
    portions_remaining: int = Field(ge=1, le=50)
    valid_until: date | None = None
    note: str | None = Field(default=None, max_length=200)


class MealLeftoverUpdate(BaseModel):
    dish_name: str | None = Field(default=None, min_length=1, max_length=200)
    portions_remaining: int | None = Field(default=None, ge=1, le=50)
    valid_until: date | None = None
    note: str | None = Field(default=None, max_length=200)
    leftover_status: str | None = Field(default=None, max_length=32)


class MealLeftoverResponse(BaseModel):
    id: int
    scope_mode: str
    dish_name: str
    portions_remaining: int
    valid_until: date | None
    note: str | None
    leftover_status: str = "active"
    created_at: datetime
    updated_at: datetime
