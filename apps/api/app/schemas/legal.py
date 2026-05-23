from datetime import datetime

from pydantic import BaseModel


class LegalDocumentInfo(BaseModel):
    id: str
    title: str
    url: str
    stub_text: str
    version: str


class LegalDocumentsResponse(BaseModel):
    version: str
    documents: list[LegalDocumentInfo]


class LegalAcceptRequest(BaseModel):
    accepted_terms: bool
    accepted_privacy: bool
    accepted_personal_data: bool


class LegalStatusResponse(BaseModel):
    version: str
    accepted_terms: bool
    accepted_privacy: bool
    accepted_personal_data: bool
    legal_accepted_at: datetime | None
    documents_up_to_date: bool
    can_use_app: bool
    phone_number: str | None
    phone_skipped: bool


class DataDeletionRequestResponse(BaseModel):
    status: str
    message: str
    request_id: str | None = None
