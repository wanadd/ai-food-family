from datetime import datetime

from pydantic import BaseModel, Field


class AdminSummaryResponse(BaseModel):
    total_users: int
    users_today: int
    active_today: int
    active_7d: int
    total_families: int
    active_subscriptions: int
    free_users: int
    total_ams_balance: int
    ams_used_total: int
    ai_requests_total: int
    ai_estimated_cost_usd: float
    openai_cost_today_usd: float
    openai_cost_month_usd: float
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
    family_name: str | None = None
    is_blocked: bool = False
    status: str = "inactive"


class AdminUserDetail(BaseModel):
    id: int
    display_name: str
    telegram_id: int
    username: str | None
    created_at: datetime
    last_activity_at: datetime
    family_name: str | None
    plan_code: str
    plan_status: str
    ama_balance: int
    is_blocked: bool
    ai_requests: int
    ams_spent: int
    openai_cost_usd: float
    menu_count: int


class AdminFamilyRow(BaseModel):
    id: int
    name: str
    member_count: int
    plan_code: str
    admin_name: str
    admin_user_id: int | None
    created_at: datetime
    ama_balance: int = 0
    openai_cost_usd: float = 0.0
    is_blocked: bool = False


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


class AdminOpenAiCategory(BaseModel):
    category: str
    requests: int
    input_tokens: int
    output_tokens: int
    total_tokens: int
    openai_cost_usd: float
    ams_spent: int
    avg_cost_usd: float


class AdminOpenAiStats(BaseModel):
    period: str
    requests: int
    openai_cost_usd: float
    input_tokens: int
    output_tokens: int
    total_tokens: int
    ams_spent: int
    menu_generations: int
    avg_request_cost_usd: float
    avg_menu_cost_usd: float
    avg_user_cost_usd: float
    avg_family_cost_usd: float
    categories: list[AdminOpenAiCategory]


class AdminAmsSummary(BaseModel):
    credited_total: int
    debited_total: int
    user_balance_total: int
    family_balance_total: int
    spent_today: int
    spent_month: int


class AdminAmaTransactionRow(BaseModel):
    id: int
    created_at: datetime
    user_id: int | None
    family_id: int | None
    amount: int
    reason: str
    type: str


class AdminErrorRow(BaseModel):
    id: int
    error_type: str
    user_id: int | None
    family_id: int | None
    endpoint: str | None
    message: str
    status: int | None
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


class AdminGrantFamilyAmsRequest(BaseModel):
    family_id: int
    amount: int = Field(ge=1, le=1_000_000)
    reason: str = Field(default="admin_grant", max_length=64)


class AdminDeductAmsRequest(BaseModel):
    user_id: int
    amount: int = Field(ge=1, le=1_000_000)
    reason: str = Field(default="admin_deduct", max_length=64)


class AdminBlockRequest(BaseModel):
    blocked: bool = True


class AdminGrantResponse(BaseModel):
    user_id: int | None = None
    family_id: int | None = None
    message: str


class AdminPingResponse(BaseModel):
    ok: bool = True


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


class AdminSubscriptionInfo(BaseModel):
    id: int
    plan_code: str
    status: str
    started_at: datetime
    trial_ends_at: datetime | None = None
    current_period_ends_at: datetime | None = None
    family_id: int | None = None
    grant_source: str = "system"
    grant_reason: str | None = None
    kind: str = "paid"


class AdminAmsTransactionItem(BaseModel):
    id: int
    amount: int
    type: str
    reason: str
    created_at: datetime
    comment: str | None = None


class AdminAmsBlock(BaseModel):
    balance: int
    credited_total: int
    spent_total: int
    transactions: list[AdminAmsTransactionItem] = []


class AdminUserCard(BaseModel):
    id: int
    display_name: str
    telegram_id: int
    username: str | None
    created_at: datetime
    last_activity_at: datetime
    family_id: int | None = None
    family_name: str | None = None
    is_blocked: bool
    blocked_at: datetime | None = None
    blocked_reason: str | None = None
    is_deleted: bool = False
    phone_number: str | None = None
    legal_accepted: bool = False
    profile_completed: bool = False
    subscription: AdminSubscriptionInfo | None = None
    ams: AdminAmsBlock
    ai_requests: int
    ams_spent: int
    openai_cost_usd: float
    menu_count: int


class AdminFamilyMemberItem(BaseModel):
    id: int
    user_id: int | None
    display_name: str
    role: str
    is_virtual: bool


class AdminFamilyCard(BaseModel):
    id: int
    name: str
    is_blocked: bool
    blocked_at: datetime | None = None
    blocked_reason: str | None = None
    created_at: datetime
    member_count: int
    admin_user_id: int | None
    admin_name: str
    members: list[AdminFamilyMemberItem]
    subscription: AdminSubscriptionInfo | None = None
    ams: AdminAmsBlock


class AdminHardDeleteRequest(BaseModel):
    confirmation: str = Field(min_length=1, max_length=32)


class AdminBlockReasonRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=500)


class AdminSubscriptionActionRequest(BaseModel):
    plan_code: str = Field(max_length=32)
    days: int = Field(default=30, ge=1, le=3650)
    reason: str | None = Field(default=None, max_length=500)
    expires_at: datetime | None = None
    as_trial: bool = False


class AdminSubscriptionExtendRequest(BaseModel):
    days: int = Field(default=30, ge=1, le=3650)
    reason: str | None = Field(default=None, max_length=500)


class AdminAmsActionRequest(BaseModel):
    amount: int = Field(ge=1, le=1_000_000)
    reason: str | None = Field(default=None, max_length=64)
    comment: str | None = Field(default=None, max_length=500)


class AdminFamilyRenameRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)


class AdminFamilyTransferRequest(BaseModel):
    new_admin_user_id: int
