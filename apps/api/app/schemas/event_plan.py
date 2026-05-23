from datetime import datetime

from pydantic import BaseModel, Field


class EventPlanCreateRequest(BaseModel):
    event_type: str = Field(max_length=64)
    title: str | None = Field(default=None, max_length=200)
    guests_count: int = Field(default=4, ge=1, le=200)
    budget: str | None = None
    theme: str | None = None
    cuisine: str | None = None
    religious_restriction: str = "none"
    fasting_mode: str = "none"
    drink_menu_mode: str = "non_alcoholic"
    alcohol_enabled: bool = False
    kids_drinks_enabled: bool = True
    allergies_note: str | None = None


class EventPlanSummary(BaseModel):
    id: int
    title: str
    event_type: str
    guests_count: int
    status: str
    created_at: datetime


class EventPlanListResponse(BaseModel):
    items: list[EventPlanSummary]


class EventPlanDetail(EventPlanSummary):
    budget: str | None = None
    theme: str | None = None
    cuisine: str | None = None
    religious_restriction: str
    fasting_mode: str
    drink_menu_mode: str
    alcohol_enabled: bool
    kids_drinks_enabled: bool
    allergies_note: str | None = None
    dishes: list[dict] = []
    shopping: list[dict] = []
    nutrition_note: str | None = None
    estimated_cost_rub: int | None = None
