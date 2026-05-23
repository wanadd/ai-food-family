from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_verified_user
from app.models.user import User
from app.schemas.subscription import (
    SelectPlanRequest,
    SubscriptionOverviewResponse,
    SubscriptionPlanResponse,
)
from app.models.subscription import SubscriptionPlan
from app.services import subscription as subscription_service
from app.services.subscription_catalog import AMA_COSTS, TRIAL_MENU_GENERATIONS

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


@router.get("/me", response_model=SubscriptionOverviewResponse)
def get_subscription_overview(
    user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
) -> SubscriptionOverviewResponse:
    sub, plan, wallet = subscription_service.get_current_subscription(db, user)
    subscription_service._refresh_subscription_status(db, sub)
    db.refresh(sub)

    limit = subscription_service._menu_generation_limit(plan, sub)
    remaining: int | None = None
    if limit is not None:
        remaining = max(0, limit - sub.menu_generations_used)

    trial_days_left: int | None = None
    if sub.trial_ends_at and sub.status == "trial":
        delta = sub.trial_ends_at - subscription_service._now()
        trial_days_left = max(0, delta.days)

    all_plans = (
        db.query(SubscriptionPlan)
        .filter(SubscriptionPlan.is_active.is_(True))
        .order_by(SubscriptionPlan.sort_order)
        .all()
    )

    return SubscriptionOverviewResponse(
        plan_code=sub.plan_code,
        plan_name=plan.name,
        status=sub.status,
        price_rub=plan.price_rub,
        trial_ends_at=sub.trial_ends_at,
        current_period_ends_at=sub.current_period_ends_at,
        menu_generations_used=sub.menu_generations_used,
        menu_generations_limit=limit,
        menu_generations_remaining=remaining,
        ama_balance=wallet.balance,
        ai_actions_enabled=subscription_service.ai_actions_allowed(sub),
        trial_days_left=trial_days_left,
        plans=[
            SubscriptionPlanResponse(
                code=p.code,
                name=p.name,
                price_rub=p.price_rub,
                max_profiles=p.max_profiles,
                monthly_menu_generations=(
                    TRIAL_MENU_GENERATIONS
                    if p.code == "trial"
                    else p.monthly_menu_generations
                ),
                monthly_ams=p.monthly_ams,
                features=p.features or {},
                is_current=p.code == sub.plan_code,
            )
            for p in all_plans
            if p.code != "trial"
        ],
        ama_costs=AMA_COSTS,
    )


@router.post("/select-plan", response_model=SubscriptionOverviewResponse)
def select_plan_stub(
    payload: SelectPlanRequest,
    user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
) -> SubscriptionOverviewResponse:
    subscription_service.select_plan_stub(db, user, payload.plan_code)
    return get_subscription_overview(user=user, db=db)
