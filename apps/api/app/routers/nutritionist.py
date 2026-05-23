from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_app_scope, get_verified_user
from app.models.user import User
from app.schemas.nutritionist import NutritionistAskRequest, NutritionistAskResponse
from app.services.app_scope import AppScope
from app.services import nutritionist as nutritionist_service

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
