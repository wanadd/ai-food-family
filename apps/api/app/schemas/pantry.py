from datetime import date, datetime

from pydantic import BaseModel, Field


class PantryItemCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    quantity: str = Field(min_length=1, max_length=80)
    expires_at: date


class PantryItemUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    quantity: str | None = Field(default=None, min_length=1, max_length=80)
    expires_at: date | None = None


class PantryItemResponse(BaseModel):
    id: int
    family_id: int
    name: str
    quantity: str
    expires_at: date
    is_expired: bool
    days_until_expiry: int
    added_by_name: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PantryListResponse(BaseModel):
    family_id: int
    items: list[PantryItemResponse]
    active_count: int
    expired_count: int
