import re
from datetime import datetime
from typing import Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, Field, field_validator

TIME_PATTERN = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")

CareModeOption = Literal["off", "minimal", "normal", "active"]


class NotificationSettingsResponse(BaseModel):
    notifications_onboarded: bool = False
    care_mode: CareModeOption = "off"
    enabled_notification_types: list[str] = Field(default_factory=list)
    buy_reminder_enabled: bool
    cook_reminder_enabled: bool
    cook_breakfast_enabled: bool
    cook_lunch_enabled: bool
    cook_dinner_enabled: bool
    buy_reminder_time: str
    cook_reminder_time: str
    cook_breakfast_time: str
    cook_lunch_time: str
    cook_dinner_time: str
    timezone: str
    updated_at: datetime | None = None


class NotificationOnboardingRequest(BaseModel):
    care_mode: CareModeOption = "off"
    enabled_notification_types: list[str] = Field(default_factory=list)
    quiet_hours_start: str | None = Field(default="22:00", max_length=5)
    quiet_hours_end: str | None = Field(default="09:00", max_length=5)
    timezone: str | None = Field(default=None, max_length=64)


class NotificationSettingsUpdate(BaseModel):
    buy_reminder_enabled: bool | None = None
    cook_reminder_enabled: bool | None = None
    cook_breakfast_enabled: bool | None = None
    cook_lunch_enabled: bool | None = None
    cook_dinner_enabled: bool | None = None
    buy_reminder_time: str | None = Field(default=None, max_length=5)
    cook_reminder_time: str | None = Field(default=None, max_length=5)
    cook_breakfast_time: str | None = Field(default=None, max_length=5)
    cook_lunch_time: str | None = Field(default=None, max_length=5)
    cook_dinner_time: str | None = Field(default=None, max_length=5)
    timezone: str | None = Field(default=None, max_length=64)

    @field_validator(
        "buy_reminder_time",
        "cook_reminder_time",
        "cook_breakfast_time",
        "cook_lunch_time",
        "cook_dinner_time",
    )
    @classmethod
    def validate_time(cls, value: str | None) -> str | None:
        if value is None:
            return value
        if not TIME_PATTERN.match(value):
            raise ValueError("Time must be in HH:MM format (00:00–23:59)")
        return value

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str | None) -> str | None:
        if value is None:
            return value
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as exc:
            raise ValueError("Invalid timezone") from exc
        return value
