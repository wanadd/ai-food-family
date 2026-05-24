from pydantic import BaseModel, Field


class WaterIntakeCreate(BaseModel):
    amount_ml: int = Field(ge=50, le=2000)


class WaterIntakeTodayResponse(BaseModel):
    total_ml: int
    target_ml: int | None = None
