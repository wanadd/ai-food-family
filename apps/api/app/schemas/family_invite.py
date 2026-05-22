from datetime import datetime

from pydantic import BaseModel, Field


class FamilyInviteCreateRequest(BaseModel):
    phone_number: str = Field(min_length=5, max_length=32)


class FamilyInviteResponse(BaseModel):
    id: int
    family_id: int
    status: str
    invite_token: str
    invited_phone_masked: str
    invited_user_id: int | None
    share_url: str
    share_text: str
    deep_link: str
    invitee_notified: bool
    family_name: str
    created_at: datetime

    model_config = {"from_attributes": True}
