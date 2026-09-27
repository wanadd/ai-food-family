from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field


class EventCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    event_type: str = Field(default="other", min_length=1, max_length=80)
    starts_at: datetime
    ends_at: datetime | None = None
    collaboration_mode: str = Field(default="ORGANIZER_ONLY", pattern="^(ORGANIZER_ONLY|RESTRICTIONS_COLLECTION|COLLABORATIVE_PLANNING)$")


class EventUpdateRequest(BaseModel):
    expected_version: int = Field(ge=1)
    title: str | None = Field(default=None, min_length=1, max_length=200)
    event_type: str | None = Field(default=None, min_length=1, max_length=80)
    starts_at: datetime | None = None
    ends_at: datetime | None = None


class LifecycleRequest(BaseModel):
    expected_version: int = Field(ge=1)
    status: str = Field(pattern="^(DRAFT|OPEN|PLANNING|READY|ACTIVE|COMPLETED|CANCELLED)$")


class ParticipantCreateRequest(BaseModel):
    display_name: str = Field(min_length=1, max_length=160)
    person_id: str | None = None
    participant_kind: str = Field(default="GUEST", pattern="^(PERSON|GUEST|DEPENDENT)$")
    age_group: str = Field(default="UNKNOWN", pattern="^(ADULT|CHILD|UNKNOWN)$")
    attendance_status: str = Field(default="PENDING", pattern="^(PENDING|ACCEPTED|DECLINED)$")


class ParticipantUpdateRequest(BaseModel):
    expected_version: int = Field(ge=1)
    display_name: str | None = Field(default=None, min_length=1, max_length=160)
    attendance_status: str | None = Field(default=None, pattern="^(PENDING|ACCEPTED|DECLINED)$")


class FoodFactsRequest(BaseModel):
    knowledge_state: str = Field(pattern="^(NOT_PROVIDED|UNKNOWN|KNOWN_NONE|KNOWN_PRESENT)$")
    restrictions: list[dict] = Field(default_factory=list)


class InvitationCreateRequest(BaseModel):
    expires_at: datetime | None = None


class InvitationRespondParticipant(BaseModel):
    display_name: str = Field(min_length=1, max_length=160)
    age_group: str = Field(default="UNKNOWN", pattern="^(ADULT|CHILD|UNKNOWN)$")
    knowledge_state: str = Field(default="UNKNOWN", pattern="^(NOT_PROVIDED|UNKNOWN|KNOWN_NONE|KNOWN_PRESENT)$")
    restrictions: list[dict] = Field(default_factory=list)


class InvitationRespondRequest(BaseModel):
    participants: list[InvitationRespondParticipant] = Field(min_length=1, max_length=50)


class MenuItemRequest(BaseModel):
    slot_key: str = Field(min_length=1, max_length=96)
    recipe_version_id: str | None = None
    servings: float | None = Field(default=None, gt=0)
    participant_ids: list[str] = Field(default_factory=list)


class MenuRevisionRequest(BaseModel):
    expected_version: int = Field(ge=1)
    items: list[MenuItemRequest] = Field(min_length=1, max_length=100)


class ShoppingDemandRequest(BaseModel):
    display_text: str = Field(min_length=1, max_length=300)
    quantity: float | None = Field(default=None, gt=0)
    unit: str | None = Field(default=None, max_length=32)
    uncertainty: str = Field(default="UNKNOWN", pattern="^(UNKNOWN|KNOWN)$")
    source_key: str = Field(min_length=1, max_length=160)


class ShoppingGenerateRequest(BaseModel):
    expected_version: int | None = Field(default=None, ge=1)
    items: list[ShoppingDemandRequest] = Field(default_factory=list, max_length=500)
