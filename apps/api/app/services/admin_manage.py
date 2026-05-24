"""Admin mutations: users, subscriptions, ams, families."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.config import settings
from app.models.admin import AdminSession
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
from app.models.user_profile import UserProfile
from app.services import subscription as subscription_service
from app.services.admin import _display_name, _last_activity, _user_family_name
from app.services.admin_audit import log_admin_action
from app.services.subscription import (
    _get_or_create_family_wallet,
    add_ams,
    get_wallet_for_user,
    spend_ams,
)

ADMIN_ADJUSTMENT_REASON = "admin_adjustment"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _admin_telegram_ids() -> set[int]:
    return settings.admin_telegram_id_set()


def _is_project_admin(user: User) -> bool:
    return user.telegram_id in _admin_telegram_ids()


def _count_active_project_admins(db: Session) -> int:
    ids = _admin_telegram_ids()
    if not ids:
        return 0
    return (
        db.query(func.count(User.id))
        .filter(
            User.telegram_id.in_(ids),
            User.is_deleted.is_(False),
        )
        .scalar()
        or 0
    )


def _get_user_or_404(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if user is None or user.is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return user


def _guard_target_user(db: Session, target: User, admin: User, *, allow_self: bool = False) -> None:
    if not allow_self and target.id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя выполнить действие над собой",
        )


def _guard_delete_user(db: Session, target: User, admin: User) -> None:
    _guard_target_user(db, target, admin)
    if _is_project_admin(target):
        if _count_active_project_admins(db) <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Нельзя удалить последнего администратора",
            )


def get_active_family_subscription(
    db: Session, family_id: int
) -> UserSubscription | None:
    return (
        db.query(UserSubscription)
        .filter(
            UserSubscription.family_id == family_id,
            UserSubscription.status.in_(
                ("active", "trial", "manually_granted")
            ),
        )
        .order_by(UserSubscription.id.desc())
        .first()
    )


def _subscription_payload(sub: UserSubscription | None) -> dict[str, Any] | None:
    if sub is None:
        return None
    raw_meta = getattr(sub, "metadata_json", None)
    meta = raw_meta if isinstance(raw_meta, dict) else {}
    return {
        "id": sub.id,
        "plan_code": sub.plan_code,
        "status": sub.status,
        "started_at": sub.started_at,
        "trial_ends_at": sub.trial_ends_at,
        "current_period_ends_at": sub.current_period_ends_at,
        "family_id": sub.family_id,
        "grant_source": meta.get("grant_source", "system"),
        "grant_reason": meta.get("grant_reason"),
        "kind": meta.get("kind", "paid" if sub.plan_code not in ("trial", "free") else sub.plan_code),
    }


def _wallet_ams_stats(db: Session, wallet: AmaWallet) -> dict[str, int]:
    credited = (
        db.query(func.coalesce(func.sum(AmaTransaction.amount), 0))
        .filter(
            AmaTransaction.wallet_id == wallet.id,
            AmaTransaction.amount > 0,
        )
        .scalar()
        or 0
    )
    debited = (
        db.query(func.coalesce(func.sum(AmaTransaction.amount), 0))
        .filter(
            AmaTransaction.wallet_id == wallet.id,
            AmaTransaction.amount < 0,
        )
        .scalar()
        or 0
    )
    return {
        "balance": wallet.balance,
        "credited_total": int(credited),
        "spent_total": int(abs(debited)),
    }


def list_user_transactions(db: Session, user_id: int, *, limit: int = 20) -> list[dict]:
    wallet = get_wallet_for_user(db, user_id)
    rows = (
        db.query(AmaTransaction)
        .filter(AmaTransaction.wallet_id == wallet.id)
        .order_by(AmaTransaction.id.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": tx.id,
            "amount": tx.amount,
            "type": tx.type,
            "reason": tx.reason,
            "created_at": tx.created_at,
            "comment": (tx.metadata_json or {}).get("comment"),
        }
        for tx in rows
    ]


def get_user_card(db: Session, user_id: int) -> dict:
    user = (
        db.query(User)
        .options(joinedload(User.profile))
        .filter(User.id == user_id, User.is_deleted.is_(False))
        .one_or_none()
    )
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    sub = subscription_service.get_active_subscription(db, user)
    wallet = get_wallet_for_user(db, user.id)
    ams = _wallet_ams_stats(db, wallet)
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
    member = (
        db.query(FamilyMember)
        .filter(FamilyMember.user_id == user.id)
        .one_or_none()
    )
    return {
        "id": user.id,
        "display_name": _display_name(user),
        "telegram_id": user.telegram_id,
        "username": user.username,
        "created_at": user.created_at,
        "last_activity_at": _last_activity(db, user.id, user.updated_at),
        "family_id": member.family_id if member else None,
        "family_name": _user_family_name(db, user.id),
        "is_blocked": user.is_blocked,
        "blocked_at": user.blocked_at,
        "blocked_reason": user.blocked_reason,
        "is_deleted": user.is_deleted,
        "phone_number": user.phone_number,
        "legal_accepted": bool(
            user.accepted_terms and user.accepted_privacy and user.accepted_personal_data
        ),
        "profile_completed": bool(user.profile and user.profile.completed),
        "subscription": _subscription_payload(sub),
        "ams": {**ams, "transactions": list_user_transactions(db, user.id)},
        "ai_requests": int(ai_stats[0] or 0),
        "ams_spent": int(ai_stats[1] or 0),
        "openai_cost_usd": float(ai_stats[2] or 0),
        "menu_count": int(menu_count),
    }


def get_family_card(db: Session, family_id: int) -> dict:
    family = (
        db.query(Family)
        .options(joinedload(Family.members).joinedload(FamilyMember.user))
        .filter(Family.id == family_id)
        .one_or_none()
    )
    if family is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    admin_member = next(
        (m for m in family.members if m.role == FamilyRole.ADMIN.value),
        family.members[0] if family.members else None,
    )
    wallet = _get_or_create_family_wallet(db, family_id)
    ams = _wallet_ams_stats(db, wallet)
    sub = get_active_family_subscription(db, family_id)
    if sub is None and admin_member and admin_member.user_id:
        admin_user = db.get(User, admin_member.user_id)
        if admin_user:
            personal = subscription_service.get_active_subscription(db, admin_user)
            if personal and personal.family_id == family_id:
                sub = personal

    members = []
    for m in family.members:
        members.append(
            {
                "id": m.id,
                "user_id": m.user_id,
                "display_name": m.display_name,
                "role": m.role,
                "is_virtual": m.is_virtual,
            }
        )

    return {
        "id": family.id,
        "name": family.name,
        "is_blocked": family.is_blocked,
        "blocked_at": family.blocked_at,
        "blocked_reason": family.blocked_reason,
        "created_at": family.created_at,
        "member_count": len(family.members),
        "admin_user_id": admin_member.user_id if admin_member else None,
        "admin_name": admin_member.display_name if admin_member else "—",
        "members": members,
        "subscription": _subscription_payload(sub),
        "ams": {**ams, "transactions": _list_family_transactions(db, wallet.id)},
    }


def _list_family_transactions(db: Session, wallet_id: int, *, limit: int = 20) -> list[dict]:
    rows = (
        db.query(AmaTransaction)
        .filter(AmaTransaction.wallet_id == wallet_id)
        .order_by(AmaTransaction.id.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": tx.id,
            "amount": tx.amount,
            "type": tx.type,
            "reason": tx.reason,
            "created_at": tx.created_at,
            "comment": (tx.metadata_json or {}).get("comment"),
        }
        for tx in rows
    ]


def block_user(
    db: Session,
    *,
    user_id: int,
    admin: User,
    reason: str | None = None,
) -> dict:
    target = _get_user_or_404(db, user_id)
    _guard_target_user(db, target, admin)
    target.is_blocked = True
    target.blocked_at = _now()
    target.blocked_reason = (reason or "")[:500] or None
    db.commit()
    log_admin_action(
        db,
        admin_user_id=admin.id,
        action_type="user_block",
        target_type="user",
        target_id=user_id,
        metadata={"reason": reason},
    )
    return {"user_id": user_id, "is_blocked": True}


def unblock_user(db: Session, *, user_id: int, admin: User) -> dict:
    target = _get_user_or_404(db, user_id)
    target.is_blocked = False
    target.blocked_at = None
    target.blocked_reason = None
    db.commit()
    log_admin_action(
        db,
        admin_user_id=admin.id,
        action_type="user_unblock",
        target_type="user",
        target_id=user_id,
    )
    return {"user_id": user_id, "is_blocked": False}


def delete_user(db: Session, *, user_id: int, admin: User) -> dict:
    target = _get_user_or_404(db, user_id)
    _guard_delete_user(db, target, admin)

    member = (
        db.query(FamilyMember)
        .filter(FamilyMember.user_id == target.id)
        .one_or_none()
    )
    if member:
        db.delete(member)

    db.query(AdminSession).filter(AdminSession.user_id == target.id).update(
        {"is_active": False}
    )

    target.is_deleted = True
    target.deleted_at = _now()
    target.deleted_by_admin_id = admin.id
    target.is_blocked = True
    db.commit()

    log_admin_action(
        db,
        admin_user_id=admin.id,
        action_type="user_delete",
        target_type="user",
        target_id=user_id,
        metadata={"telegram_id": target.telegram_id},
    )
    return {"user_id": user_id, "deleted": True}


def reset_user_onboarding(db: Session, *, user_id: int, admin: User) -> dict:
    user = _get_user_or_404(db, user_id)
    profile = user.profile
    if profile is None:
        profile = UserProfile(user_id=user.id)
        db.add(profile)
    profile.current_step = 0
    profile.completed = False
    db.commit()
    log_admin_action(
        db,
        admin_user_id=admin.id,
        action_type="user_reset_onboarding",
        target_type="user",
        target_id=user_id,
    )
    return {"user_id": user_id}


def reset_user_phone(db: Session, *, user_id: int, admin: User) -> dict:
    user = _get_user_or_404(db, user_id)
    user.phone_number = None
    user.phone_skipped = False
    db.commit()
    log_admin_action(
        db,
        admin_user_id=admin.id,
        action_type="user_reset_phone",
        target_type="user",
        target_id=user_id,
    )
    return {"user_id": user_id}


def reset_user_legal(db: Session, *, user_id: int, admin: User) -> dict:
    user = _get_user_or_404(db, user_id)
    user.accepted_terms = False
    user.accepted_privacy = False
    user.accepted_personal_data = False
    user.legal_accepted_at = None
    user.legal_documents_version = None
    db.commit()
    log_admin_action(
        db,
        admin_user_id=admin.id,
        action_type="user_reset_legal",
        target_type="user",
        target_id=user_id,
    )
    return {"user_id": user_id}


def reset_user_nutrition(db: Session, *, user_id: int, admin: User) -> dict:
    user = _get_user_or_404(db, user_id)
    if user.profile:
        db.delete(user.profile)
    profile = UserProfile(user_id=user.id, current_step=0, completed=False)
    db.add(profile)
    db.commit()
    log_admin_action(
        db,
        admin_user_id=admin.id,
        action_type="user_reset_nutrition",
        target_type="user",
        target_id=user_id,
    )
    return {"user_id": user_id}


def _cancel_active_subs(
    db: Session, *, user_id: int | None = None, family_id: int | None = None
) -> None:
    q = db.query(UserSubscription).filter(
        UserSubscription.status.in_(("active", "trial", "manually_granted"))
    )
    if user_id is not None:
        q = q.filter(UserSubscription.user_id == user_id, UserSubscription.family_id.is_(None))
    if family_id is not None:
        q = q.filter(UserSubscription.family_id == family_id)
    for sub in q.all():
        sub.status = "cancelled"
    db.commit()


def _create_subscription(
    db: Session,
    *,
    user: User,
    plan_code: str,
    days: int,
    family_id: int | None,
    status: str,
    admin: User,
    reason: str | None,
    expires_at: datetime | None,
) -> UserSubscription:
    subscription_service.seed_subscription_plans(db)
    plan = subscription_service.get_plan(db, plan_code)
    if plan is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Неизвестный тариф")

    if family_id:
        _cancel_active_subs(db, family_id=family_id)
    else:
        _cancel_active_subs(db, user_id=user.id)

    now = _now()
    end = expires_at or (now + timedelta(days=days))
    sub = UserSubscription(
        user_id=user.id,
        family_id=family_id,
        plan_code=plan_code,
        status=status,
        started_at=now,
        current_period_ends_at=end,
        trial_ends_at=end if status == "trial" else None,
        menu_generations_used=0,
        metadata_json={
            "grant_source": "admin",
            "grant_reason": reason,
            "admin_user_id": admin.id,
            "kind": "trial" if status == "trial" else "manual",
        },
    )
    db.add(sub)
    db.commit()
    db.refresh(sub)

    wallet = (
        _get_or_create_family_wallet(db, family_id)
        if family_id
        else get_wallet_for_user(db, user.id)
    )
    if plan.monthly_ams > wallet.balance:
        add_ams(
            db,
            wallet,
            plan.monthly_ams - wallet.balance,
            reason=ADMIN_ADJUSTMENT_REASON,
            metadata={"plan_code": plan_code, "admin_grant": True},
        )
    return sub


def grant_user_subscription(
    db: Session,
    *,
    user_id: int,
    admin: User,
    plan_code: str,
    days: int = 30,
    reason: str | None = None,
    expires_at: datetime | None = None,
    as_trial: bool = False,
) -> dict:
    user = _get_user_or_404(db, user_id)
    status = "trial" if as_trial else "manually_granted"
    sub = _create_subscription(
        db,
        user=user,
        plan_code=plan_code,
        days=days,
        family_id=None,
        status=status,
        admin=admin,
        reason=reason,
        expires_at=expires_at,
    )
    log_admin_action(
        db,
        admin_user_id=admin.id,
        action_type="subscription_grant",
        target_type="user",
        target_id=user_id,
        metadata={"plan_code": plan_code, "days": days},
    )
    return _subscription_payload(sub) or {}


def extend_user_subscription(
    db: Session, *, user_id: int, admin: User, days: int, reason: str | None = None
) -> dict:
    user = _get_user_or_404(db, user_id)
    sub = subscription_service.get_active_subscription(db, user)
    if sub is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Нет подписки")
    base = sub.current_period_ends_at or _now()
    sub.current_period_ends_at = base + timedelta(days=days)
    meta = dict(sub.metadata_json or {})
    meta["grant_reason"] = reason
    sub.metadata_json = meta
    db.commit()
    log_admin_action(
        db,
        admin_user_id=admin.id,
        action_type="subscription_extend",
        target_type="user",
        target_id=user_id,
        metadata={"days": days},
    )
    return _subscription_payload(sub) or {}


def disable_user_subscription(db: Session, *, user_id: int, admin: User) -> dict:
    user = _get_user_or_404(db, user_id)
    sub = subscription_service.get_active_subscription(db, user)
    if sub:
        sub.status = "disabled"
        db.commit()
    log_admin_action(
        db,
        admin_user_id=admin.id,
        action_type="subscription_disable",
        target_type="user",
        target_id=user_id,
    )
    return {"user_id": user_id, "disabled": True}


def change_user_plan(
    db: Session,
    *,
    user_id: int,
    admin: User,
    plan_code: str,
    days: int = 30,
    reason: str | None = None,
) -> dict:
    user = _get_user_or_404(db, user_id)
    sub = _create_subscription(
        db,
        user=user,
        plan_code=plan_code,
        days=days,
        family_id=None,
        status="manually_granted",
        admin=admin,
        reason=reason,
        expires_at=None,
    )
    log_admin_action(
        db,
        admin_user_id=admin.id,
        action_type="subscription_change_plan",
        target_type="user",
        target_id=user_id,
        metadata={"plan_code": plan_code},
    )
    return _subscription_payload(sub) or {}


def grant_family_subscription(
    db: Session,
    *,
    family_id: int,
    admin: User,
    plan_code: str,
    days: int = 30,
    reason: str | None = None,
    as_trial: bool = False,
) -> dict:
    family = db.get(Family, family_id)
    if family is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    billing_user = subscription_service.get_family_admin_user(db, family_id)
    if billing_user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="У семьи нет администратора",
        )
    status = "trial" if as_trial else "manually_granted"
    sub = _create_subscription(
        db,
        user=billing_user,
        plan_code=plan_code,
        days=days,
        family_id=family_id,
        status=status,
        admin=admin,
        reason=reason,
        expires_at=None,
    )
    log_admin_action(
        db,
        admin_user_id=admin.id,
        action_type="subscription_grant",
        target_type="family",
        target_id=family_id,
        metadata={"plan_code": plan_code},
    )
    return _subscription_payload(sub) or {}


def extend_family_subscription(
    db: Session, *, family_id: int, admin: User, days: int, reason: str | None = None
) -> dict:
    sub = get_active_family_subscription(db, family_id)
    if sub is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Нет подписки")
    base = sub.current_period_ends_at or _now()
    sub.current_period_ends_at = base + timedelta(days=days)
    db.commit()
    log_admin_action(
        db,
        admin_user_id=admin.id,
        action_type="subscription_extend",
        target_type="family",
        target_id=family_id,
        metadata={"days": days},
    )
    return _subscription_payload(sub) or {}


def disable_family_subscription(db: Session, *, family_id: int, admin: User) -> dict:
    sub = get_active_family_subscription(db, family_id)
    if sub:
        sub.status = "disabled"
        db.commit()
    log_admin_action(
        db,
        admin_user_id=admin.id,
        action_type="subscription_disable",
        target_type="family",
        target_id=family_id,
    )
    return {"family_id": family_id, "disabled": True}


def change_family_plan(
    db: Session,
    *,
    family_id: int,
    admin: User,
    plan_code: str,
    days: int = 30,
    reason: str | None = None,
) -> dict:
    billing_user = subscription_service.get_family_admin_user(db, family_id)
    if billing_user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Нет админа семьи")
    sub = _create_subscription(
        db,
        user=billing_user,
        plan_code=plan_code,
        days=days,
        family_id=family_id,
        status="manually_granted",
        admin=admin,
        reason=reason,
        expires_at=None,
    )
    log_admin_action(
        db,
        admin_user_id=admin.id,
        action_type="subscription_change_plan",
        target_type="family",
        target_id=family_id,
        metadata={"plan_code": plan_code},
    )
    return _subscription_payload(sub) or {}


def _ams_meta(comment: str | None, admin_id: int) -> dict:
    return {"comment": comment, "admin_user_id": admin_id}


def add_user_ams(
    db: Session,
    *,
    user_id: int,
    admin: User,
    amount: int,
    reason: str | None = None,
    comment: str | None = None,
) -> dict:
    if amount <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid amount")
    user = _get_user_or_404(db, user_id)
    wallet = get_wallet_for_user(db, user.id)
    add_ams(
        db,
        wallet,
        amount,
        reason=ADMIN_ADJUSTMENT_REASON,
        metadata=_ams_meta(comment or reason, admin.id),
    )
    db.refresh(wallet)
    log_admin_action(
        db,
        admin_user_id=admin.id,
        action_type="ams_add",
        target_type="user",
        target_id=user_id,
        metadata={"amount": amount},
    )
    return {"balance": wallet.balance}


def remove_user_ams(
    db: Session,
    *,
    user_id: int,
    admin: User,
    amount: int,
    comment: str | None = None,
) -> dict:
    if amount <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid amount")
    user = _get_user_or_404(db, user_id)
    wallet = get_wallet_for_user(db, user.id)
    spend_ams(
        db,
        wallet,
        amount,
        reason=ADMIN_ADJUSTMENT_REASON,
        metadata=_ams_meta(comment, admin.id),
    )
    db.refresh(wallet)
    log_admin_action(
        db,
        admin_user_id=admin.id,
        action_type="ams_remove",
        target_type="user",
        target_id=user_id,
        metadata={"amount": amount},
    )
    return {"balance": wallet.balance}


def reset_user_ams(db: Session, *, user_id: int, admin: User) -> dict:
    user = _get_user_or_404(db, user_id)
    wallet = get_wallet_for_user(db, user.id)
    if wallet.balance > 0:
        spend_ams(
            db,
            wallet,
            wallet.balance,
            reason=ADMIN_ADJUSTMENT_REASON,
            metadata=_ams_meta("admin reset", admin.id),
        )
    db.refresh(wallet)
    log_admin_action(
        db,
        admin_user_id=admin.id,
        action_type="ams_reset",
        target_type="user",
        target_id=user_id,
    )
    return {"balance": wallet.balance}


def add_family_ams(
    db: Session,
    *,
    family_id: int,
    admin: User,
    amount: int,
    comment: str | None = None,
) -> dict:
    if amount <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid amount")
    wallet = _get_or_create_family_wallet(db, family_id)
    add_ams(
        db,
        wallet,
        amount,
        reason=ADMIN_ADJUSTMENT_REASON,
        metadata=_ams_meta(comment, admin.id),
    )
    db.refresh(wallet)
    log_admin_action(
        db,
        admin_user_id=admin.id,
        action_type="ams_add",
        target_type="family",
        target_id=family_id,
        metadata={"amount": amount},
    )
    return {"balance": wallet.balance}


def remove_family_ams(
    db: Session,
    *,
    family_id: int,
    admin: User,
    amount: int,
    comment: str | None = None,
) -> dict:
    wallet = _get_or_create_family_wallet(db, family_id)
    spend_ams(
        db,
        wallet,
        amount,
        reason=ADMIN_ADJUSTMENT_REASON,
        metadata=_ams_meta(comment, admin.id),
    )
    db.refresh(wallet)
    log_admin_action(
        db,
        admin_user_id=admin.id,
        action_type="ams_remove",
        target_type="family",
        target_id=family_id,
        metadata={"amount": amount},
    )
    return {"balance": wallet.balance}


def reset_family_ams(db: Session, *, family_id: int, admin: User) -> dict:
    wallet = _get_or_create_family_wallet(db, family_id)
    if wallet.balance > 0:
        spend_ams(
            db,
            wallet,
            wallet.balance,
            reason=ADMIN_ADJUSTMENT_REASON,
            metadata=_ams_meta("admin reset", admin.id),
        )
    db.refresh(wallet)
    log_admin_action(
        db,
        admin_user_id=admin.id,
        action_type="ams_reset",
        target_type="family",
        target_id=family_id,
    )
    return {"balance": wallet.balance}


def rename_family(db: Session, *, family_id: int, name: str, admin: User) -> dict:
    family = db.get(Family, family_id)
    if family is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    family.name = name.strip()[:120]
    db.commit()
    log_admin_action(
        db,
        admin_user_id=admin.id,
        action_type="family_rename",
        target_type="family",
        target_id=family_id,
        metadata={"name": family.name},
    )
    return {"family_id": family_id, "name": family.name}


def block_family(
    db: Session, *, family_id: int, admin: User, reason: str | None = None
) -> dict:
    family = db.get(Family, family_id)
    if family is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    family.is_blocked = True
    family.blocked_at = _now()
    family.blocked_reason = (reason or "")[:500] or None
    db.commit()
    log_admin_action(
        db,
        admin_user_id=admin.id,
        action_type="family_block",
        target_type="family",
        target_id=family_id,
    )
    return {"family_id": family_id, "is_blocked": True}


def unblock_family(db: Session, *, family_id: int, admin: User) -> dict:
    family = db.get(Family, family_id)
    if family is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    family.is_blocked = False
    family.blocked_at = None
    family.blocked_reason = None
    db.commit()
    log_admin_action(
        db,
        admin_user_id=admin.id,
        action_type="family_unblock",
        target_type="family",
        target_id=family_id,
    )
    return {"family_id": family_id, "is_blocked": False}


def delete_family_record(db: Session, *, family_id: int, admin: User) -> dict:
    family = db.get(Family, family_id)
    if family is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    name = family.name
    db.delete(family)
    db.commit()
    log_admin_action(
        db,
        admin_user_id=admin.id,
        action_type="family_delete",
        target_type="family",
        target_id=family_id,
        metadata={"name": name},
    )
    return {"family_id": family_id, "deleted": True}


def transfer_family_owner(
    db: Session, *, family_id: int, new_admin_user_id: int, admin: User
) -> dict:
    family = db.get(Family, family_id)
    if family is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    target_member = (
        db.query(FamilyMember)
        .filter(
            FamilyMember.family_id == family_id,
            FamilyMember.user_id == new_admin_user_id,
        )
        .one_or_none()
    )
    if target_member is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь не в этой семье",
        )
    for m in family.members:
        if m.role == FamilyRole.ADMIN.value:
            m.role = FamilyRole.ADULT.value
    target_member.role = FamilyRole.ADMIN.value
    db.commit()
    log_admin_action(
        db,
        admin_user_id=admin.id,
        action_type="family_transfer_owner",
        target_type="family",
        target_id=family_id,
        metadata={"new_admin_user_id": new_admin_user_id},
    )
    return {"family_id": family_id, "admin_user_id": new_admin_user_id}


def remove_family_member(
    db: Session, *, family_id: int, member_id: int, admin: User
) -> dict:
    member = (
        db.query(FamilyMember)
        .filter(FamilyMember.id == member_id, FamilyMember.family_id == family_id)
        .one_or_none()
    )
    if member is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    if member.role == FamilyRole.ADMIN.value and not member.is_virtual:
        others = (
            db.query(FamilyMember)
            .filter(
                FamilyMember.family_id == family_id,
                FamilyMember.id != member_id,
                FamilyMember.user_id.isnot(None),
            )
            .count()
        )
        if others == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Нельзя удалить единственного администратора",
            )
    db.delete(member)
    db.commit()
    log_admin_action(
        db,
        admin_user_id=admin.id,
        action_type="family_remove_member",
        target_type="family",
        target_id=family_id,
        metadata={"member_id": member_id},
    )
    return {"member_id": member_id, "removed": True}
