from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_app_scope, get_verified_user
from app.models.user import User
from app.schemas.deferred_advice import (
    DeferredAdviceCreate,
    DeferredAdviceResponse,
    DeferredAdviceUpdate,
)
from app.schemas.nutritionist import NutritionistAskRequest, NutritionistAskResponse
from app.schemas.water_intake import WaterIntakeCreate, WaterIntakeTodayResponse
from app.services.app_scope import AppScope
from app.services import nutritionist as nutritionist_service
from app.services import deferred_advice as deferred_advice_service
from app.services import water_intake as water_intake_service

router = APIRouter(prefix="/nutritionist", tags=["nutritionist"])


@router.post("/ask", response_model=NutritionistAskResponse)
async def ask_nutritionist(
    payload: NutritionistAskRequest,
    user: User = Depends(get_verified_user),
    scope: AppScope = Depends(get_app_scope),
    db: Session = Depends(get_db),
) -> NutritionistAskResponse:
    answer, used_ai = await nutritionist_service.ask_nutritionist(
        db, user, scope, payload.message.strip()
    )
    return NutritionistAskResponse(answer=answer, used_ai=used_ai)


@router.get("/deferred-advice", response_model=list[DeferredAdviceResponse])
def list_deferred_advice(
    user: User = Depends(get_verified_user),
    scope: AppScope = Depends(get_app_scope),
    db: Session = Depends(get_db),
) -> list[DeferredAdviceResponse]:
    return deferred_advice_service.list_deferred(db, user, scope)


@router.post(
    "/deferred-advice",
    response_model=DeferredAdviceResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_deferred_advice(
    payload: DeferredAdviceCreate,
    user: User = Depends(get_verified_user),
    scope: AppScope = Depends(get_app_scope),
    db: Session = Depends(get_db),
) -> DeferredAdviceResponse:
    return deferred_advice_service.defer_advice(db, user, scope, payload)


@router.patch("/deferred-advice/{advice_id}", response_model=DeferredAdviceResponse)
def patch_deferred_advice(
    advice_id: int,
    payload: DeferredAdviceUpdate,
    user: User = Depends(get_verified_user),
    scope: AppScope = Depends(get_app_scope),
    db: Session = Depends(get_db),
) -> DeferredAdviceResponse:
    return deferred_advice_service.update_deferred(db, user, scope, advice_id, payload)


@router.delete("/deferred-advice/{advice_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_deferred_advice(
    advice_id: int,
    user: User = Depends(get_verified_user),
    scope: AppScope = Depends(get_app_scope),
    db: Session = Depends(get_db),
) -> None:
    deferred_advice_service.delete_deferred(db, user, scope, advice_id)


@router.get("/water/today", response_model=WaterIntakeTodayResponse)
def water_today(
    user: User = Depends(get_verified_user),
    scope: AppScope = Depends(get_app_scope),
    db: Session = Depends(get_db),
) -> WaterIntakeTodayResponse:
    return water_intake_service.get_today_total(db, user, scope)


@router.post("/water", response_model=WaterIntakeTodayResponse)
def add_water(
    payload: WaterIntakeCreate,
    user: User = Depends(get_verified_user),
    scope: AppScope = Depends(get_app_scope),
    db: Session = Depends(get_db),
) -> WaterIntakeTodayResponse:
    return water_intake_service.add_water(db, user, scope, payload)
