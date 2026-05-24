from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

IntensityLevel = Literal["low", "medium", "high"]
MemberProgressStatus = Literal["improving", "stable", "attention", "hidden"]


class ProgressEntryCreate(BaseModel):
    weight_kg: float | None = None
    body_fat_percent: float | None = None
    waist_cm: float | None = None
    chest_cm: float | None = None
    hips_cm: float | None = None
    notes: str | None = None
    recorded_at: datetime | None = None


class ProgressEntryResponse(BaseModel):
    id: int
    weight_kg: float | None
    body_fat_percent: float | None
    waist_cm: float | None
    chest_cm: float | None
    hips_cm: float | None
    notes: str | None
    recorded_at: datetime


class TrainingEntryCreate(BaseModel):
    training_type: str = Field(min_length=1, max_length=64)
    duration_minutes: int | None = Field(default=None, ge=1, le=600)
    intensity: IntensityLevel = "medium"
    calories_burned: int | None = Field(default=None, ge=0)
    notes: str | None = None
    training_date: date | None = None


class TrainingEntryResponse(BaseModel):
    id: int
    training_type: str
    duration_minutes: int | None
    intensity: str
    calories_burned: int | None
    notes: str | None
    training_date: date


class NutritionActualResponse(BaseModel):
    calories_consumed: int = 0
    protein_consumed_g: int = 0
    fat_consumed_g: int = 0
    carbs_consumed_g: int = 0
    water_consumed_ml: int = 0
    meals_logged: int = 0


class NutritionTargetsResponse(BaseModel):
    calories_target: int | None
    protein_target_g: int | None
    fat_target_g: int | None
    carbs_target_g: int | None
    fiber_target_g: int | None
    water_target_ml: int | None
    goal_type: str | None


class NutritionTargetsUpdate(BaseModel):
    calories_target: int | None = None
    protein_target_g: int | None = None
    fat_target_g: int | None = None
    carbs_target_g: int | None = None
    fiber_target_g: int | None = None
    water_target_ml: int | None = None
    goal_type: str | None = None


class ProgressSettingsUpdate(BaseModel):
    show_progress_to_family: bool | None = None


class FamilyMemberProgressCard(BaseModel):
    member_id: int
    name: str
    goal_label: str | None
    progress_summary: str
    status: MemberProgressStatus
    is_you: bool = False


class ProgressOverviewResponse(BaseModel):
    is_pro: bool
    goal_label: str | None
    goal_type: str | None
    current_weight_kg: float | None
    start_weight_kg: float | None = None
    target_weight_kg: float | None = None
    goal_started_at: date | None = None
    goal_forecast_date: date | None = None
    weight_change_week_kg: float | None
    goal_progress_percent: int | None
    targets: NutritionTargetsResponse | None = None
    daily_actual: NutritionActualResponse | None = None
    trainings_this_week: int = 0
    training_minutes_week: int = 0
    show_progress_to_family: bool = True
    family_progress: list[FamilyMemberProgressCard] = []
    pro_recommendation: str | None = None
    latest_entry: ProgressEntryResponse | None = None
