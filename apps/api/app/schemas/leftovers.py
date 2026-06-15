from datetime import date, datetime

from pydantic import BaseModel, Field


class PreparedDishOut(BaseModel):
    id: int
    recipe_id: int | None
    recipe_title: str | None
    remaining_servings: float
    total_servings: float
    serving_unit: str
    meal_type: str | None = None
    planned_date: date | None = None
    day_index: int | None = None
    menu_selection_id: int | None = None
    batch_status: str
    source: str = "cooking_batch"
    can_manage: bool = False


class StockProductOut(BaseModel):
    id: int
    title: str
    quantity: str
    unit: str
    category: str
    source: str = "inventory"


class StocksSummaryOut(BaseModel):
    products_count: int
    prepared_dishes_count: int
    total_positions_count: int


class StocksOverviewOut(BaseModel):
    products: list[StockProductOut]
    prepared_dishes: list[PreparedDishOut]
    summary: StocksSummaryOut


class CookingBatchCreateIn(BaseModel):
    family_id: int | None = None
    recipe_id: int | None = None
    recipe_title: str = Field(min_length=1, max_length=300)
    menu_selection_id: int | None = None
    day_index: int | None = None
    planned_date: date | None = None
    meal_type: str | None = None
    total_servings: float = Field(default=1.0, ge=0)
    serving_unit: str = Field(default="порция", max_length=32)


class CookingBatchUseIn(BaseModel):
    servings_used: float = Field(gt=0)
    note: str | None = Field(default=None, max_length=500)


class CookingBatchAdjustIn(BaseModel):
    remaining_servings: float = Field(ge=0)
    note: str | None = Field(default=None, max_length=500)


class CookingBatchOut(BaseModel):
    id: int
    family_id: int | None
    owner_user_id: int | None
    recipe_id: int | None
    recipe_title: str | None
    menu_selection_id: int | None
    day_index: int | None
    planned_date: date | None
    meal_type: str | None
    batch_status: str
    total_servings: float
    remaining_servings: float
    serving_unit: str
    cooked_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
