from pydantic import BaseModel, Field


class NutritionistAskRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)


class NutritionistAskResponse(BaseModel):
    answer: str
    used_ai: bool = False
