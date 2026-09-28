from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.config import settings
from app.core.models import CoreAccount, CorePerson, CoreSession, ExternalIdentity, IdentityLinkIntent
from app.telegram.validate import TelegramAuthError, validate_init_data
from app.v2.errors import error
from app.v2.uuid7 import uuid7_str

SESSION_TTL = timedelta(hours=12)
LINK_INTENT_TTL = timedelta(minutes=10)


@dataclass(frozen=True)
class AuthResult:
    provider: str
    provider_subject: str
    provider_payload_hash: str | None
    provider_metadata: dict[str, str]


@dataclass(frozen=True)
class IssuedSession:
    session: CoreSession
    access_token: str
    refresh_token: str


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _aware(value: datetime) -> datetime:
    return value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)


def digest_secret(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def verify_telegram_init_data(init_data: str) -> AuthResult:
    try:
        telegram_user = validate_init_data(init_data, settings.telegram_bot_token)
    except TelegramAuthError as exc:
        raise error("authentication_required", 401) from exc
    metadata = {
        key: value
        for key, value in {
            "username": telegram_user.username or "",
            "language_code": telegram_user.language_code or "",
        }.items()
        if value
    }
    return AuthResult(
        provider="telegram",
        provider_subject=str(telegram_user.id),
        provider_payload_hash=digest_secret(init_data),
        provider_metadata=metadata,
    )


def verify_provider_bootstrap(provider: str, init_data: str) -> AuthResult:
    if provider != "telegram":
        raise error("validation_error", 422, details={"provider": "unsupported_in_wave_0"})
    return verify_telegram_init_data(init_data)


def resolve_or_create_account(db: Session, auth: AuthResult) -> tuple[CoreAccount, bool]:
    identity = (
        db.query(ExternalIdentity)
        .filter(
            ExternalIdentity.provider == auth.provider,
            ExternalIdentity.provider_subject == auth.provider_subject,
        )
        .one_or_none()
    )
    if identity is not None:
        if identity.status == "revoked":
            identity.status = "active"
            identity.revoked_at = None
        account = db.get(CoreAccount, identity.account_id)
        if account is None or account.status != "active":
            raise error("forbidden", 403)
        identity.provider_payload_hash = auth.provider_payload_hash
        identity.provider_metadata_json = auth.provider_metadata
        return account, False

    person = CorePerson(person_id=uuid7_str(), status="active", birth_date_precision="unknown")
    db.add(person)
    db.flush()
    account = CoreAccount(account_id=uuid7_str(), primary_person_id=person.person_id, status="active")
    db.add(account)
    db.flush()
    db.add(
        ExternalIdentity(
            identity_id=uuid7_str(),
            account_id=account.account_id,
            provider=auth.provider,
            provider_subject=auth.provider_subject,
            provider_payload_hash=auth.provider_payload_hash,
            provider_metadata_json=auth.provider_metadata,
        )
    )
    db.flush()
    return account, True


def issue_session(
    db: Session,
    account_id: str,
    *,
    client_type: str,
    security_metadata: dict[str, str] | None = None,
) -> IssuedSession:
    now = utc_now()
    access_token = secrets.token_urlsafe(32)
    refresh_token = secrets.token_urlsafe(32)
    session = CoreSession(
        session_id=uuid7_str(),
        account_id=account_id,
        client_type=client_type,
        token_hash=digest_secret(access_token),
        refresh_token_hash=digest_secret(refresh_token),
        issued_at=now,
        expires_at=now + SESSION_TTL,
        last_activity_at=now,
        security_metadata_json=security_metadata or {},
    )
    db.add(session)
    db.flush()
    return IssuedSession(session, access_token, refresh_token)


def resolve_or_create_audit_session(db: Session, init_data: str) -> CoreSession:
    """Resolve a deterministic local-only V2 session for browser audit fixtures."""
    from app.services.audit_auth import (
        get_or_create_audit_user,
        is_audit_init_data,
        is_audit_mode_enabled,
        persona_from_audit_init_data,
    )

    if not is_audit_mode_enabled() or not is_audit_init_data(init_data):
        raise error("authentication_required", 401)
    persona = persona_from_audit_init_data(init_data)
    if persona is None:
        raise error("authentication_required", 401)

    user, _ = get_or_create_audit_user(db, persona)
    provider_subject = str(user.telegram_id)
    identity = (
        db.query(ExternalIdentity)
        .filter(
            ExternalIdentity.provider == "telegram",
            ExternalIdentity.provider_subject == provider_subject,
        )
        .one_or_none()
    )
    if identity is None:
        person = CorePerson(person_id=uuid7_str(), status="active", birth_date_precision="unknown")
        db.add(person)
        db.flush()
        account = CoreAccount(account_id=uuid7_str(), primary_person_id=person.person_id, status="active")
        db.add(account)
        db.flush()
        identity = ExternalIdentity(
            identity_id=uuid7_str(),
            account_id=account.account_id,
            provider="telegram",
            provider_subject=provider_subject,
            provider_payload_hash=digest_secret(init_data),
            provider_metadata_json={"audit_persona": persona},
        )
        db.add(identity)
        db.flush()
    session = (
        db.query(CoreSession)
        .filter(CoreSession.token_hash == digest_secret(init_data))
        .one_or_none()
    )
    if session is None:
        now = utc_now()
        session = CoreSession(
            session_id=uuid7_str(),
            account_id=identity.account_id,
            client_type="audit",
            token_hash=digest_secret(init_data),
            issued_at=now,
            expires_at=now + SESSION_TTL,
            last_activity_at=now,
            security_metadata_json={"audit_persona": persona},
        )
        db.add(session)
        db.commit()
        db.refresh(session)
    return session


def resolve_session(db: Session, access_token: str) -> CoreSession:
    session = db.query(CoreSession).filter(CoreSession.token_hash == digest_secret(access_token)).one_or_none()
    now = utc_now()
    if session is None or session.revoked_at is not None or _aware(session.expires_at) <= now:
        raise error("invalid_session", 401)
    return session


def resolve_session_by_refresh(db: Session, refresh_token: str) -> CoreSession:
    session = db.query(CoreSession).filter(CoreSession.refresh_token_hash == digest_secret(refresh_token)).one_or_none()
    now = utc_now()
    if session is None or session.revoked_at is not None or _aware(session.expires_at) <= now:
        raise error("invalid_session", 401)
    return session


def rotate_session(db: Session, session: CoreSession, refresh_token: str) -> IssuedSession:
    if session.refresh_token_hash != digest_secret(refresh_token):
        raise error("invalid_session", 401)
    now = utc_now()
    access_token = secrets.token_urlsafe(32)
    next_refresh = secrets.token_urlsafe(32)
    session.token_hash = digest_secret(access_token)
    session.refresh_token_hash = digest_secret(next_refresh)
    session.issued_at = now
    session.expires_at = now + SESSION_TTL
    session.last_activity_at = now
    session.rotation_counter += 1
    db.flush()
    return IssuedSession(session, access_token, next_refresh)


def create_link_intent(db: Session, account_id: str, provider: str) -> tuple[IdentityLinkIntent, str]:
    if provider != "telegram":
        raise error("validation_error", 422, details={"provider": "unsupported_in_wave_0"})
    secret = secrets.token_urlsafe(32)
    intent = IdentityLinkIntent(
        intent_id=uuid7_str(),
        initiating_account_id=account_id,
        provider=provider,
        secret_hash=digest_secret(secret),
        status="pending",
        created_at=utc_now(),
        expires_at=utc_now() + LINK_INTENT_TTL,
    )
    db.add(intent)
    db.flush()
    return intent, secret


def complete_link_intent(db: Session, intent_id: str, secret: str, auth: AuthResult) -> ExternalIdentity:
    intent = db.get(IdentityLinkIntent, intent_id)
    now = utc_now()
    if intent is None or intent.secret_hash != digest_secret(secret):
        raise error("link_replayed", 409)
    if intent.status != "pending":
        raise error("link_replayed", 409)
    if _aware(intent.expires_at) <= now:
        intent.status = "expired"
        db.flush()
        raise error("link_expired", 409)
    if intent.provider != auth.provider:
        raise error("validation_error", 422)
    existing = (
        db.query(ExternalIdentity)
        .filter(
            ExternalIdentity.provider == auth.provider,
            ExternalIdentity.provider_subject == auth.provider_subject,
        )
        .one_or_none()
    )
    if existing is not None and existing.account_id != intent.initiating_account_id and existing.status == "active":
        raise error("identity_conflict", 409)
    if existing is None:
        existing = ExternalIdentity(
            identity_id=uuid7_str(),
            account_id=intent.initiating_account_id,
            provider=auth.provider,
            provider_subject=auth.provider_subject,
            provider_payload_hash=auth.provider_payload_hash,
            provider_metadata_json=auth.provider_metadata,
        )
        db.add(existing)
    else:
        existing.status = "active"
        existing.revoked_at = None
    intent.status = "consumed"
    intent.consumed_at = now
    db.flush()
    return existing


def unlink_identity(db: Session, *, account_id: str, identity_id: str) -> ExternalIdentity:
    identity = db.get(ExternalIdentity, identity_id)
    if identity is None or identity.account_id != account_id:
        raise error("not_found", 404)
    if identity.status != "active":
        raise error("conflict", 409)
    active_count = db.query(ExternalIdentity).filter(
        ExternalIdentity.account_id == account_id,
        ExternalIdentity.status == "active",
    ).count()
    if active_count <= 1:
        raise error("last_identity", 409)
    identity.status = "revoked"
    identity.revoked_at = utc_now()
    db.flush()
    return identity
