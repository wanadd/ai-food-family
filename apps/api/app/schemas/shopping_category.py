from datetime import datetime

from pydantic import BaseModel, Field


class ShoppingCategoryResponse(BaseModel):
    id: int
    slug: str
    name: str
    icon: str | None
    is_food: bool
    is_system: bool
    created_at: datetime


class ShoppingCategoryCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    is_food: bool = True
    icon: str | None = Field(default=None, max_length=16)
