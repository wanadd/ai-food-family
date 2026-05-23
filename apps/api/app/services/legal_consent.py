from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.legal.documents import DOCUMENTS, LEGAL_DOCUMENTS_VERSION
from app.models.user import User
from app.schemas.legal import (
    LegalAcceptRequest,
    LegalDocumentInfo,
    LegalDocumentsResponse,
    LegalStatusResponse,
)

LEGAL_REQUIRED_MESSAGE = (
    "Примите пользовательское соглашение, политику конфиденциальности "
    "и согласие на обработку данных в боте (/start) или в приложении."
)


def user_has_legal_consent(user: User | None) -> bool:
    if user is None:
        return False
    return bool(
        user.accepted_terms
        and user.accepted_privacy
        and user.accepted_personal_data
        and user.legal_documents_version == LEGAL_DOCUMENTS_VERSION
    )


def user_can_access_app(user: User | None) -> bool:
    if not user_has_legal_consent(user):
        return False
    if user and user.phone_number and user.phone_number.strip():
        return True
    return bool(user and user.phone_skipped)


def get_documents_response() -> LegalDocumentsResponse:
    docs = [
        LegalDocumentInfo(
            id=meta["id"],
            title=meta["title"],
            url=meta["url"],
            stub_text=meta["stub_text"],
            version=LEGAL_DOCUMENTS_VERSION,
        )
        for meta in DOCUMENTS.values()
    ]
    return LegalDocumentsResponse(version=LEGAL_DOCUMENTS_VERSION, documents=docs)


def get_legal_status(user: User) -> LegalStatusResponse:
    return LegalStatusResponse(
        version=LEGAL_DOCUMENTS_VERSION,
        accepted_terms=bool(user.accepted_terms),
        accepted_privacy=bool(user.accepted_privacy),
        accepted_personal_data=bool(user.accepted_personal_data),
        legal_accepted_at=user.legal_accepted_at,
        documents_up_to_date=user_has_legal_consent(user),
        can_use_app=user_can_access_app(user),
        phone_number=user.phone_number,
        phone_skipped=bool(user.phone_skipped),
    )


def accept_legal(db: Session, user: User, payload: LegalAcceptRequest) -> User:
    if not (
        payload.accepted_terms
        and payload.accepted_privacy
        and payload.accepted_personal_data
    ):
        raise ValueError("Необходимо принять все документы")

    now = datetime.now(timezone.utc)
    user.accepted_terms = True
    user.accepted_privacy = True
    user.accepted_personal_data = True
    user.legal_accepted_at = now
    user.legal_documents_version = LEGAL_DOCUMENTS_VERSION
    db.commit()
    db.refresh(user)
    return user


def mark_phone_skipped(db: Session, user: User) -> User:
    user.phone_skipped = True
    db.commit()
    db.refresh(user)
    return user
