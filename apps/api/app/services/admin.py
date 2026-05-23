"""Admin panel data and manual billing operations."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models.family import Family, FamilyMember, FamilyRole
from app.models.menu_selection import FamilyMenuSelection
from app.models.subscription import AiUsageLog, AmaWallet, SubscriptionPlan, UserSubscription
from app.models.user import User
from app.services import admin_errors
from app.services import subscription as subscription_service
from app.services.subscription import add_ams, get_wallet_for_user


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _start_of_today_utc() -> datetime:
    now = _now()
    return now.replace(hour=0, minute=0, second=0, microsecond=0)


def _display_name(user: User) -> str:
    parts = [user.first_name, user.last_name]
    name = " ".join(p for p in parts if p).strip()
    if name:
        return name
    if user.username:
        return f"@{user.username}"
    return f"ID {user.telegram_id}"


def get_summary(db: Session) -> dict:
    today_start = _start_of_today_utc()
    total_users = db.query(func.count(User.id)).scalar() or 0
    users_today = (
        db.query(func.count(User.id))
        .filter(User.created_at >= today_start)
        .scalar()
        or 0
    )
    total_families = db.query(func.count(Family.id)).scalar() or 0
    active_subscriptions = (
        db.query(func.count(UserSubscription.id))
        .filter(UserSubscription.status.in_(("active", "trial")))
        .scalar()
        or 0
    )
    ams_used = (
        db.query(func.coalesce(func.sum(AiUsageLog.ams_spent), 0)).scalar() or 0
    )
    ai_requests = db.query(func.count(AiUsageLog.id)).scalar() or 0
    ai_cost = (
        db.query(func.coalesce(func.sum(AiUsageLog.estimated_cost), 0.0)).scalar()
        or 0.0
    )

    return {
        "total_users": total_users,
        "users_today": users_today,
        "total_families": total_families,
        "active_subscriptions": active_subscriptions,
        "ams_used_total": int(ams_used),
        "ai_requests_total": int(ai_requests),
        "ai_estimated_cost_usd": float(ai_cost),
        "errors_last_24h": admin_errors.count_errors_since(24),
    }


def _last_activity(db: Session, user_id: int, user_updated: datetime) -> datetime:
    latest_ai = (
        db.query(func.max(AiUsageLog.created_at))
        .filter(AiUsageLog.user_id == user_id)
        .scalar()
    )
    latest_menu = (
        db.query(func.max(FamilyMenuSelection.selected_at))
        .filter(FamilyMenuSelection.user_id == user_id)
        .scalar()
    )
    candidates = [user_updated]
    if latest_ai:
        candidates.append(latest_ai)
    if latest_menu:
        candidates.append(latest_menu)
    return max(candidates)


def list_users(db: Session, *, limit: int = 200, offset: int = 0) -> list[dict]:
    users = (
        db.query(User)
        .order_by(User.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    result: list[dict] = []
    for user in users:
        sub = subscription_service.get_active_subscription(db, user)
        plan_code = sub.plan_code if sub else "—"
        plan_status = sub.status if sub else "none"
        wallet = get_wallet_for_user(db, user.id)
        menu_count = (
            db.query(func.count(FamilyMenuSelection.id))
            .filter(FamilyMenuSelection.user_id == user.id)
            .scalar()
            or 0
        )
        result.append(
            {
                "id": user.id,
                "display_name": _display_name(user),
                "telegram_id": user.telegram_id,
                "username": user.username,
                "created_at": user.created_at,
                "plan_code": plan_code,
                "plan_status": plan_status,
                "ama_balance": wallet.balance,
                "menu_count": int(menu_count),
                "last_activity_at": _last_activity(db, user.id, user.updated_at),
            }
        )
    return result


def list_families(db: Session, *, limit: int = 200, offset: int = 0) -> list[dict]:
    families = (
        db.query(Family)
        .options(joinedload(Family.members).joinedload(FamilyMember.user))
        .order_by(Family.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    result: list[dict] = []
    for family in families:
        members = family.members or []
        admin_member = next(
            (m for m in members if m.role == FamilyRole.ADMIN.value),
            members[0] if members else None,
        )
        admin_name = admin_member.display_name if admin_member else "—"
        admin_user_id = admin_member.user_id if admin_member else None

        plan_code = "—"
        if admin_user_id:
            admin_user = db.get(User, admin_user_id)
            if admin_user:
                sub = subscription_service.get_active_subscription(db, admin_user)
                if sub:
                    plan_code = sub.plan_code

        result.append(
            {
                "id": family.id,
                "name": family.name,
                "member_count": len(members),
                "plan_code": plan_code,
                "admin_name": admin_name,
                "admin_user_id": admin_user_id,
                "created_at": family.created_at,
            }
        )
    return result


def list_subscriptions(db: Session, *, limit: int = 200) -> list[dict]:
    rows = (
        db.query(UserSubscription, User)
        .join(User, User.id == UserSubscription.user_id)
        .order_by(UserSubscription.id.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": sub.id,
            "user_id": user.id,
            "user_name": _display_name(user),
            "telegram_id": user.telegram_id,
            "plan_code": sub.plan_code,
            "status": sub.status,
            "started_at": sub.started_at,
            "trial_ends_at": sub.trial_ends_at,
            "current_period_ends_at": sub.current_period_ends_at,
            "menu_generations_used": sub.menu_generations_used,
        }
        for sub, user in rows
    ]


def list_ai_usage(db: Session, *, limit: int = 100) -> list[dict]:
    rows = (
        db.query(AiUsageLog, User)
        .join(User, User.id == AiUsageLog.user_id)
        .order_by(AiUsageLog.id.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": log.id,
            "action_type": log.action_type,
            "user_id": user.id,
            "user_name": _display_name(user),
            "family_id": log.family_id,
            "ams_spent": log.ams_spent,
            "model": log.model,
            "input_tokens": log.input_tokens,
            "output_tokens": log.output_tokens,
            "estimated_cost": log.estimated_cost,
            "created_at": log.created_at,
        }
        for log, user in rows
    ]


def grant_subscription(
    db: Session,
    *,
    user_id: int,
    plan_code: str,
    extend_days: int = 30,
    promo_note: str | None = None,
) -> dict:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")

    plan = subscription_service.get_plan(db, plan_code)
    if plan is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Неизвестный тариф")

    subscription_service.seed_subscription_plans(db)
    old = subscription_service.get_active_subscription(db, user)
    if old is not None:
        old.status = "cancelled"
        db.commit()

    now = _now()
    sub = UserSubscription(
        user_id=user.id,
        plan_code=plan_code,
        status="active" if plan_code != "trial" else "trial",
        started_at=now,
        current_period_ends_at=now + timedelta(days=extend_days),
        trial_ends_at=now + timedelta(days=extend_days) if plan_code == "trial" else None,
        menu_generations_used=0,
    )
    db.add(sub)
    db.commit()
    db.refresh(sub)

    wallet = get_wallet_for_user(db, user.id)
    metadata = {"admin_grant": True, "promo_note": promo_note} if promo_note else {"admin_grant": True}
    if plan.monthly_ams > wallet.balance:
        add_ams(
            db,
            wallet,
            plan.monthly_ams - wallet.balance,
            reason="admin_plan_grant",
            metadata=metadata,
        )

    return {
        "user_id": user.id,
        "plan_code": sub.plan_code,
        "status": sub.status,
        "current_period_ends_at": sub.current_period_ends_at,
        "promo_note": promo_note,
    }


def grant_ams(
    db: Session,
    *,
    user_id: int,
    amount: int,
    reason: str = "admin_grant",
) -> dict:
    if amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Сумма должна быть больше нуля",
        )
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")

    wallet = get_wallet_for_user(db, user.id)
    add_ams(
        db,
        wallet,
        amount,
        reason=reason,
        metadata={"admin_grant": True},
    )
    db.refresh(wallet)
    return {"user_id": user.id, "amount": amount, "new_balance": wallet.balance}


def list_plans(db: Session) -> list[dict]:
    plans = (
        db.query(SubscriptionPlan)
        .filter(SubscriptionPlan.is_active.is_(True))
        .order_by(SubscriptionPlan.sort_order)
        .all()
    )
    return [
        {
            "code": p.code,
            "name": p.name,
            "price_rub": p.price_rub,
            "monthly_ams": p.monthly_ams,
        }
        for p in plans
    ]
