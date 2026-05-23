"""Local development authentication (disabled in production)."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.config import settings
from app.models.user import User
from app.services.users import upsert_user_from_bot

# Must match apps/web/lib/dev-auth.ts
DEV_INIT_DATA = "planam-dev-local-v1"

DEV_TELEGRAM_ID = 999_999_999
DEV_FIRST_NAME = "Иван"
DEV_USERNAME = "dev_user"
DEV_PHONE = "+79009999999"


def dev_auth_enabled() -> bool:
    return settings.is_development


def is_dev_init_data(init_data: str | None) -> bool:
    return bool(init_data) and init_data == DEV_INIT_DATA


def get_or_create_dev_user(db: Session) -> tuple[User, bool]:
    user, is_new = upsert_user_from_bot(
        db,
        telegram_id=DEV_TELEGRAM_ID,
        username=DEV_USERNAME,
        first_name=DEV_FIRST_NAME,
        last_name=None,
        language_code="ru",
        phone_number=DEV_PHONE,
    )
    if not user.accepted_terms:
        from app.legal.documents import LEGAL_DOCUMENTS_VERSION
        from datetime import datetime, timezone

        user.accepted_terms = True
        user.accepted_privacy = True
        user.accepted_personal_data = True
        user.legal_documents_version = LEGAL_DOCUMENTS_VERSION
        user.legal_accepted_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(user)
    return user, is_new
