"""P0-3 / P0-4: Telegram webhook secret and debug endpoint removal."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

API_ROOT = Path(__file__).resolve().parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.routers import telegram_bot  # noqa: E402


def test_webhook_secret_required_in_production():
    request = MagicMock()
    request.headers.get.return_value = None

    with patch.object(telegram_bot.settings, "telegram_webhook_secret", ""), patch.object(
        telegram_bot.settings, "environment", "production"
    ):
        with pytest.raises(HTTPException) as exc:
            telegram_bot._validate_webhook_secret(request)
    assert exc.value.status_code == 503


def test_webhook_secret_skipped_in_development():
    request = MagicMock()
    request.headers.get.return_value = None

    with patch.object(telegram_bot.settings, "telegram_webhook_secret", ""), patch.object(
        telegram_bot.settings, "environment", "development"
    ):
        telegram_bot._validate_webhook_secret(request)


def test_webhook_secret_mismatch_returns_403():
    request = MagicMock()
    request.headers.get.return_value = "wrong"

    with patch.object(telegram_bot.settings, "telegram_webhook_secret", "expected"):
        with pytest.raises(HTTPException) as exc:
            telegram_bot._validate_webhook_secret(request)
    assert exc.value.status_code == 403


def test_debug_webhook_routes_removed():
    paths = [route.path for route in telegram_bot.router.routes]
    assert "/webhook/info" not in paths
    assert "/webhook/url" not in paths
