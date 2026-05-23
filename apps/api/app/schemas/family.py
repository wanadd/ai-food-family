from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.family_member_nutrition import VirtualNutritionProfile

FamilyRoleType = Literal["admin", "adult", "child"]


class FamilyCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)


class FamilyInviteByPhoneRequest(BaseModel):
    phone_number: str = Field(min_length=5, max_length=32)


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
    is_virtual: bool = False
    member_type: Literal["telegram", "virtual"] = "telegram"
    role_label: str = "Участник"
    nutrition_goal_label: str | None = None
    nutrition_profile_complete: bool = False
    allow_admin_profile_edit: bool = False
    virtual_kind: str | None = None
    can_admin_edit_nutrition: bool = False
    nutrition_summary: dict | None = None
    virtual_nutrition: VirtualNutritionProfile | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class FamilyResponse(BaseModel):
    id: int
    name: str
    members: list[FamilyMemberResponse]
    members_count: int = 0
    plan_label: str = "Семейный"
    your_role: FamilyRoleType | None = None
    created_at: datetime
    updated_at: datetime
