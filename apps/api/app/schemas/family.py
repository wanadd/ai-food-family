from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

FamilyRoleType = Literal["admin", "adult", "child"]


class FamilyCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)


class FamilyMemberCreateRequest(BaseModel):
    display_name: str = Field(min_length=1, max_length=120)
    role: FamilyRoleType = "adult"
    goals: list[str] = Field(default_factory=list)
    restrictions: list[str] = Field(default_factory=list)


class FamilyMemberUpdateRequest(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=120)
    role: FamilyRoleType | None = None
    goals: list[str] | None = None
    restrictions: list[str] | None = None


class FamilyMemberResponse(BaseModel):
    id: int
    family_id: int
    user_id: int | None
    display_name: str
    role: FamilyRoleType
    goals: list[str]
    restrictions: list[str]
    is_you: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class FamilyResponse(BaseModel):
    id: int
    name: str
    members: list[FamilyMemberResponse]
    your_role: FamilyRoleType | None = None
    created_at: datetime
    updated_at: datetime
