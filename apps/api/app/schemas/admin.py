from datetime import datetime

from pydantic import BaseModel, Field


class AdminSummaryResponse(BaseModel):
    total_users: int
    users_today: int
    total_families: int
    active_subscriptions: int
    ams_used_total: int
    ai_requests_total: int
    ai_estimated_cost_usd: float
    errors_last_24h: int


class AdminUserRow(BaseModel):
    id: int
    display_name: str
    telegram_id: int
    username: str | None
    created_at: datetime
    plan_code: str
    plan_status: str
    ama_balance: int
    menu_count: int
    last_activity_at: datetime


class AdminFamilyRow(BaseModel):
    id: int
    name: str
    member_count: int
    plan_code: str
    admin_name: str
    admin_user_id: int | None
    created_at: datetime


class AdminSubscriptionRow(BaseModel):
    id: int
    user_id: int
    user_name: str
    telegram_id: int
    plan_code: str
    status: str
    started_at: datetime
    trial_ends_at: datetime | None
    current_period_ends_at: datetime | None
    menu_generations_used: int


class AdminAiUsageRow(BaseModel):
    id: int
    action_type: str
    user_id: int
    user_name: str
    family_id: int | None
    ams_spent: int
    model: str | None
    input_tokens: int | None
    output_tokens: int | None
    estimated_cost: float | None
    created_at: datetime


class AdminGrantSubscriptionRequest(BaseModel):
    user_id: int
    plan_code: str
    extend_days: int = Field(default=30, ge=1, le=3650)
    promo_note: str | None = Field(default=None, max_length=500)


class AdminGrantAmsRequest(BaseModel):
    user_id: int
    amount: int = Field(ge=1, le=1_000_000)
    reason: str = Field(default="admin_grant", max_length=64)


class AdminGrantResponse(BaseModel):
    user_id: int
    message: str


class AdminBackupRow(BaseModel):
    id: str
    path: str
    created_at: str
    size_bytes: int
    has_database: bool
    has_env: bool


class AdminBackupCreateResponse(BaseModel):
    id: str
    path: str
    created_at: str
    size_bytes: str
    message: str


class AdminPlanOption(BaseModel):
    code: str
    name: str
    price_rub: int
    monthly_ams: int
