"""Tests for local audit auth harness."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

API_ROOT = Path(__file__).resolve().parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app import deps  # noqa: E402
from app.config import settings  # noqa: E402
from app.models.user import User  # noqa: E402
from app.services import audit_auth  # noqa: E402
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@pytest.fixture()
def mock_request():
    request = MagicMock()
    request.url.path = "/test"
    request.headers.get = lambda key, default=None: (
        "http://localhost:3002" if key == "origin" else default
    )
    return request


@pytest.fixture()
def db():
    engine = create_engine("sqlite:///:memory:")
    User.__table__.create(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(autouse=True)
def _reset_audit(monkeypatch):
    monkeypatch.setattr(settings, "environment", "development")
    monkeypatch.setattr(settings, "planam_audit_mode", False)
    monkeypatch.setattr(settings, "planam_audit_secret", None)
    monkeypatch.setattr(
        "app.services.subscription.ensure_user_billing",
        lambda _db, _user: None,
    )


def test_audit_mode_disabled_by_default():
    assert audit_auth.is_audit_mode_enabled() is False


def test_audit_mode_enabled_only_in_development(monkeypatch):
    monkeypatch.setattr(settings, "planam_audit_mode", True)
    assert audit_auth.is_audit_mode_enabled() is True
    monkeypatch.setattr(settings, "environment", "production")
    assert audit_auth.is_audit_mode_enabled() is False


def test_unknown_persona_rejected(db, monkeypatch):
    monkeypatch.setattr(settings, "planam_audit_mode", True)
    with pytest.raises(HTTPException) as exc:
        audit_auth.get_or_create_audit_user(db, "audit_hacker")
    assert exc.value.status_code == 403


def test_known_persona_created(db, monkeypatch):
    monkeypatch.setattr(settings, "planam_audit_mode", True)
    user, is_new = audit_auth.get_or_create_audit_user(db, "audit_personal_day5")
    assert user.telegram_id == 900_000_002
    assert user.accepted_terms is True
    assert is_new is True
    user2, is_new2 = audit_auth.get_or_create_audit_user(db, "audit_personal_day5")
    assert user2.id == user.id
    assert is_new2 is False


def test_audit_headers_ignored_when_mode_off(db, monkeypatch):
    monkeypatch.setattr(settings, "planam_audit_mode", False)
    result = audit_auth.get_audit_user_from_request(
        db,
        init_data=audit_auth.audit_init_data_for_persona("audit_new_user"),
        header_persona="audit_new_user",
        header_user=None,
        header_secret=None,
    )
    assert result is None


def test_audit_secret_required_when_configured(db, monkeypatch):
    monkeypatch.setattr(settings, "planam_audit_mode", True)
    monkeypatch.setattr(settings, "planam_audit_secret", "top-secret")
    with pytest.raises(HTTPException) as exc:
        audit_auth.get_audit_user_from_request(
            db,
            init_data=audit_auth.audit_init_data_for_persona("audit_new_user"),
            header_persona="audit_new_user",
            header_user=None,
            header_secret="wrong",
        )
    assert exc.value.status_code == 403


def test_audit_user_from_request_success(db, monkeypatch):
    monkeypatch.setattr(settings, "planam_audit_mode", True)
    user = audit_auth.get_audit_user_from_request(
        db,
        init_data=audit_auth.audit_init_data_for_persona("audit_athlete"),
        header_persona="audit_athlete",
        header_user="audit_athlete",
        header_secret=None,
    )
    assert user is not None
    assert user.username == "audit_athlete"


def test_get_current_user_audit_path(db, monkeypatch, mock_request):
    monkeypatch.setattr(settings, "planam_audit_mode", True)
    init = audit_auth.audit_init_data_for_persona("audit_healthy_eating")
    user = deps.get_current_user(
        mock_request,
        x_telegram_init_data=init,
        x_planam_audit_persona="audit_healthy_eating",
        x_planam_audit_user="audit_healthy_eating",
        x_planam_audit_secret=None,
        db=db,
    )
    assert user.username == "audit_healthy_eating"


def test_get_current_user_rejects_audit_init_when_disabled(db, monkeypatch, mock_request):
    monkeypatch.setattr(settings, "planam_audit_mode", False)
    init = audit_auth.audit_init_data_for_persona("audit_new_user")
    with pytest.raises(HTTPException) as exc:
        deps.get_current_user(
            mock_request,
            x_telegram_init_data=init,
            x_planam_audit_persona=None,
            x_planam_audit_user=None,
            x_planam_audit_secret=None,
            db=db,
        )
    assert exc.value.status_code == 403


def test_cannot_impersonate_arbitrary_user_id_via_headers(db, monkeypatch):
    monkeypatch.setattr(settings, "planam_audit_mode", True)
    result = audit_auth.get_audit_user_from_request(
        db,
        init_data=None,
        header_persona="999999",
        header_user="999999",
        header_secret=None,
    )
    assert result is None


def test_audit_cors_origins_added_in_development(monkeypatch):
    monkeypatch.setattr(settings, "environment", "development")
    monkeypatch.setattr(settings, "planam_audit_mode", True)
    monkeypatch.setattr(settings, "backend_cors_origins", "http://localhost:3000")
    origins = settings.effective_cors_origins
    assert "http://localhost:3000" in origins
    assert "http://localhost:3002" in origins
    assert "http://127.0.0.1:3002" in origins


def test_audit_cors_origins_not_added_in_production(monkeypatch):
    monkeypatch.setattr(settings, "environment", "production")
    monkeypatch.setattr(settings, "planam_audit_mode", True)
    monkeypatch.setattr(settings, "backend_cors_origins", "http://localhost:3000")
    origins = settings.effective_cors_origins
    assert origins == ["http://localhost:3000"]
    assert "http://localhost:3002" not in origins
