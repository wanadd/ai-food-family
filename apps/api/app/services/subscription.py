from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.subscription import (
    AiUsageLog,
    AmaTransaction,
    AmaWallet,
    SubscriptionPlan,
    UserSubscription,
)
from app.models.user import User
from app.services.app_scope import AppScope
from app.services.subscription_catalog import (
    AMA_COSTS,
    PLAN_SEEDS,
    TRIAL_DAYS,
    TRIAL_MENU_GENERATIONS,
)


@dataclass
class MenuGenerationAccess:
    allowed: bool
    uses_quota: bool
    uses_ams: bool
    message: str | None = None
    code: str | None = None
    ams_cost: int = 0
    can_pay_with_ams: bool = False


def seed_subscription_plans(db: Session) -> None:
    for item in PLAN_SEEDS:
        existing = (
            db.query(SubscriptionPlan)
            .filter(SubscriptionPlan.code == item["code"])
            .one_or_none()
        )
        if existing is None:
            db.add(SubscriptionPlan(**item))
        else:
            for key, value in item.items():
                setattr(existing, key, value)
    db.commit()


def get_plan(db: Session, plan_code: str) -> SubscriptionPlan | None:
    return (
        db.query(SubscriptionPlan)
        .filter(SubscriptionPlan.code == plan_code, SubscriptionPlan.is_active.is_(True))
        .one_or_none()
    )


def _now() -> datetime:
    return datetime.now(timezone.utc)


def get_active_subscription(db: Session, user: User) -> UserSubscription | None:
    return (
        db.query(UserSubscription)
        .filter(
            UserSubscription.user_id == user.id,
            UserSubscription.status.in_(("active", "trial")),
        )
        .order_by(UserSubscription.id.desc())
        .first()
    )


def ensure_user_billing(db: Session, user: User) -> UserSubscription:
    seed_subscription_plans(db)
    sub = get_active_subscription(db, user)
    if sub is not None:
        _refresh_subscription_status(db, sub)
        _ensure_wallet(db, user, sub)
        return sub

    now = _now()
    sub = UserSubscription(
        user_id=user.id,
        plan_code="trial",
        status="trial",
        started_at=now,
        trial_ends_at=now + timedelta(days=TRIAL_DAYS),
        menu_generations_used=0,
    )
    db.add(sub)
    db.commit()
    db.refresh(sub)

    trial_plan = get_plan(db, "trial")
    initial_ams = trial_plan.monthly_ams if trial_plan else 200
    wallet = _get_or_create_user_wallet(db, user.id)
    if wallet.balance == 0:
        add_ams(
            db,
            wallet,
            initial_ams,
            reason="trial_welcome",
            metadata={"plan_code": "trial"},
        )
    return sub


def ensure_all_users_have_billing(db: Session) -> None:
    users = db.query(User).all()
    for user in users:
        ensure_user_billing(db, user)


def _ensure_wallet(db: Session, user: User, sub: UserSubscription) -> AmaWallet:
    return _get_or_create_user_wallet(db, user.id)


def _get_or_create_user_wallet(db: Session, user_id: int) -> AmaWallet:
    wallet = (
        db.query(AmaWallet)
        .filter(AmaWallet.user_id == user_id, AmaWallet.family_id.is_(None))
        .one_or_none()
    )
    if wallet is None:
        wallet = AmaWallet(user_id=user_id, balance=0)
        db.add(wallet)
        db.commit()
        db.refresh(wallet)
    return wallet


def get_wallet_for_user(db: Session, user_id: int) -> AmaWallet:
    return _get_or_create_user_wallet(db, user_id)


def _refresh_subscription_status(db: Session, sub: UserSubscription) -> None:
    if sub.status not in ("active", "trial"):
        return
    if sub.plan_code == "trial":
        expired = False
        if sub.trial_ends_at and _now() > sub.trial_ends_at:
            expired = True
        if sub.menu_generations_used >= TRIAL_MENU_GENERATIONS:
            expired = True
        if expired and sub.status == "trial":
            sub.status = "expired"
            db.commit()


def get_current_subscription(
    db: Session, user: User
) -> tuple[UserSubscription, SubscriptionPlan, AmaWallet]:
    sub = ensure_user_billing(db, user)
    plan = get_plan(db, sub.plan_code)
    if plan is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Тариф не найден",
        )
    wallet = get_wallet_for_user(db, user.id)
    return sub, plan, wallet


def ai_actions_allowed(sub: UserSubscription) -> bool:
    _ = sub  # status refreshed by caller
    return sub.status in ("active", "trial")


def check_feature_access(
    db: Session, user: User, feature: str
) -> bool:
    sub, plan, _ = get_current_subscription(db, user)
    if not ai_actions_allowed(sub) and feature.startswith("ai_"):
        return False
    features = plan.features or {}
    value = features.get(feature)
    if value is True:
        return True
    if value in ("limited", "basic"):
        return True
    if feature in ("shopping", "pantry", "notifications", "nutrition_profile"):
        return bool(value)
    return bool(value)


def _menu_generation_limit(plan: SubscriptionPlan, sub: UserSubscription) -> int | None:
    if plan.monthly_menu_generations is None:
        return None
    if sub.plan_code == "trial":
        return TRIAL_MENU_GENERATIONS
    return plan.monthly_menu_generations


def evaluate_menu_generation(
    db: Session, user: User, scope: AppScope
) -> MenuGenerationAccess:
    sub, plan, wallet = get_current_subscription(db, user)
    _refresh_subscription_status(db, sub)
    db.refresh(sub)

    if not ai_actions_allowed(sub):
        return MenuGenerationAccess(
            allowed=False,
            uses_quota=False,
            uses_ams=False,
            code="trial_expired",
            message=(
                "Пробный период закончился. Выберите тариф, чтобы снова "
                "генерировать меню и использовать AI."
            ),
        )

    limit = _menu_generation_limit(plan, sub)
    if limit is None:
        return MenuGenerationAccess(allowed=True, uses_quota=True, uses_ams=False)

    if sub.menu_generations_used < limit:
        return MenuGenerationAccess(allowed=True, uses_quota=True, uses_ams=False)

    ams_cost = AMA_COSTS["menu_generation_extra"]
    can_pay = wallet.balance >= ams_cost
    return MenuGenerationAccess(
        allowed=can_pay,
        uses_quota=False,
        uses_ams=can_pay,
        code="menu_generation_limit",
        message=(
            "Лимит генераций закончился. Перейдите на тариф выше "
            "или используйте Амы."
        ),
        ams_cost=ams_cost,
        can_pay_with_ams=can_pay,
    )


def assert_menu_generation_allowed(
    db: Session, user: User, scope: AppScope
) -> MenuGenerationAccess:
    access = evaluate_menu_generation(db, user, scope)
    if not access.allowed:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "code": access.code,
                "message": access.message,
                "ams_cost": access.ams_cost,
                "can_pay_with_ams": access.can_pay_with_ams,
            },
        )
    return access


def commit_menu_generation(
    db: Session,
    user: User,
    scope: AppScope,
    access: MenuGenerationAccess,
    *,
    used_ai: bool,
    model: str | None = None,
) -> None:
    sub, _, wallet = get_current_subscription(db, user)
    ams_spent = 0

    if access.uses_ams:
        ams_spent = AMA_COSTS["menu_generation_extra"]
        spend_ams(
            db,
            wallet,
            ams_spent,
            reason="menu_generation_extra",
            metadata={"scope": scope.mode},
        )
    elif access.uses_quota:
        sub.menu_generations_used += 1
        db.commit()

    log_ai_usage(
        db,
        user_id=user.id,
        family_id=scope.family_id,
        action_type="menu_generate",
        ams_spent=ams_spent,
        model=model if used_ai else None,
        metadata={"used_ai": used_ai, "plan_code": sub.plan_code},
    )


def require_ai_action(
    db: Session,
    user: User,
    scope: AppScope,
    action_type: str,
    *,
    ama_cost: int | None = None,
) -> int:
    sub, plan, wallet = get_current_subscription(db, user)
    _refresh_subscription_status(db, sub)
    db.refresh(sub)

    if not ai_actions_allowed(sub):
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "code": "trial_expired",
                "message": (
                    "Пробный период закончился. Выберите тариф для "
                    "дополнительных AI-действий."
                ),
            },
        )

    cost = ama_cost if ama_cost is not None else AMA_COSTS.get(action_type, 0)
    if cost <= 0:
        return 0

    if wallet.balance < cost:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "code": "insufficient_ams",
                "message": (
                    f"Недостаточно Амов. Нужно {cost}, на балансе {wallet.balance}. "
                    "Пополните баланс или смените тариф."
                ),
                "ams_cost": cost,
                "ams_balance": wallet.balance,
            },
        )

    spend_ams(
        db,
        wallet,
        cost,
        reason=action_type,
        metadata={"scope": scope.mode},
    )
    return cost


def spend_ams(
    db: Session,
    wallet: AmaWallet,
    amount: int,
    *,
    reason: str,
    metadata: dict[str, Any] | None = None,
) -> AmaTransaction:
    if amount <= 0:
        raise ValueError("amount must be positive")
    if wallet.balance < amount:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Недостаточно Амов",
        )
    wallet.balance -= amount
    tx = AmaTransaction(
        wallet_id=wallet.id,
        amount=-amount,
        type="debit",
        reason=reason,
        metadata_json=metadata,
    )
    db.add(tx)
    db.commit()
    db.refresh(wallet)
    return tx


def add_ams(
    db: Session,
    wallet: AmaWallet,
    amount: int,
    *,
    reason: str,
    metadata: dict[str, Any] | None = None,
) -> AmaTransaction:
    if amount <= 0:
        raise ValueError("amount must be positive")
    wallet.balance += amount
    tx = AmaTransaction(
        wallet_id=wallet.id,
        amount=amount,
        type="credit",
        reason=reason,
        metadata_json=metadata,
    )
    db.add(tx)
    db.commit()
    db.refresh(wallet)
    return tx


def log_ai_usage(
    db: Session,
    *,
    user_id: int,
    family_id: int | None,
    action_type: str,
    ams_spent: int = 0,
    model: str | None = None,
    input_tokens: int | None = None,
    output_tokens: int | None = None,
    estimated_cost: float | None = None,
    metadata: dict[str, Any] | None = None,
) -> AiUsageLog:
    entry = AiUsageLog(
        user_id=user_id,
        family_id=family_id,
        action_type=action_type,
        ams_spent=ams_spent,
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        estimated_cost=estimated_cost,
        metadata_json=metadata,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def reset_monthly_limits(db: Session) -> None:
    """Placeholder for cron: reset menu_generations_used on paid plans."""
    subs = (
        db.query(UserSubscription)
        .filter(
            UserSubscription.status == "active",
            UserSubscription.plan_code != "trial",
        )
        .all()
    )
    for sub in subs:
        sub.menu_generations_used = 0
    db.commit()


def select_plan_stub(
    db: Session, user: User, plan_code: str
) -> UserSubscription:
    """UI stub: switch plan without payment (for testing / preview)."""
    plan = get_plan(db, plan_code)
    if plan is None or plan_code == "trial":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Этот тариф нельзя выбрать вручную",
        )

    old = get_active_subscription(db, user)
    if old is not None:
        old.status = "cancelled"
        db.commit()

    now = _now()
    sub = UserSubscription(
        user_id=user.id,
        plan_code=plan_code,
        status="active",
        started_at=now,
        current_period_ends_at=now + timedelta(days=30),
        menu_generations_used=0,
    )
    db.add(sub)
    db.commit()
    db.refresh(sub)

    wallet = get_wallet_for_user(db, user.id)
    if wallet.balance < plan.monthly_ams:
        add_ams(
            db,
            wallet,
            plan.monthly_ams - wallet.balance,
            reason="plan_change_grant",
            metadata={"plan_code": plan_code},
        )
    return sub
