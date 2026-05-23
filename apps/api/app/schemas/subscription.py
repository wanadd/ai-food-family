from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class PlanFeatureFlags(BaseModel):
    shopping: bool = True
    pantry: bool = True
    notifications: bool = True
    nutrition_profile: bool = True
    nutritionist_basic: bool = True
    nutritionist_extended: bool = False
    family_mode: bool = False
    virtual_members: bool = False
    macros: bool = False
    sport_goals: bool = False
    ai_care: bool = False


class SubscriptionPlanResponse(BaseModel):
    code: str
    name: str
    price_rub: int
    max_profiles: int
    monthly_menu_generations: int | None
    monthly_ams: int
    features: dict[str, Any]
    is_current: bool = False


class AmaTransactionItem(BaseModel):
    id: int
    user_name: str
    amount: int
    reason: str
    reason_label: str
    created_at: datetime


class SubscriptionOverviewResponse(BaseModel):
    plan_code: str
    plan_name: str
    status: str
    price_rub: int
    trial_ends_at: datetime | None = None
    current_period_ends_at: datetime | None = None
    menu_generations_used: int
    menu_generations_limit: int | None
    menu_generations_remaining: int | None
    ama_balance: int
    ai_actions_enabled: bool
    trial_days_left: int | None = None
    plans: list[SubscriptionPlanResponse]
    ama_costs: dict[str, int]
    is_family_billing: bool = False
    family_name: str | None = None
    is_family_admin: bool = False
    can_spend_ama: bool = True
    ama_transactions: list[AmaTransactionItem] = Field(default_factory=list)


class SelectPlanRequest(BaseModel):
    plan_code: str = Field(min_length=1, max_length=32)
