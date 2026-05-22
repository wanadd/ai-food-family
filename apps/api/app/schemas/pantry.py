from datetime import date, datetime

from pydantic import BaseModel, Field


class PantryItemCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    quantity: str = Field(min_length=1, max_length=80)
    expires_at: date
    source: str = "manual"
    unit: str = ""


class PantryItemUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    quantity: str | None = Field(default=None, min_length=1, max_length=80)
    expires_at: date | None = None


class PantryItemResponse(BaseModel):
    id: int
    scope_mode: str
    user_id: int | None = None
    family_id: int | None = None
    name: str
    quantity: str
    unit: str = ""
    source: str = "manual"
    expires_at: date
    is_expired: bool
    days_until_expiry: int
    added_by_name: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PantryListResponse(BaseModel):
    scope_mode: str
    user_id: int | None = None
    family_id: int | None = None
    items: list[PantryItemResponse]
    active_count: int
    expired_count: int
