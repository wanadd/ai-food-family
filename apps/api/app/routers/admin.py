import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_admin_user
from app.models.user import User
from app.schemas.admin import (
    AdminAiUsageRow,
    AdminBackupCreateResponse,
    AdminBackupRow,
    AdminFamilyRow,
    AdminGrantAmsRequest,
    AdminGrantResponse,
    AdminGrantSubscriptionRequest,
    AdminPlanOption,
    AdminSubscriptionRow,
    AdminSummaryResponse,
    AdminUserRow,
)
from app.services import admin as admin_service
from app.services import backup as backup_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/summary", response_model=AdminSummaryResponse)
def admin_summary(
    _: User = Depends(require_admin_user),
    db: Session = Depends(get_db),
) -> AdminSummaryResponse:
    return AdminSummaryResponse(**admin_service.get_summary(db))


@router.get("/users", response_model=list[AdminUserRow])
def admin_users(
    _: User = Depends(require_admin_user),
    db: Session = Depends(get_db),
    limit: int = 200,
    offset: int = 0,
) -> list[AdminUserRow]:
    return [AdminUserRow(**row) for row in admin_service.list_users(db, limit=limit, offset=offset)]


@router.get("/families", response_model=list[AdminFamilyRow])
def admin_families(
    _: User = Depends(require_admin_user),
    db: Session = Depends(get_db),
    limit: int = 200,
    offset: int = 0,
) -> list[AdminFamilyRow]:
    return [
        AdminFamilyRow(**row) for row in admin_service.list_families(db, limit=limit, offset=offset)
    ]


@router.get("/subscriptions", response_model=list[AdminSubscriptionRow])
def admin_subscriptions(
    _: User = Depends(require_admin_user),
    db: Session = Depends(get_db),
    limit: int = 200,
) -> list[AdminSubscriptionRow]:
    return [
        AdminSubscriptionRow(**row)
        for row in admin_service.list_subscriptions(db, limit=limit)
    ]


@router.get("/plans", response_model=list[AdminPlanOption])
def admin_plans(
    _: User = Depends(require_admin_user),
    db: Session = Depends(get_db),
) -> list[AdminPlanOption]:
    return [AdminPlanOption(**row) for row in admin_service.list_plans(db)]


@router.post("/subscriptions/grant", response_model=AdminGrantResponse)
def admin_grant_subscription(
    payload: AdminGrantSubscriptionRequest,
    _: User = Depends(require_admin_user),
    db: Session = Depends(get_db),
) -> AdminGrantResponse:
    result = admin_service.grant_subscription(
        db,
        user_id=payload.user_id,
        plan_code=payload.plan_code,
        extend_days=payload.extend_days,
        promo_note=payload.promo_note,
    )
    return AdminGrantResponse(
        user_id=result["user_id"],
        message=f"Тариф «{result['plan_code']}» выдан до {result['current_period_ends_at']}",
    )


@router.post("/ams/grant", response_model=AdminGrantResponse)
def admin_grant_ams(
    payload: AdminGrantAmsRequest,
    _: User = Depends(require_admin_user),
    db: Session = Depends(get_db),
) -> AdminGrantResponse:
    result = admin_service.grant_ams(
        db,
        user_id=payload.user_id,
        amount=payload.amount,
        reason=payload.reason,
    )
    return AdminGrantResponse(
        user_id=result["user_id"],
        message=f"Начислено {result['amount']} Амов. Баланс: {result['new_balance']}",
    )


@router.get("/ai-usage", response_model=list[AdminAiUsageRow])
def admin_ai_usage(
    _: User = Depends(require_admin_user),
    db: Session = Depends(get_db),
    limit: int = 100,
) -> list[AdminAiUsageRow]:
    return [AdminAiUsageRow(**row) for row in admin_service.list_ai_usage(db, limit=limit)]


@router.get("/backups", response_model=list[AdminBackupRow])
def admin_list_backups(
    _: User = Depends(require_admin_user),
) -> list[AdminBackupRow]:
    return [AdminBackupRow(**row) for row in backup_service.list_backups()]


@router.post("/backups/create", response_model=AdminBackupCreateResponse)
def admin_create_backup(
    _: User = Depends(require_admin_user),
) -> AdminBackupCreateResponse:
    try:
        result = backup_service.create_backup()
    except RuntimeError as exc:
        logger.exception("Backup creation failed")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    return AdminBackupCreateResponse(
        **result,
        message=f"Резервная копия создана: {result['id']}",
    )
