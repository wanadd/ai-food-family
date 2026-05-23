import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas.legal import (
    DataDeletionRequestResponse,
    LegalAcceptRequest,
    LegalDocumentsResponse,
    LegalStatusResponse,
)
from app.services import legal_consent as legal_service

router = APIRouter(prefix="/legal", tags=["legal"])


@router.get("/documents", response_model=LegalDocumentsResponse)
def list_documents() -> LegalDocumentsResponse:
    return legal_service.get_documents_response()


@router.get("/status", response_model=LegalStatusResponse)
def legal_status(
    user: User = Depends(get_current_user),
) -> LegalStatusResponse:
    return legal_service.get_legal_status(user)


@router.post("/accept", response_model=LegalStatusResponse)
def accept_documents(
    payload: LegalAcceptRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> LegalStatusResponse:
    try:
        legal_service.accept_legal(db, user, payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    return legal_service.get_legal_status(user)


@router.post("/skip-phone", response_model=LegalStatusResponse)
def skip_phone(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> LegalStatusResponse:
    if not legal_service.user_has_legal_consent(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=legal_service.LEGAL_REQUIRED_MESSAGE,
        )
    legal_service.mark_phone_skipped(db, user)
    return legal_service.get_legal_status(user)


@router.post("/delete-data-request", response_model=DataDeletionRequestResponse)
def request_data_deletion(
    user: User = Depends(get_current_user),
) -> DataDeletionRequestResponse:
    request_id = f"del-{user.id}-{uuid.uuid4().hex[:8]}"
    return DataDeletionRequestResponse(
        status="pending",
        message=(
            "Запрос принят. Удаление данных будет доступно в следующем обновлении. "
            "Поддержка свяжется с вами при необходимости."
        ),
        request_id=request_id,
    )
