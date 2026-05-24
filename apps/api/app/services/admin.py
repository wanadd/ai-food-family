"""Admin panel data and manual billing operations."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models.family import Family, FamilyMember, FamilyRole
from app.models.menu_selection import FamilyMenuSelection
from app.models.subscription import (
    AiUsageLog,
    AmaTransaction,
    AmaWallet,
    SubscriptionPlan,
    UserSubscription,
)
from app.models.user import User
from app.services import admin_errors
from app.services import subscription as subscription_service
from app.services.admin_audit import log_admin_action
from app.services.subscription import (
    _get_or_create_family_wallet,
    add_ams,
    get_wallet_for_user,
    spend_ams,
)


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


def _start_of_month_utc() -> datetime:
    now = _now()
    return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def get_summary(db: Session) -> dict:
    today_start = _start_of_today_utc()
    week_start = _now() - timedelta(days=7)
    month_start = _start_of_month_utc()
    total_users = db.query(func.count(User.id)).scalar() or 0
    users_today = (
        db.query(func.count(User.id))
        .filter(User.created_at >= today_start)
        .scalar()
        or 0
    )
    active_today = (
        db.query(func.count(func.distinct(AiUsageLog.user_id)))
        .filter(AiUsageLog.created_at >= today_start)
        .scalar()
        or 0
    )
    active_7d = (
        db.query(func.count(func.distinct(AiUsageLog.user_id)))
        .filter(AiUsageLog.created_at >= week_start)
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
    paid_plans = ("basic", "family", "pro", "premium")
    paid_users = (
        db.query(func.count(func.distinct(UserSubscription.user_id)))
        .filter(
            UserSubscription.status.in_(("active", "trial")),
            UserSubscription.plan_code.in_(paid_plans),
        )
        .scalar()
        or 0
    )
    free_users = max(total_users - paid_users, 0)
    ams_used = (
        db.query(func.coalesce(func.sum(AiUsageLog.ams_spent), 0)).scalar() or 0
    )
    ai_requests = db.query(func.count(AiUsageLog.id)).scalar() or 0
    ai_cost = (
        db.query(func.coalesce(func.sum(AiUsageLog.estimated_cost), 0.0)).scalar()
        or 0.0
    )
    openai_today = (
        db.query(func.coalesce(func.sum(AiUsageLog.estimated_cost), 0.0))
        .filter(AiUsageLog.created_at >= today_start)
        .scalar()
        or 0.0
    )
    openai_month = (
        db.query(func.coalesce(func.sum(AiUsageLog.estimated_cost), 0.0))
        .filter(AiUsageLog.created_at >= month_start)
        .scalar()
        or 0.0
    )
    user_ams_balance = (
        db.query(func.coalesce(func.sum(AmaWallet.balance), 0))
        .filter(AmaWallet.user_id.isnot(None))
        .scalar()
        or 0
    )
    family_ams_balance = (
        db.query(func.coalesce(func.sum(AmaWallet.balance), 0))
        .filter(AmaWallet.family_id.isnot(None))
        .scalar()
        or 0
    )

    return {
        "total_users": total_users,
        "users_today": users_today,
        "active_today": int(active_today),
        "active_7d": int(active_7d),
        "total_families": total_families,
        "active_subscriptions": active_subscriptions,
        "free_users": int(free_users),
        "total_ams_balance": int(user_ams_balance) + int(family_ams_balance),
        "ams_used_total": int(ams_used),
        "ai_requests_total": int(ai_requests),
        "ai_estimated_cost_usd": float(ai_cost),
        "openai_cost_today_usd": float(openai_today),
        "openai_cost_month_usd": float(openai_month),
        "errors_last_24h": admin_errors.count_errors_since(24, db=db),
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


def _user_family_name(db: Session, user_id: int) -> str | None:
    member = (
        db.query(FamilyMember)
        .filter(FamilyMember.user_id == user_id)
        .one_or_none()
    )
    if member is None:
        return None
    family = db.get(Family, member.family_id)
    return family.name if family else None


def list_users(
    db: Session,
    *,
    limit: int = 200,
    offset: int = 0,
    q: str | None = None,
    status_filter: str = "all",
) -> list[dict]:
    query = db.query(User)
    if q:
        needle = q.strip().lower()
        if needle.isdigit():
            query = query.filter(User.telegram_id == int(needle))
        else:
            query = query.filter(
                func.lower(func.coalesce(User.username, "")).contains(needle)
                | func.lower(func.coalesce(User.first_name, "")).contains(needle)
                | func.lower(func.coalesce(User.last_name, "")).contains(needle)
            )
    users = query.order_by(User.created_at.desc()).offset(offset).limit(limit).all()
    paid_plans = {"basic", "family", "pro", "premium"}
    week_start = _now() - timedelta(days=7)
    result: list[dict] = []
    for user in users:
        sub = subscription_service.get_active_subscription(db, user)
        plan_code = sub.plan_code if sub else "free"
        plan_status = sub.status if sub else "none"
        is_paid = plan_code in paid_plans and plan_status in ("active", "trial")
        last_at = _last_activity(db, user.id, user.updated_at)
        is_active = last_at >= week_start
        blocked = bool(getattr(user, "is_blocked", False))

        if status_filter == "blocked" and not blocked:
            continue
        if status_filter == "active" and not is_active:
            continue
        if status_filter == "free" and is_paid:
            continue
        if status_filter == "paid" and not is_paid:
            continue

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
                "last_activity_at": last_at,
                "family_name": _user_family_name(db, user.id),
                "is_blocked": blocked,
                "status": "blocked" if blocked else ("active" if is_active else "inactive"),
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

        wallet = (
            db.query(AmaWallet)
            .filter(AmaWallet.family_id == family.id, AmaWallet.user_id.is_(None))
            .one_or_none()
        )
        ai_cost = (
            db.query(func.coalesce(func.sum(AiUsageLog.estimated_cost), 0.0))
            .filter(AiUsageLog.family_id == family.id)
            .scalar()
            or 0.0
        )
        result.append(
            {
                "id": family.id,
                "name": family.name,
                "member_count": len(members),
                "plan_code": plan_code,
                "admin_name": admin_name,
                "admin_user_id": admin_user_id,
                "created_at": family.created_at,
                "ama_balance": wallet.balance if wallet else 0,
                "openai_cost_usd": float(ai_cost),
                "is_blocked": bool(getattr(family, "is_blocked", False)),
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
    admin_user_id: int | None = None,
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

    result = {
        "user_id": user.id,
        "plan_code": sub.plan_code,
        "status": sub.status,
        "current_period_ends_at": sub.current_period_ends_at,
        "promo_note": promo_note,
    }
    log_admin_action(
        db,
        admin_user_id=admin_user_id,
        action_type="grant_subscription",
        target_type="user",
        target_id=user.id,
        metadata=result,
    )
    return result


def grant_ams(
    db: Session,
    *,
    user_id: int,
    amount: int,
    reason: str = "admin_grant",
    admin_user_id: int | None = None,
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
    result = {"user_id": user.id, "amount": amount, "new_balance": wallet.balance}
    log_admin_action(
        db,
        admin_user_id=admin_user_id,
        action_type="grant_ams",
        target_type="user",
        target_id=user.id,
        metadata={"amount": amount, "reason": reason},
    )
    return result


def deduct_ams(
    db: Session,
    *,
    user_id: int,
    amount: int,
    reason: str = "admin_deduct",
    admin_user_id: int | None = None,
) -> dict:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    wallet = get_wallet_for_user(db, user.id)
    spend_ams(db, wallet, amount, reason=reason, metadata={"admin_deduct": True})
    db.refresh(wallet)
    result = {"user_id": user.id, "amount": amount, "new_balance": wallet.balance}
    log_admin_action(
        db,
        admin_user_id=admin_user_id,
        action_type="deduct_ams",
        target_type="user",
        target_id=user.id,
        metadata=result,
    )
    return result


def grant_ams_family(
    db: Session,
    *,
    family_id: int,
    amount: int,
    reason: str = "admin_grant",
    admin_user_id: int | None = None,
) -> dict:
    family = db.get(Family, family_id)
    if family is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    wallet = _get_or_create_family_wallet(db, family_id)
    add_ams(db, wallet, amount, reason=reason, metadata={"admin_grant": True})
    db.refresh(wallet)
    result = {"family_id": family_id, "amount": amount, "new_balance": wallet.balance}
    log_admin_action(
        db,
        admin_user_id=admin_user_id,
        action_type="grant_ams",
        target_type="family",
        target_id=family_id,
        metadata={"amount": amount, "reason": reason},
    )
    return result


def set_user_blocked(
    db: Session, *, user_id: int, blocked: bool, admin_user_id: int | None = None
) -> dict:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    user.is_blocked = blocked
    db.commit()
    action = "block_user" if blocked else "unblock_user"
    log_admin_action(
        db,
        admin_user_id=admin_user_id,
        action_type=action,
        target_type="user",
        target_id=user_id,
    )
    return {"user_id": user_id, "is_blocked": blocked}


def set_family_blocked(
    db: Session, *, family_id: int, blocked: bool, admin_user_id: int | None = None
) -> dict:
    family = db.get(Family, family_id)
    if family is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    family.is_blocked = blocked
    db.commit()
    action = "block_family" if blocked else "unblock_family"
    log_admin_action(
        db,
        admin_user_id=admin_user_id,
        action_type=action,
        target_type="family",
        target_id=family_id,
    )
    return {"family_id": family_id, "is_blocked": blocked}


def delete_family(
    db: Session, *, family_id: int, admin_user_id: int | None = None
) -> dict:
    family = db.get(Family, family_id)
    if family is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    name = family.name
    db.delete(family)
    db.commit()
    log_admin_action(
        db,
        admin_user_id=admin_user_id,
        action_type="delete_family",
        target_type="family",
        target_id=family_id,
        metadata={"name": name},
    )
    return {"family_id": family_id, "deleted": True}


def get_user_detail(db: Session, user_id: int) -> dict:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    sub = subscription_service.get_active_subscription(db, user)
    wallet = get_wallet_for_user(db, user.id)
    ai_stats = (
        db.query(
            func.count(AiUsageLog.id),
            func.coalesce(func.sum(AiUsageLog.ams_spent), 0),
            func.coalesce(func.sum(AiUsageLog.estimated_cost), 0.0),
        )
        .filter(AiUsageLog.user_id == user.id)
        .one()
    )
    menu_count = (
        db.query(func.count(FamilyMenuSelection.id))
        .filter(FamilyMenuSelection.user_id == user.id)
        .scalar()
        or 0
    )
    return {
        "id": user.id,
        "display_name": _display_name(user),
        "telegram_id": user.telegram_id,
        "username": user.username,
        "created_at": user.created_at,
        "last_activity_at": _last_activity(db, user.id, user.updated_at),
        "family_name": _user_family_name(db, user.id),
        "plan_code": sub.plan_code if sub else "free",
        "plan_status": sub.status if sub else "none",
        "ama_balance": wallet.balance,
        "is_blocked": bool(user.is_blocked),
        "ai_requests": int(ai_stats[0] or 0),
        "ams_spent": int(ai_stats[1] or 0),
        "openai_cost_usd": float(ai_stats[2] or 0),
        "menu_count": int(menu_count),
    }


def get_ams_summary(db: Session) -> dict:
    today_start = _start_of_today_utc()
    month_start = _start_of_month_utc()
    credited = (
        db.query(func.coalesce(func.sum(AmaTransaction.amount), 0))
        .filter(AmaTransaction.amount > 0)
        .scalar()
        or 0
    )
    debited = (
        db.query(func.coalesce(func.sum(AmaTransaction.amount), 0))
        .filter(AmaTransaction.amount < 0)
        .scalar()
        or 0
    )
    user_balance = (
        db.query(func.coalesce(func.sum(AmaWallet.balance), 0))
        .filter(AmaWallet.user_id.isnot(None))
        .scalar()
        or 0
    )
    family_balance = (
        db.query(func.coalesce(func.sum(AmaWallet.balance), 0))
        .filter(AmaWallet.family_id.isnot(None))
        .scalar()
        or 0
    )
    spent_today = (
        db.query(func.coalesce(func.sum(AiUsageLog.ams_spent), 0))
        .filter(AiUsageLog.created_at >= today_start)
        .scalar()
        or 0
    )
    spent_month = (
        db.query(func.coalesce(func.sum(AiUsageLog.ams_spent), 0))
        .filter(AiUsageLog.created_at >= month_start)
        .scalar()
        or 0
    )
    return {
        "credited_total": int(credited),
        "debited_total": int(abs(debited)),
        "user_balance_total": int(user_balance),
        "family_balance_total": int(family_balance),
        "spent_today": int(spent_today),
        "spent_month": int(spent_month),
    }


def list_ama_transactions(db: Session, *, limit: int = 100) -> list[dict]:
    rows = (
        db.query(AmaTransaction, AmaWallet)
        .join(AmaWallet, AmaWallet.id == AmaTransaction.wallet_id)
        .order_by(AmaTransaction.id.desc())
        .limit(limit)
        .all()
    )
    result: list[dict] = []
    for tx, wallet in rows:
        user_id = wallet.user_id
        family_id = wallet.family_id
        result.append(
            {
                "id": tx.id,
                "created_at": tx.created_at,
                "user_id": user_id,
                "family_id": family_id,
                "amount": tx.amount,
                "reason": tx.reason,
                "type": tx.type,
            }
        )
    return result


def _period_start(period: str) -> datetime | None:
    now = _now()
    if period == "today":
        return _start_of_today_utc()
    if period == "7d":
        return now - timedelta(days=7)
    if period == "30d":
        return now - timedelta(days=30)
    if period == "month":
        return _start_of_month_utc()
    return None


def get_openai_stats(db: Session, *, period: str = "30d") -> dict:
    since = _period_start(period) or (_now() - timedelta(days=30))
    base = db.query(AiUsageLog).filter(AiUsageLog.created_at >= since)
    totals = base.with_entities(
        func.count(AiUsageLog.id),
        func.coalesce(func.sum(AiUsageLog.estimated_cost), 0.0),
        func.coalesce(func.sum(AiUsageLog.input_tokens), 0),
        func.coalesce(func.sum(AiUsageLog.output_tokens), 0),
        func.coalesce(func.sum(AiUsageLog.ams_spent), 0),
    ).one()
    requests = int(totals[0] or 0)
    cost = float(totals[1] or 0)
    input_tokens = int(totals[2] or 0)
    output_tokens = int(totals[3] or 0)
    ams = int(totals[4] or 0)
    menu_gens = (
        base.filter(AiUsageLog.action_type.ilike("%menu%"))
        .with_entities(func.count(AiUsageLog.id))
        .scalar()
        or 0
    )
    distinct_users = (
        base.with_entities(func.count(func.distinct(AiUsageLog.user_id))).scalar() or 0
    )
    distinct_families = (
        base.with_entities(func.count(func.distinct(AiUsageLog.family_id)))
        .filter(AiUsageLog.family_id.isnot(None))
        .scalar()
        or 0
    )
    categories_raw = (
        base.with_entities(
            AiUsageLog.action_type,
            func.count(AiUsageLog.id),
            func.coalesce(func.sum(AiUsageLog.input_tokens), 0),
            func.coalesce(func.sum(AiUsageLog.output_tokens), 0),
            func.coalesce(func.sum(AiUsageLog.estimated_cost), 0.0),
            func.coalesce(func.sum(AiUsageLog.ams_spent), 0),
        )
        .group_by(AiUsageLog.action_type)
        .all()
    )
    categories = [
        {
            "category": row[0] or "other",
            "requests": int(row[1]),
            "input_tokens": int(row[2]),
            "output_tokens": int(row[3]),
            "total_tokens": int(row[2]) + int(row[3]),
            "openai_cost_usd": float(row[4]),
            "ams_spent": int(row[5]),
            "avg_cost_usd": float(row[4]) / int(row[1]) if row[1] else 0.0,
        }
        for row in categories_raw
    ]
    return {
        "period": period,
        "requests": requests,
        "openai_cost_usd": cost,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
        "ams_spent": ams,
        "menu_generations": int(menu_gens),
        "avg_request_cost_usd": cost / requests if requests else 0.0,
        "avg_menu_cost_usd": cost / menu_gens if menu_gens else 0.0,
        "avg_user_cost_usd": cost / distinct_users if distinct_users else 0.0,
        "avg_family_cost_usd": cost / distinct_families if distinct_families else 0.0,
        "categories": categories,
    }


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
