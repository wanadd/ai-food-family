from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from app.services.member_age import MAX_AGE_MONTHS, normalize_age_months, validate_age_months


class VirtualNutritionProfile(BaseModel):
    """Stored in family_members.nutrition_profile JSON."""

    age_months: int | None = Field(default=None, ge=0, le=MAX_AGE_MONTHS)
    nutrition_goal: str | None = None
    custom_nutrition_goal: str | None = Field(default=None, max_length=200)
    allergies: list[str] = Field(default_factory=list)
    custom_allergies: list[str] = Field(default_factory=list)
    restrictions: list[str] = Field(default_factory=list)
    custom_restrictions: list[str] = Field(default_factory=list)
    favorite_foods: str = ""
    disliked_foods: str = ""
    notes: str = ""

    # Legacy fields (read/write compat)
    age: int | None = Field(default=None, ge=0, le=120)
    age_years: int | None = Field(default=None, ge=0, le=130)
    diets: list[str] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def migrate_legacy_age(cls, data):
        if not isinstance(data, dict):
            return data
        if data.get("age_months") is None:
            resolved = normalize_age_months(
                age_months=data.get("age_months"),
                age_years=data.get("age_years"),
                age=data.get("age"),
            )
            if resolved is not None:
                data = {**data, "age_months": resolved}
        return data

    @field_validator("age_months")
    @classmethod
    def check_age_months(cls, value: int | None) -> int | None:
        if value is None:
            return value
        validate_age_months(value)
        return value


class VirtualMemberCreateRequest(BaseModel):
    display_name: str = Field(min_length=1, max_length=120)
    virtual_kind: str | None = Field(default=None, max_length=32)
    role: Literal["adult", "child"] = "child"
    nutrition: VirtualNutritionProfile = Field(default_factory=VirtualNutritionProfile)
    guardian_consent: bool = False
    data_consent: bool = False


class MemberNutritionUpdateRequest(BaseModel):
    nutrition: VirtualNutritionProfile


class AllowAdminEditRequest(BaseModel):
    allow_admin_profile_edit: bool = False
