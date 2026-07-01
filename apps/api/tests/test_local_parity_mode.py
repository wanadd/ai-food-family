from __future__ import annotations

import os
import sys
import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException, status
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

API_ROOT = Path(__file__).resolve().parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app import deps  # noqa: E402
from app.config import settings  # noqa: E402
from app.models.user import User  # noqa: E402
from app.routers.auth import authenticate_local_parity  # noqa: E402
from app.services import local_parity_auth, notification_scheduler  # noqa: E402
from app.telegram import messages  # noqa: E402


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
def reset_local_parity(monkeypatch):
    monkeypatch.setattr(settings, "environment", "development")
    monkeypatch.setattr(settings, "planam_env", "development")
    monkeypatch.setattr(settings, "local_parity_mode", False)
    monkeypatch.setattr(settings, "local_parity_telegram_id", None)
    monkeypatch.setattr(settings, "telegram_outbound_enabled", True)
    monkeypatch.setattr(settings, "notification_scheduler_enabled", True)
    monkeypatch.setattr(settings, "care_scheduler_enabled", True)
    monkeypatch.setattr(settings, "disable_external_side_effects", False)


def _enable_local_parity(monkeypatch, telegram_id: int | None = 589328345):
    monkeypatch.setattr(settings, "environment", "development")
    monkeypatch.setattr(settings, "planam_env", "local-parity")
    monkeypatch.setattr(settings, "local_parity_mode", True)
    monkeypatch.setattr(settings, "local_parity_telegram_id", telegram_id)


def test_local_parity_auth_endpoint_disabled_when_mode_false(db):
    with pytest.raises(HTTPException) as exc:
        authenticate_local_parity(db)
    assert exc.value.status_code == status.HTTP_403_FORBIDDEN


def test_local_parity_auth_enabled_only_outside_production(monkeypatch):
    _enable_local_parity(monkeypatch)
    assert local_parity_auth.local_parity_auth_enabled() is True
    monkeypatch.setattr(settings, "environment", "production")
    assert local_parity_auth.local_parity_auth_enabled() is False


def test_local_parity_auth_requires_configured_user_id(db, monkeypatch):
    _enable_local_parity(monkeypatch, telegram_id=None)
    with pytest.raises(HTTPException) as exc:
        authenticate_local_parity(db)
    assert exc.value.status_code == status.HTTP_403_FORBIDDEN


def test_local_parity_auth_requires_existing_snapshot_user(db, monkeypatch):
    _enable_local_parity(monkeypatch, telegram_id=589328345)
    with pytest.raises(HTTPException) as exc:
        authenticate_local_parity(db)
    assert exc.value.status_code == status.HTTP_404_NOT_FOUND


def test_local_parity_init_data_returns_configured_user(db, monkeypatch):
    _enable_local_parity(monkeypatch, telegram_id=589328345)
    user = User(
        telegram_id=589328345,
        username="qa_user",
        first_name="QA",
        is_blocked=False,
        is_deleted=False,
    )
    db.add(user)
    db.commit()
    token = local_parity_auth.local_parity_init_data_for_telegram_id(589328345)
    request = MagicMock()
    request.url.path = "/menus/selected"
    request.headers.get = lambda _key, default=None: default

    result = deps.get_current_user(
        request,
        x_telegram_init_data=token,
        db=db,
    )

    assert result.telegram_id == 589328345


def test_telegram_outbound_disabled_flag_prevents_send(monkeypatch):
    monkeypatch.setattr(settings, "local_parity_mode", True)
    monkeypatch.setattr(settings, "planam_env", "local-parity")
    monkeypatch.setattr(settings, "telegram_bot_token", "token")
    post = AsyncMock()
    client = MagicMock()
    client.__aenter__.return_value.post = post
    monkeypatch.setattr("httpx.AsyncClient", lambda *args, **kwargs: client)

    sent = asyncio.run(messages.send_telegram_message(123, "hello"))

    assert sent is False
    post.assert_not_called()


def test_scheduler_disabled_flag_prevents_scheduler_start(monkeypatch):
    monkeypatch.setattr(settings, "local_parity_mode", True)
    monkeypatch.setattr(settings, "planam_env", "local-parity")
    monkeypatch.setattr(settings, "notification_scheduler_enabled", False)

    asyncio.run(notification_scheduler.run_notification_scheduler())
