from datetime import datetime

from pydantic import BaseModel, Field


class ShoppingListItem(BaseModel):
    id: str
    name: str
    amount: str
    amounts: list[str] = Field(default_factory=list)
    category: str
    checked: bool = False
    checked_by_user_id: int | None = None
    checked_by_name: str | None = None
    checked_at: datetime | None = None


class ShoppingListResponse(BaseModel):
    family_id: int
    menu_title: str | None = None
    items: list[ShoppingListItem]
    total_count: int
    checked_count: int
    updated_at: datetime


class ToggleItemRequest(BaseModel):
    checked: bool
