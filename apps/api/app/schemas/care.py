from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

CareLevel = Literal["minimal", "standard", "active"]
CareNotificationType = Literal[
    "water",
    "protein",
    "menu",
    "shopping",
    "pantry",
    "progress",
    "family",
    "pro",
]


class CareSettingsResponse(BaseModel):
    water_enabled: bool
    protein_enabled: bool
    menu_enabled: bool
    shopping_enabled: bool
    pantry_enabled: bool
    progress_enabled: bool
    family_enabled: bool
    pro_enabled: bool
    care_level: CareLevel
    quiet_hours_start: str | None = None
    quiet_hours_end: str | None = None
    timezone: str | None = None
    has_pro_plan: bool = False
    updated_at: datetime | None = None


class CareSettingsUpdate(BaseModel):
    water_enabled: bool | None = None
    protein_enabled: bool | None = None
    menu_enabled: bool | None = None
    shopping_enabled: bool | None = None
    pantry_enabled: bool | None = None
    progress_enabled: bool | None = None
    family_enabled: bool | None = None
    pro_enabled: bool | None = None
    care_level: CareLevel | None = None
    quiet_hours_start: str | None = None
    quiet_hours_end: str | None = None
    timezone: str | None = None


class CareNotificationResponse(BaseModel):
    id: int
    type: str
    title: str
    message: str
    status: str
    sent_at: datetime | None
    created_at: datetime


class TestCareNotificationRequest(BaseModel):
    notification_type: CareNotificationType = "water"


class TestCareNotificationResponse(BaseModel):
    ok: bool
    message: str
    notification_id: int | None = None


class CareTipPreview(BaseModel):
    type: str
    title: str
    message: str


class CareTipsResponse(BaseModel):
    tips: list[CareTipPreview]
