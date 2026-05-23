from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_app_scope, get_verified_user
from app.models.user import User
from app.schemas.subscription import (
    AmaTransactionItem,
    SelectPlanRequest,
    SubscriptionOverviewResponse,
    SubscriptionPlanResponse,
)
from app.models.subscription import SubscriptionPlan
from app.services.app_scope import AppScope
from app.services import subscription as subscription_service
from app.services.subscription_catalog import AMA_COSTS, TRIAL_MENU_GENERATIONS

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


@router.get("/me", response_model=SubscriptionOverviewResponse)
def get_subscription_overview(
    user: User = Depends(get_verified_user),
    scope: AppScope = Depends(get_app_scope),
    db: Session = Depends(get_db),
) -> SubscriptionOverviewResponse:
    sub, plan, wallet, billing_meta = subscription_service.get_current_subscription(
        db, user, scope
    )
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

    tx_rows = subscription_service.list_ama_transactions(db, wallet, limit=25)

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
        is_family_billing=billing_meta["is_family_billing"],
        family_name=billing_meta.get("family_name"),
        is_family_admin=billing_meta["is_family_admin"],
        can_spend_ama=billing_meta["can_spend_ama"],
        ama_transactions=[AmaTransactionItem(**row) for row in tx_rows],
    )


@router.post("/select-plan", response_model=SubscriptionOverviewResponse)
def select_plan_stub(
    payload: SelectPlanRequest,
    user: User = Depends(get_verified_user),
    scope: AppScope = Depends(get_app_scope),
    db: Session = Depends(get_db),
) -> SubscriptionOverviewResponse:
    family_id = scope.family_id if scope.is_family else None
    if family_id and not subscription_service.is_family_admin(db, user, family_id):
        from fastapi import HTTPException, status

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Менять семейный тариф может только администратор",
        )
    subscription_service.select_plan_stub(
        db, user, payload.plan_code, family_id=family_id
    )
    return get_subscription_overview(user=user, scope=scope, db=db)
