from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.goal_details import NutritionGoalDetails


class NutritionProData(BaseModel):
    workouts_enabled: bool = False
    workout_goal: str = ""
    workout_frequency: str | None = None
    body_measurements: str = ""
    water_liters: float | None = None
    track_macros: bool = False


class NutritionProfileData(BaseModel):
    age: int | None = Field(default=None, ge=1, le=120)
    gender: str | None = None
    height_cm: int | None = Field(default=None, ge=50, le=250)
    weight_kg: float | None = Field(default=None, ge=20, le=300)
    nutrition_goal: str | None = None
    activity_level: str | None = None
    allergies: list[str] = Field(default_factory=list)
    medical_restrictions: str = ""
    banned_foods: str = ""
    diets: list[str] = Field(default_factory=list)
    favorite_foods: str = ""
    disliked_foods: str = ""
    budget: str | None = None
    cooking_time: str | None = None
    dish_complexity: str | None = None
    pro: NutritionProData = Field(default_factory=NutritionProData)
    goal_details: NutritionGoalDetails = Field(default_factory=NutritionGoalDetails)
    completed: bool = False


class NutritionProfileResponse(NutritionProfileData):
    updated_at: datetime | None = None
