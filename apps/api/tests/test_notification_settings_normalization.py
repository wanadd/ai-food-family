"""Tests for notification/care settings normalization."""

from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

API_ROOT = Path(__file__).resolve().parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.services.normalization import notifications as notif  # noqa: E402


def test_is_valid_time():
    assert notif.is_valid_time("09:00") is True
    assert notif.is_valid_time("23:59") is True
    assert notif.is_valid_time("24:00") is False
    assert notif.is_valid_time("9:60") is False
    assert notif.is_valid_time("abc") is False
    assert notif.is_valid_time(None) is False


def test_normalize_time_pads_and_falls_back():
    assert notif.normalize_time("9:05", "08:00") == "09:05"
    assert notif.normalize_time("bad", "08:00") == "08:00"


def test_normalize_quiet_hours_requires_both():
    assert notif.normalize_quiet_hours("22:00", "07:00") == ("22:00", "07:00")
    assert notif.normalize_quiet_hours("22:00", None) == (None, None)
    assert notif.normalize_quiet_hours("bad", "07:00") == (None, None)


def test_normalize_quiet_hours_zero_length_cleared():
    assert notif.normalize_quiet_hours("08:00", "08:00") == (None, None)


def test_normalize_care_level():
    assert notif.normalize_care_level("INTENSE") == "intense"
    assert notif.normalize_care_level("weird") == "standard"
    assert notif.normalize_care_level(None) == "standard"


def test_normalize_timezone_default():
    assert notif.normalize_timezone("") == notif.DEFAULT_TIMEZONE
    assert notif.normalize_timezone("Europe/Berlin") == "Europe/Berlin"


def test_normalize_notification_settings_dict():
    out = notif.normalize_notification_settings(
        {"buy_reminder_time": "9:0", "timezone": "", "unknown": 1}
    )
    assert out["buy_reminder_time"] == "09:00"
    assert out["timezone"] == notif.DEFAULT_TIMEZONE
    assert out["unknown"] == 1
