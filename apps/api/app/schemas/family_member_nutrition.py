from typing import Literal

from pydantic import BaseModel, Field


class VirtualNutritionProfile(BaseModel):
    age: int | None = Field(default=None, ge=0, le=120)
    age_years: int | None = Field(default=None, ge=0, le=17)
    age_months: int | None = Field(default=None, ge=0, le=11)
    nutrition_goal: str | None = None
    allergies: list[str] = Field(default_factory=list)
    restrictions: list[str] = Field(default_factory=list)
    diets: list[str] = Field(default_factory=list)
    favorite_foods: str = ""
    disliked_foods: str = ""
    notes: str = ""


class VirtualMemberCreateRequest(BaseModel):
    display_name: str = Field(min_length=1, max_length=120)
    virtual_kind: str | None = Field(default=None, max_length=32)
    role: Literal["adult", "child"] = "child"
    nutrition: VirtualNutritionProfile = Field(default_factory=VirtualNutritionProfile)


class MemberNutritionUpdateRequest(BaseModel):
    nutrition: VirtualNutritionProfile


class AllowAdminEditRequest(BaseModel):
    allow_admin_profile_edit: bool = False
