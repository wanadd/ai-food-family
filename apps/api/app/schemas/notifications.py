import re
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

TIME_PATTERN = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")

SUPPORTED_TIMEZONES = [
    "Europe/Moscow",
    "Europe/Kaliningrad",
    "Europe/Samara",
    "Asia/Yekaterinburg",
    "Asia/Omsk",
    "Asia/Krasnoyarsk",
    "Asia/Irkutsk",
    "Asia/Vladivostok",
    "UTC",
]


class NotificationSettingsResponse(BaseModel):
    buy_reminder_enabled: bool
    cook_reminder_enabled: bool
    buy_reminder_time: str
    cook_reminder_time: str
    timezone: str
    updated_at: datetime | None = None


class NotificationSettingsUpdate(BaseModel):
    buy_reminder_enabled: bool | None = None
    cook_reminder_enabled: bool | None = None
    buy_reminder_time: str | None = Field(default=None, max_length=5)
    cook_reminder_time: str | None = Field(default=None, max_length=5)
    timezone: str | None = Field(default=None, max_length=64)

    @field_validator("buy_reminder_time", "cook_reminder_time")
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
        if value not in SUPPORTED_TIMEZONES:
            raise ValueError(f"Unsupported timezone. Use one of: {SUPPORTED_TIMEZONES}")
        return value
