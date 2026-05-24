import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_admin_user
from app.models.user import User
from app.schemas.admin import (
    AdminAiUsageRow,
    AdminAmaTransactionRow,
    AdminAmsSummary,
    AdminBackupCreateResponse,
    AdminBackupRow,
    AdminBlockRequest,
    AdminDeductAmsRequest,
    AdminErrorRow,
    AdminFamilyRow,
    AdminGrantAmsRequest,
    AdminGrantFamilyAmsRequest,
    AdminGrantResponse,
    AdminGrantSubscriptionRequest,
    AdminOpenAiStats,
    AdminPingResponse,
    AdminPlanOption,
    AdminSubscriptionRow,
    AdminSummaryResponse,
    AdminUserDetail,
    AdminUserRow,
)
from app.services import admin as admin_service
from app.services import backup as backup_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/ping", response_model=AdminPingResponse)
def admin_ping(_: User = Depends(require_admin_user)) -> AdminPingResponse:
    return AdminPingResponse(ok=True)


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
    q: str | None = None,
    filter: str = Query(default="all", alias="filter"),
) -> list[AdminUserRow]:
    rows = admin_service.list_users(
        db, limit=limit, offset=offset, q=q, status_filter=filter
    )
    return [AdminUserRow(**row) for row in rows]


@router.get("/users/{user_id}", response_model=AdminUserDetail)
def admin_user_detail(
    user_id: int,
    _: User = Depends(require_admin_user),
    db: Session = Depends(get_db),
) -> AdminUserDetail:
    return AdminUserDetail(**admin_service.get_user_detail(db, user_id))


@router.post("/users/{user_id}/block", response_model=AdminGrantResponse)
def admin_block_user(
    user_id: int,
    payload: AdminBlockRequest,
    admin: User = Depends(require_admin_user),
    db: Session = Depends(get_db),
) -> AdminGrantResponse:
    result = admin_service.set_user_blocked(
        db, user_id=user_id, blocked=payload.blocked, admin_user_id=admin.id
    )
    verb = "заблокирован" if payload.blocked else "разблокирован"
    return AdminGrantResponse(user_id=user_id, message=f"Пользователь {verb}")


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


@router.post("/families/{family_id}/block", response_model=AdminGrantResponse)
def admin_block_family(
    family_id: int,
    payload: AdminBlockRequest,
    admin: User = Depends(require_admin_user),
    db: Session = Depends(get_db),
) -> AdminGrantResponse:
    admin_service.set_family_blocked(
        db, family_id=family_id, blocked=payload.blocked, admin_user_id=admin.id
    )
    verb = "заблокирована" if payload.blocked else "разблокирована"
    return AdminGrantResponse(family_id=family_id, message=f"Семья {verb}")


@router.delete("/families/{family_id}", response_model=AdminGrantResponse)
def admin_delete_family(
    family_id: int,
    admin: User = Depends(require_admin_user),
    db: Session = Depends(get_db),
) -> AdminGrantResponse:
    admin_service.delete_family(db, family_id=family_id, admin_user_id=admin.id)
    return AdminGrantResponse(family_id=family_id, message="Семья удалена")


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
    admin: User = Depends(require_admin_user),
    db: Session = Depends(get_db),
) -> AdminGrantResponse:
    result = admin_service.grant_subscription(
        db,
        user_id=payload.user_id,
        plan_code=payload.plan_code,
        extend_days=payload.extend_days,
        promo_note=payload.promo_note,
        admin_user_id=admin.id,
    )
    return AdminGrantResponse(
        user_id=result["user_id"],
        message=f"Тариф «{result['plan_code']}» выдан до {result['current_period_ends_at']}",
    )


@router.post("/ams/grant", response_model=AdminGrantResponse)
def admin_grant_ams(
    payload: AdminGrantAmsRequest,
    admin: User = Depends(require_admin_user),
    db: Session = Depends(get_db),
) -> AdminGrantResponse:
    result = admin_service.grant_ams(
        db,
        user_id=payload.user_id,
        amount=payload.amount,
        reason=payload.reason,
        admin_user_id=admin.id,
    )
    return AdminGrantResponse(
        user_id=result["user_id"],
        message=f"Начислено {result['amount']} Амов. Баланс: {result['new_balance']}",
    )


@router.post("/ams/deduct", response_model=AdminGrantResponse)
def admin_deduct_ams(
    payload: AdminDeductAmsRequest,
    admin: User = Depends(require_admin_user),
    db: Session = Depends(get_db),
) -> AdminGrantResponse:
    result = admin_service.deduct_ams(
        db,
        user_id=payload.user_id,
        amount=payload.amount,
        reason=payload.reason,
        admin_user_id=admin.id,
    )
    return AdminGrantResponse(
        user_id=result["user_id"],
        message=f"Списано {result['amount']} Амов. Баланс: {result['new_balance']}",
    )


@router.post("/ams/grant-family", response_model=AdminGrantResponse)
def admin_grant_family_ams(
    payload: AdminGrantFamilyAmsRequest,
    admin: User = Depends(require_admin_user),
    db: Session = Depends(get_db),
) -> AdminGrantResponse:
    result = admin_service.grant_ams_family(
        db,
        family_id=payload.family_id,
        amount=payload.amount,
        reason=payload.reason,
        admin_user_id=admin.id,
    )
    return AdminGrantResponse(
        family_id=result["family_id"],
        message=f"Начислено {result['amount']} Амов семье. Баланс: {result['new_balance']}",
    )


@router.get("/ams/summary", response_model=AdminAmsSummary)
def admin_ams_summary(
    _: User = Depends(require_admin_user),
    db: Session = Depends(get_db),
) -> AdminAmsSummary:
    return AdminAmsSummary(**admin_service.get_ams_summary(db))


@router.get("/ams/transactions", response_model=list[AdminAmaTransactionRow])
def admin_ama_transactions(
    _: User = Depends(require_admin_user),
    db: Session = Depends(get_db),
    limit: int = 100,
) -> list[AdminAmaTransactionRow]:
    return [
        AdminAmaTransactionRow(**row)
        for row in admin_service.list_ama_transactions(db, limit=limit)
    ]


@router.get("/openai", response_model=AdminOpenAiStats)
def admin_openai_stats(
    _: User = Depends(require_admin_user),
    db: Session = Depends(get_db),
    period: str = Query(default="30d"),
) -> AdminOpenAiStats:
    return AdminOpenAiStats(**admin_service.get_openai_stats(db, period=period))


@router.get("/errors", response_model=list[AdminErrorRow])
def admin_errors(
    _: User = Depends(require_admin_user),
    db: Session = Depends(get_db),
    limit: int = 100,
    offset: int = 0,
) -> list[AdminErrorRow]:
    from app.services import admin_errors as admin_errors_service

    return [
        AdminErrorRow(**row)
        for row in admin_errors_service.list_errors(db, limit=limit, offset=offset)
    ]


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
            detail="Service unavailable",
        ) from exc
    return AdminBackupCreateResponse(
        **result,
        message=f"Резервная копия создана: {result['id']}",
    )
