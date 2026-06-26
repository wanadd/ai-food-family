import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_admin_user
from app.models.user import User
from app.schemas.admin import (
    AdminAiUsageRow,
    AdminAmaTransactionRow,
    AdminAmsActionRequest,
    AdminAmsSummary,
    AdminBackupCreateResponse,
    AdminBackupRow,
    AdminBlockReasonRequest,
    AdminDeductAmsRequest,
    AdminErrorRow,
    AdminFamilyCard,
    AdminFamilyRenameRequest,
    AdminFamilyRow,
    AdminFamilyTransferRequest,
    AdminGrantAmsRequest,
    AdminGrantFamilyAmsRequest,
    AdminGrantResponse,
    AdminHardDeleteRequest,
    AdminGrantSubscriptionRequest,
    AdminOpenAiStats,
    AdminPingResponse,
    AdminPlanOption,
    AdminSubscriptionActionRequest,
    AdminSubscriptionExtendRequest,
    AdminSubscriptionRow,
    AdminSummaryResponse,
    AdminUserCard,
    AdminUserRow,
)
from app.services import admin as admin_service
from app.services import admin_manage as manage
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


@router.get("/users/{user_id}", response_model=AdminUserCard)
def admin_user_card(
    user_id: int,
    _: User = Depends(require_admin_user),
    db: Session = Depends(get_db),
) -> AdminUserCard:
    return AdminUserCard(**manage.get_user_card(db, user_id))


@router.delete("/users/{user_id}", response_model=AdminGrantResponse)
def admin_delete_user(
    user_id: int,
    admin: User = Depends(require_admin_user),
    db: Session = Depends(get_db),
) -> AdminGrantResponse:
    manage.delete_user(db, user_id=user_id, admin=admin)
    return AdminGrantResponse(user_id=user_id, message="Пользователь архивирован (скрыт из списка)")


@router.post("/users/{user_id}/block", response_model=AdminGrantResponse)
def admin_block_user(
    user_id: int,
    payload: AdminBlockReasonRequest,
    admin: User = Depends(require_admin_user),
    db: Session = Depends(get_db),
) -> AdminGrantResponse:
    manage.block_user(db, user_id=user_id, admin=admin, reason=payload.reason)
    return AdminGrantResponse(user_id=user_id, message="Пользователь заблокирован")


@router.post("/users/{user_id}/unblock", response_model=AdminGrantResponse)
def admin_unblock_user(
    user_id: int,
    admin: User = Depends(require_admin_user),
    db: Session = Depends(get_db),
) -> AdminGrantResponse:
    manage.unblock_user(db, user_id=user_id, admin=admin)
    return AdminGrantResponse(user_id=user_id, message="Пользователь разблокирован")


@router.post("/users/{user_id}/clear-data", response_model=AdminGrantResponse)
def admin_clear_user_data(
    user_id: int,
    admin: User = Depends(require_admin_user),
    db: Session = Depends(get_db),
) -> AdminGrantResponse:
    manage.clear_user_data(db, user_id=user_id, admin=admin)
    return AdminGrantResponse(user_id=user_id, message="Данные пользователя очищены")


@router.post("/users/{user_id}/reset-as-new", response_model=AdminGrantResponse)
def admin_reset_user_as_new(
    user_id: int,
    admin: User = Depends(require_admin_user),
    db: Session = Depends(get_db),
) -> AdminGrantResponse:
    manage.reset_user_as_new(db, user_id=user_id, admin=admin)
    return AdminGrantResponse(
        user_id=user_id,
        message="Пользователь сброшен. При следующем входе создастся новый аккаунт с 7 днями доступа.",
    )


@router.post("/users/{user_id}/hard-delete", response_model=AdminGrantResponse)
def admin_hard_delete_user(
    user_id: int,
    payload: AdminHardDeleteRequest,
    admin: User = Depends(require_admin_user),
    db: Session = Depends(get_db),
) -> AdminGrantResponse:
    manage.hard_delete_user(
        db, user_id=user_id, admin=admin, confirmation=payload.confirmation
    )
    return AdminGrantResponse(user_id=user_id, message="Пользователь удалён навсегда")


@router.post("/users/{user_id}/reset/onboarding", response_model=AdminGrantResponse)
def admin_reset_onboarding(
    user_id: int,
    admin: User = Depends(require_admin_user),
    db: Session = Depends(get_db),
) -> AdminGrantResponse:
    manage.reset_user_onboarding(db, user_id=user_id, admin=admin)
    return AdminGrantResponse(user_id=user_id, message="Onboarding сброшен")


@router.post("/users/{user_id}/reset/phone", response_model=AdminGrantResponse)
def admin_reset_phone(
    user_id: int,
    admin: User = Depends(require_admin_user),
    db: Session = Depends(get_db),
) -> AdminGrantResponse:
    manage.reset_user_phone(db, user_id=user_id, admin=admin)
    return AdminGrantResponse(user_id=user_id, message="Телефон сброшен")


@router.post("/users/{user_id}/reset/legal", response_model=AdminGrantResponse)
def admin_reset_legal(
    user_id: int,
    admin: User = Depends(require_admin_user),
    db: Session = Depends(get_db),
) -> AdminGrantResponse:
    manage.reset_user_legal(db, user_id=user_id, admin=admin)
    return AdminGrantResponse(user_id=user_id, message="Согласия сброшены")


@router.post("/users/{user_id}/reset/nutrition", response_model=AdminGrantResponse)
def admin_reset_nutrition(
    user_id: int,
    admin: User = Depends(require_admin_user),
    db: Session = Depends(get_db),
) -> AdminGrantResponse:
    manage.reset_user_nutrition(db, user_id=user_id, admin=admin)
    return AdminGrantResponse(user_id=user_id, message="Профиль питания сброшен")


@router.post("/users/{user_id}/subscription/grant", response_model=AdminGrantResponse)
def admin_user_sub_grant(
    user_id: int,
    payload: AdminSubscriptionActionRequest,
    admin: User = Depends(require_admin_user),
    db: Session = Depends(get_db),
) -> AdminGrantResponse:
    manage.grant_user_subscription(
        db,
        user_id=user_id,
        admin=admin,
        plan_code=payload.plan_code,
        days=payload.days,
        reason=payload.reason,
        expires_at=payload.expires_at,
        as_trial=payload.as_trial,
    )
    return AdminGrantResponse(user_id=user_id, message="Подписка выдана")


@router.post("/users/{user_id}/subscription/extend", response_model=AdminGrantResponse)
def admin_user_sub_extend(
    user_id: int,
    payload: AdminSubscriptionExtendRequest,
    admin: User = Depends(require_admin_user),
    db: Session = Depends(get_db),
) -> AdminGrantResponse:
    manage.extend_user_subscription(
        db, user_id=user_id, admin=admin, days=payload.days, reason=payload.reason
    )
    return AdminGrantResponse(user_id=user_id, message="Подписка продлена")


@router.post("/users/{user_id}/subscription/disable", response_model=AdminGrantResponse)
def admin_user_sub_disable(
    user_id: int,
    admin: User = Depends(require_admin_user),
    db: Session = Depends(get_db),
) -> AdminGrantResponse:
    manage.disable_user_subscription(db, user_id=user_id, admin=admin)
    return AdminGrantResponse(user_id=user_id, message="Подписка отключена")


@router.post("/users/{user_id}/subscription/change-plan", response_model=AdminGrantResponse)
def admin_user_sub_change(
    user_id: int,
    payload: AdminSubscriptionActionRequest,
    admin: User = Depends(require_admin_user),
    db: Session = Depends(get_db),
) -> AdminGrantResponse:
    manage.change_user_plan(
        db,
        user_id=user_id,
        admin=admin,
        plan_code=payload.plan_code,
        days=payload.days,
        reason=payload.reason,
    )
    return AdminGrantResponse(user_id=user_id, message="Тариф изменён")


@router.post("/users/{user_id}/ams/add", response_model=AdminGrantResponse)
def admin_user_ams_add(
    user_id: int,
    payload: AdminAmsActionRequest,
    admin: User = Depends(require_admin_user),
    db: Session = Depends(get_db),
) -> AdminGrantResponse:
    result = manage.add_user_ams(
        db,
        user_id=user_id,
        admin=admin,
        amount=payload.amount,
        reason=payload.reason,
        comment=payload.comment,
    )
    return AdminGrantResponse(
        user_id=user_id, message=f"Баланс: {result['balance']} Амов"
    )


@router.post("/users/{user_id}/ams/remove", response_model=AdminGrantResponse)
def admin_user_ams_remove(
    user_id: int,
    payload: AdminAmsActionRequest,
    admin: User = Depends(require_admin_user),
    db: Session = Depends(get_db),
) -> AdminGrantResponse:
    result = manage.remove_user_ams(
        db, user_id=user_id, admin=admin, amount=payload.amount, comment=payload.comment
    )
    return AdminGrantResponse(
        user_id=user_id, message=f"Баланс: {result['balance']} Амов"
    )


@router.post("/users/{user_id}/ams/reset", response_model=AdminGrantResponse)
def admin_user_ams_reset(
    user_id: int,
    admin: User = Depends(require_admin_user),
    db: Session = Depends(get_db),
) -> AdminGrantResponse:
    result = manage.reset_user_ams(db, user_id=user_id, admin=admin)
    return AdminGrantResponse(
        user_id=user_id, message=f"Баланс обнулён: {result['balance']}"
    )


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


@router.get("/families/{family_id}", response_model=AdminFamilyCard)
def admin_family_card(
    family_id: int,
    _: User = Depends(require_admin_user),
    db: Session = Depends(get_db),
) -> AdminFamilyCard:
    return AdminFamilyCard(**manage.get_family_card(db, family_id))


@router.patch("/families/{family_id}", response_model=AdminGrantResponse)
def admin_rename_family(
    family_id: int,
    payload: AdminFamilyRenameRequest,
    admin: User = Depends(require_admin_user),
    db: Session = Depends(get_db),
) -> AdminGrantResponse:
    manage.rename_family(db, family_id=family_id, name=payload.name, admin=admin)
    return AdminGrantResponse(family_id=family_id, message="Название обновлено")


@router.post("/families/{family_id}/block", response_model=AdminGrantResponse)
def admin_block_family(
    family_id: int,
    payload: AdminBlockReasonRequest,
    admin: User = Depends(require_admin_user),
    db: Session = Depends(get_db),
) -> AdminGrantResponse:
    manage.block_family(db, family_id=family_id, admin=admin, reason=payload.reason)
    return AdminGrantResponse(family_id=family_id, message="Семья заблокирована")


@router.post("/families/{family_id}/unblock", response_model=AdminGrantResponse)
def admin_unblock_family(
    family_id: int,
    admin: User = Depends(require_admin_user),
    db: Session = Depends(get_db),
) -> AdminGrantResponse:
    manage.unblock_family(db, family_id=family_id, admin=admin)
    return AdminGrantResponse(family_id=family_id, message="Семья разблокирована")


@router.delete("/families/{family_id}", response_model=AdminGrantResponse)
def admin_delete_family(
    family_id: int,
    admin: User = Depends(require_admin_user),
    db: Session = Depends(get_db),
) -> AdminGrantResponse:
    manage.delete_family_record(db, family_id=family_id, admin=admin)
    return AdminGrantResponse(family_id=family_id, message="Семья удалена")


@router.post("/families/{family_id}/transfer-owner", response_model=AdminGrantResponse)
def admin_transfer_family_owner(
    family_id: int,
    payload: AdminFamilyTransferRequest,
    admin: User = Depends(require_admin_user),
    db: Session = Depends(get_db),
) -> AdminGrantResponse:
    manage.transfer_family_owner(
        db,
        family_id=family_id,
        new_admin_user_id=payload.new_admin_user_id,
        admin=admin,
    )
    return AdminGrantResponse(family_id=family_id, message="Администратор семьи назначен")


@router.delete(
    "/families/{family_id}/members/{member_id}",
    response_model=AdminGrantResponse,
)
def admin_remove_family_member(
    family_id: int,
    member_id: int,
    admin: User = Depends(require_admin_user),
    db: Session = Depends(get_db),
) -> AdminGrantResponse:
    manage.remove_family_member(
        db, family_id=family_id, member_id=member_id, admin=admin
    )
    return AdminGrantResponse(family_id=family_id, message="Участник удалён")


@router.post("/families/{family_id}/subscription/grant", response_model=AdminGrantResponse)
def admin_family_sub_grant(
    family_id: int,
    payload: AdminSubscriptionActionRequest,
    admin: User = Depends(require_admin_user),
    db: Session = Depends(get_db),
) -> AdminGrantResponse:
    manage.grant_family_subscription(
        db,
        family_id=family_id,
        admin=admin,
        plan_code=payload.plan_code,
        days=payload.days,
        reason=payload.reason,
        as_trial=payload.as_trial,
    )
    return AdminGrantResponse(family_id=family_id, message="Семейная подписка выдана")


@router.post("/families/{family_id}/subscription/extend", response_model=AdminGrantResponse)
def admin_family_sub_extend(
    family_id: int,
    payload: AdminSubscriptionExtendRequest,
    admin: User = Depends(require_admin_user),
    db: Session = Depends(get_db),
) -> AdminGrantResponse:
    manage.extend_family_subscription(
        db, family_id=family_id, admin=admin, days=payload.days, reason=payload.reason
    )
    return AdminGrantResponse(family_id=family_id, message="Подписка продлена")


@router.post("/families/{family_id}/subscription/disable", response_model=AdminGrantResponse)
def admin_family_sub_disable(
    family_id: int,
    admin: User = Depends(require_admin_user),
    db: Session = Depends(get_db),
) -> AdminGrantResponse:
    manage.disable_family_subscription(db, family_id=family_id, admin=admin)
    return AdminGrantResponse(family_id=family_id, message="Подписка отключена")


@router.post(
    "/families/{family_id}/subscription/change-plan", response_model=AdminGrantResponse
)
def admin_family_sub_change(
    family_id: int,
    payload: AdminSubscriptionActionRequest,
    admin: User = Depends(require_admin_user),
    db: Session = Depends(get_db),
) -> AdminGrantResponse:
    manage.change_family_plan(
        db,
        family_id=family_id,
        admin=admin,
        plan_code=payload.plan_code,
        days=payload.days,
        reason=payload.reason,
    )
    return AdminGrantResponse(family_id=family_id, message="Тариф семьи изменён")


@router.post("/families/{family_id}/ams/add", response_model=AdminGrantResponse)
def admin_family_ams_add(
    family_id: int,
    payload: AdminAmsActionRequest,
    admin: User = Depends(require_admin_user),
    db: Session = Depends(get_db),
) -> AdminGrantResponse:
    result = manage.add_family_ams(
        db,
        family_id=family_id,
        admin=admin,
        amount=payload.amount,
        comment=payload.comment,
    )
    return AdminGrantResponse(
        family_id=family_id, message=f"Баланс семьи: {result['balance']}"
    )


@router.post("/families/{family_id}/ams/remove", response_model=AdminGrantResponse)
def admin_family_ams_remove(
    family_id: int,
    payload: AdminAmsActionRequest,
    admin: User = Depends(require_admin_user),
    db: Session = Depends(get_db),
) -> AdminGrantResponse:
    result = manage.remove_family_ams(
        db, family_id=family_id, admin=admin, amount=payload.amount, comment=payload.comment
    )
    return AdminGrantResponse(
        family_id=family_id, message=f"Баланс семьи: {result['balance']}"
    )


@router.post("/families/{family_id}/ams/reset", response_model=AdminGrantResponse)
def admin_family_ams_reset(
    family_id: int,
    admin: User = Depends(require_admin_user),
    db: Session = Depends(get_db),
) -> AdminGrantResponse:
    result = manage.reset_family_ams(db, family_id=family_id, admin=admin)
    return AdminGrantResponse(
        family_id=family_id, message=f"Баланс обнулён: {result['balance']}"
    )


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
