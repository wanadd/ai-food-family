"""Safe local audit authentication — disabled in production."""

from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.legal.documents import LEGAL_DOCUMENTS_VERSION
from app.models.user import User
from app.services.users import upsert_user_from_bot

AUDIT_INIT_DATA_PREFIX = "planam-audit-v1:"

# Fixed telegram_id range for audit personas (never overlaps real users).
AUDIT_PERSONA_TELEGRAM_IDS: dict[str, int] = {
    "audit_new_user": 900_000_001,
    "audit_personal_day5": 900_000_002,
    "audit_family_admin": 900_000_003,
    "audit_family_adult": 900_000_004,
    "audit_family_child": 900_000_005,
    "audit_athlete": 900_000_006,
    "audit_strict_diet": 900_000_007,
    "audit_healthy_eating": 900_000_008,
    "audit_start_trial": 900_000_009,
    "audit_personal_plus": 900_000_010,
    "audit_pair": 900_000_011,
    "audit_family": 900_000_012,
    "audit_family_pro": 900_000_013,
}

AUDIT_PERSONA_DISPLAY: dict[str, str] = {
    "audit_new_user": "Audit New User",
    "audit_personal_day5": "Audit Personal Day5",
    "audit_family_admin": "Audit Family Admin",
    "audit_family_adult": "Audit Family Adult",
    "audit_family_child": "Audit Family Child",
    "audit_athlete": "Audit Athlete",
    "audit_strict_diet": "Audit Strict Diet",
    "audit_healthy_eating": "Audit Healthy Eating",
    "audit_start_trial": "Audit Start Trial",
    "audit_personal_plus": "Audit Personal Plus",
    "audit_pair": "Audit Pair",
    "audit_family": "Audit Family",
    "audit_family_pro": "Audit Family Pro",
}

AUDIT_PHONE = "+79009000000"


def is_audit_mode_enabled() -> bool:
    """Audit auth is never active in production."""
    if not settings.is_development:
        return False
    return bool(settings.planam_audit_mode)


def audit_init_data_for_persona(persona: str) -> str:
    _validate_persona_slug(persona)
    return f"{AUDIT_INIT_DATA_PREFIX}{persona}"


def is_audit_init_data(init_data: str | None) -> bool:
    return bool(init_data) and init_data.startswith(AUDIT_INIT_DATA_PREFIX)


def persona_from_audit_init_data(init_data: str) -> str | None:
    if not is_audit_init_data(init_data):
        return None
    slug = init_data[len(AUDIT_INIT_DATA_PREFIX) :].strip()
    return slug if slug in AUDIT_PERSONA_TELEGRAM_IDS else None


def _validate_persona_slug(persona: str) -> str:
    if persona not in AUDIT_PERSONA_TELEGRAM_IDS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Unknown audit persona: {persona}",
        )
    return persona


def verify_audit_secret(
    provided: str | None,
    *,
    persona: str | None = None,
    path: str | None = None,
    origin: str | None = None,
) -> None:
    import logging

    required = (settings.planam_audit_secret or "").strip()
    if not required:
        return
    if (provided or "").strip() != required:
        if is_audit_mode_enabled():
            logging.getLogger(__name__).warning(
                "audit_auth_secret_rejected persona=%s has_secret_header=%s "
                "expected_secret_present=%s path=%s origin=%s",
                persona or "?",
                bool((provided or "").strip()),
                bool(required),
                path or "?",
                origin or "?",
            )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid audit secret",
        )


def resolve_audit_persona(
    *,
    init_data: str | None,
    header_persona: str | None,
    header_user: str | None,
) -> str | None:
    """Resolve persona from init data or headers (headers must match init data if both)."""
    from_init = persona_from_audit_init_data(init_data) if init_data else None
    from_header = (header_persona or header_user or "").strip() or None
    if from_header and from_header not in AUDIT_PERSONA_TELEGRAM_IDS:
        return None
    if from_init and from_header and from_init != from_header:
        return None
    return from_init or from_header


def get_or_create_audit_user(db: Session, persona: str) -> tuple[User, bool]:
    _validate_persona_slug(persona)
    telegram_id = AUDIT_PERSONA_TELEGRAM_IDS[persona]
    display = AUDIT_PERSONA_DISPLAY.get(persona, persona)
    user, is_new = upsert_user_from_bot(
        db,
        telegram_id=telegram_id,
        username=persona,
        first_name=display,
        last_name="(audit)",
        language_code="ru",
        phone_number=AUDIT_PHONE,
    )
    _ensure_audit_user_ready(db, user)
    return user, is_new


def _ensure_audit_user_ready(db: Session, user: User) -> None:
    from datetime import datetime, timezone

    changed = False
    if not user.accepted_terms:
        user.accepted_terms = True
        user.accepted_privacy = True
        user.accepted_personal_data = True
        user.legal_documents_version = LEGAL_DOCUMENTS_VERSION
        user.legal_accepted_at = datetime.now(timezone.utc)
        changed = True
    if user.is_blocked or user.is_deleted:
        user.is_blocked = False
        user.is_deleted = False
        changed = True
    if changed:
        db.commit()
        db.refresh(user)


def get_audit_user_from_request(
    db: Session,
    *,
    init_data: str | None,
    header_persona: str | None,
    header_user: str | None,
    header_secret: str | None,
    path: str | None = None,
    origin: str | None = None,
) -> User | None:
    if not is_audit_mode_enabled():
        return None

    persona = resolve_audit_persona(
        init_data=init_data,
        header_persona=header_persona,
        header_user=header_user,
    )
    if not persona:
        if is_audit_init_data(init_data):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid audit persona in init data",
            )
        return None

    verify_audit_secret(header_secret, persona=persona, path=path, origin=origin)
    user, _ = get_or_create_audit_user(db, persona)
    return user
