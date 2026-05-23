from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_verified_user
from app.models.user import User
from app.schemas.care import (
    CareNotificationResponse,
    CareSettingsResponse,
    CareSettingsUpdate,
    CareTipsResponse,
    TestCareNotificationRequest,
    TestCareNotificationResponse,
)
from app.services import care as care_service

router = APIRouter(prefix="/care", tags=["care"])


@router.get("/settings", response_model=CareSettingsResponse)
def get_care_settings(
    user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
) -> CareSettingsResponse:
    return care_service.get_care_settings(db, user)


@router.patch("/settings", response_model=CareSettingsResponse)
def patch_care_settings(
    payload: CareSettingsUpdate,
    user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
) -> CareSettingsResponse:
    return care_service.update_care_settings(db, user, payload)


@router.get("/notifications", response_model=list[CareNotificationResponse])
def list_care_notifications(
    user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
) -> list[CareNotificationResponse]:
    return care_service.list_care_notifications(db, user)


@router.get("/tips", response_model=CareTipsResponse)
def preview_care_tips(
    user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
) -> CareTipsResponse:
    ctx = care_service.build_care_context(db, user)
    return CareTipsResponse(tips=care_service.generate_basic_care_tips(db, user, ctx))


@router.post("/test-notification", response_model=TestCareNotificationResponse)
async def send_test_notification(
    payload: TestCareNotificationRequest,
    user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
) -> TestCareNotificationResponse:
    ok, message, notification = await care_service.send_care_notification_by_type(
        db,
        user,
        payload.notification_type,
        ignore_quiet_hours=True,
        ignore_cooldown=True,
    )
    return TestCareNotificationResponse(
        ok=ok,
        message=message,
        notification_id=notification.id if notification else None,
    )
