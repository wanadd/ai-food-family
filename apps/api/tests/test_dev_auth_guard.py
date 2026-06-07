"""Defense-in-depth: dev-auth must honor is_blocked / is_deleted.

dev-auth is disabled in production via settings.is_development, but the
get_current_user() dev branch must still refuse blocked/deleted dev users.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
from fastapi import HTTPException, status

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

API_ROOT = Path(__file__).resolve().parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app import deps  # noqa: E402
from app.models.user import User  # noqa: E402
from app.services.dev_auth import DEV_INIT_DATA  # noqa: E402


def _call_with_dev_user(monkeypatch, user: User, *, dev_enabled: bool = True):
    monkeypatch.setattr(deps, "dev_auth_enabled", lambda: dev_enabled)
    monkeypatch.setattr(deps, "get_or_create_dev_user", lambda db: (user, False))
    return deps.get_current_user(x_telegram_init_data=DEV_INIT_DATA, db=None)


def test_dev_branch_returns_active_user(monkeypatch):
    user = User(telegram_id=999_999_999, is_blocked=False, is_deleted=False)
    result = _call_with_dev_user(monkeypatch, user)
    assert result is user


def test_dev_branch_rejects_blocked_user(monkeypatch):
    user = User(telegram_id=999_999_999, is_blocked=True, is_deleted=False)
    with pytest.raises(HTTPException) as exc:
        _call_with_dev_user(monkeypatch, user)
    assert exc.value.status_code == status.HTTP_403_FORBIDDEN


def test_dev_branch_rejects_deleted_user(monkeypatch):
    user = User(telegram_id=999_999_999, is_blocked=False, is_deleted=True)
    with pytest.raises(HTTPException) as exc:
        _call_with_dev_user(monkeypatch, user)
    assert exc.value.status_code == status.HTTP_403_FORBIDDEN


def test_dev_branch_disabled_returns_403(monkeypatch):
    user = User(telegram_id=999_999_999, is_blocked=False, is_deleted=False)
    with pytest.raises(HTTPException) as exc:
        _call_with_dev_user(monkeypatch, user, dev_enabled=False)
    assert exc.value.status_code == status.HTTP_403_FORBIDDEN
    assert exc.value.detail == "Dev auth is disabled"


def test_missing_header_returns_401():
    with pytest.raises(HTTPException) as exc:
        deps.get_current_user(x_telegram_init_data=None, db=None)
    assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED
