from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.shopping_category import ShoppingCategoryResponse


class ShoppingListItem(BaseModel):
    id: str
    name: str
    category: str
    quantity: str = ""
    unit: str = "шт"
    amount: str = ""
    amounts: list[str] = Field(default_factory=list)
    note: str | None = None
    source: str = "menu"
    checked: bool = False
    checked_by_user_id: int | None = None
    checked_by_name: str | None = None
    checked_at: datetime | None = None
    linked_pantry_item_id: int | None = None
    added_to_pantry: bool = False
    created_by_user_id: int | None = None


class ShoppingListResponse(BaseModel):
    scope_mode: str
    user_id: int | None = None
    family_id: int | None = None
    menu_title: str | None = None
    items: list[ShoppingListItem]
    categories: list[ShoppingCategoryResponse] = Field(default_factory=list)
    total_count: int
    checked_count: int
    updated_at: datetime


class ShoppingItemCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    category: str = Field(min_length=1, max_length=120)
    quantity: str = Field(default="1", max_length=32)
    unit: str = Field(default="шт", max_length=32)
    note: str | None = Field(default=None, max_length=200)
    is_food: bool | None = None


class ShoppingItemUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    category: str | None = Field(default=None, min_length=1, max_length=120)
    quantity: str | None = Field(default=None, max_length=32)
    unit: str | None = Field(default=None, max_length=32)
    note: str | None = None
    checked: bool | None = None
    remove_from_pantry: bool = False


class ToggleItemRequest(BaseModel):
    checked: bool
    remove_from_pantry: bool = False
