from datetime import datetime

from pydantic import BaseModel, Field


class OnboardingData(BaseModel):
    current_step: int = Field(ge=0, le=8)
    completed: bool = False
    goals: list[str] = Field(default_factory=list)
    diets: list[str] = Field(default_factory=list)
    allergies: list[str] = Field(default_factory=list)
    restrictions: list[str] = Field(default_factory=list)
    favorite_foods: str = ""
    disliked_foods: str = ""
    budget: str | None = None
    cooking_time: str | None = None


class OnboardingResponse(OnboardingData):
    updated_at: datetime | None = None
