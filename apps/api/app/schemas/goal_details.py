from pydantic import BaseModel, Field


class NutritionGoalDetails(BaseModel):
    goal_type: str | None = None
    current_weight_kg: float | None = Field(default=None, ge=20, le=300)
    target_weight_kg: float | None = Field(default=None, ge=20, le=300)
    target_weight_min_kg: float | None = Field(default=None, ge=20, le=300)
    target_weight_max_kg: float | None = Field(default=None, ge=20, le=300)
    target_date: str | None = None
    goal_pace: str | None = None
    mass_gain_type: str | None = None
    sport_goal_type: str | None = None
    workouts_per_week: int | None = Field(default=None, ge=0, le=14)
    workout_days: list[str] = Field(default_factory=list)
    protein_target_g: float | None = None
    protein_per_kg: float | None = None
    water_target_ml: int | None = None
    health_focus: str | None = None
    habit_focus: str | None = None
    child_age_months: int | None = None
    child_feeding_stage: str | None = None
    parent_notes: str | None = None
