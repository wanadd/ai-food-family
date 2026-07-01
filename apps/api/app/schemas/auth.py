from datetime import datetime

from pydantic import BaseModel, Field


class TelegramAuthRequest(BaseModel):
    init_data: str = Field(min_length=1)


class UserResponse(BaseModel):
    id: int
    telegram_id: int
    username: str | None
    first_name: str | None
    last_name: str | None
    language_code: str | None
    phone_number: str | None = None
    photo_url: str | None
    accepted_terms: bool = False
    accepted_privacy: bool = False
    accepted_personal_data: bool = False
    legal_accepted_at: datetime | None = None
    legal_documents_version: str | None = None
    phone_skipped: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TelegramAuthResponse(BaseModel):
    user: UserResponse
    is_new: bool
    phone_verified: bool = False
    legal_accepted: bool = False
    can_use_app: bool = False


class DevLoginResponse(TelegramAuthResponse):
    dev_init_data: str


class AuditLoginResponse(TelegramAuthResponse):
    audit_init_data: str
    audit_persona: str


class LocalParityLoginResponse(TelegramAuthResponse):
    local_parity_init_data: str
