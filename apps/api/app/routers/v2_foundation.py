from __future__ import annotations

from fastapi import APIRouter, Depends, Header, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.models import CoreSession
from app.database import get_db
from app.v2.authorization import AuthorizedContext, authorized_context
from app.v2.identity import (
    complete_link_intent,
    create_link_intent,
    issue_session,
    resolve_or_create_account,
    resolve_session_by_refresh,
    rotate_session,
    utc_now,
    verify_provider_bootstrap,
)

router = APIRouter(prefix="/api/v2", tags=["v2-foundation"])


class AuthBootstrapRequest(BaseModel):
    provider: str = Field(default="telegram", min_length=1, max_length=64)
    init_data: str = Field(min_length=1)
    client_type: str = Field(default="telegram", min_length=1, max_length=24)


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=16)


class LinkIntentRequest(BaseModel):
    provider: str = Field(default="telegram", min_length=1, max_length=64)


class LinkCompleteRequest(BaseModel):
    secret: str = Field(min_length=16)
    init_data: str = Field(min_length=1)


def _session_payload(issued) -> dict:
    session = issued.session
    return {
        "session_id": session.session_id,
        "account_id": session.account_id,
        "client_type": session.client_type,
        "access_token": issued.access_token,
        "refresh_token": issued.refresh_token,
        "expires_at": session.expires_at.isoformat(),
    }


def _context(
    db: Session = Depends(get_db),
    authorization: str | None = Header(default=None),
    x_planam_session: str | None = Header(default=None, alias="X-Planam-Session"),
    x_household_id: str | None = Header(default=None, alias="X-Planam-Household-Id"),
    x_person_id: str | None = Header(default=None, alias="X-Planam-Person-Id"),
) -> AuthorizedContext:
    return authorized_context(
        db,
        authorization=authorization,
        x_planam_session=x_planam_session,
        x_household_id=x_household_id,
        x_person_id=x_person_id,
    )


@router.post("/auth/bootstrap")
def auth_bootstrap(payload: AuthBootstrapRequest, db: Session = Depends(get_db)) -> dict:
    auth = verify_provider_bootstrap(payload.provider, payload.init_data)
    account, is_new = resolve_or_create_account(db, auth)
    issued = issue_session(
        db,
        account.account_id,
        client_type=payload.client_type,
        security_metadata={"provider": auth.provider},
    )
    db.commit()
    return {**_session_payload(issued), "is_new_account": is_new, "provider": auth.provider}


@router.get("/me")
def me(context: AuthorizedContext = Depends(_context)) -> dict:
    return {
        "account_id": context.account.account_id,
        "person_id": context.person.person_id if context.person else None,
        "household_id": context.household_id,
        "session_id": context.session.session_id,
        "client_type": context.session.client_type,
    }


@router.get("/session")
def current_session(context: AuthorizedContext = Depends(_context)) -> dict:
    return {
        "session_id": context.session.session_id,
        "account_id": context.account.account_id,
        "client_type": context.session.client_type,
        "expires_at": context.session.expires_at.isoformat(),
        "last_activity_at": context.session.last_activity_at.isoformat(),
    }


@router.post("/session/refresh")
def refresh_session(payload: RefreshRequest, db: Session = Depends(get_db)) -> dict:
    session = resolve_session_by_refresh(db, payload.refresh_token)
    issued = rotate_session(db, session, payload.refresh_token)
    db.commit()
    return _session_payload(issued)


@router.post("/session/revoke")
def revoke_session(context: AuthorizedContext = Depends(_context), db: Session = Depends(get_db)) -> dict:
    session = db.get(CoreSession, context.session.session_id)
    if session is not None:
        session.revoked_at = utc_now()
        session.refresh_token_hash = None
        db.commit()
    return {"revoked": True, "session_id": context.session.session_id}


@router.get("/account/identities")
def list_identities(context: AuthorizedContext = Depends(_context), db: Session = Depends(get_db)) -> list[dict]:
    from app.core.models import ExternalIdentity

    identities = db.query(ExternalIdentity).filter(ExternalIdentity.account_id == context.account.account_id).all()
    return [
        {
            "identity_id": identity.identity_id,
            "provider": identity.provider,
            "status": identity.status,
            "linked_at": identity.linked_at.isoformat() if identity.linked_at else None,
        }
        for identity in identities
    ]


@router.post("/account/link-intents")
def start_link_intent(payload: LinkIntentRequest, context: AuthorizedContext = Depends(_context), db: Session = Depends(get_db)) -> dict:
    intent, secret = create_link_intent(db, context.account.account_id, payload.provider)
    db.commit()
    return {"intent_id": intent.intent_id, "provider": intent.provider, "secret": secret, "expires_at": intent.expires_at.isoformat()}


@router.post("/account/link-intents/{intent_id}/complete")
def finish_link_intent(
    intent_id: str,
    payload: LinkCompleteRequest,
    context: AuthorizedContext = Depends(_context),
    db: Session = Depends(get_db),
) -> dict:
    from app.core.models import IdentityLinkIntent

    intent = db.get(IdentityLinkIntent, intent_id)
    if intent is None or intent.initiating_account_id != context.account.account_id:
        from app.v2.errors import error

        raise error("forbidden", 403)
    auth = verify_provider_bootstrap(intent.provider, payload.init_data)
    identity = complete_link_intent(db, intent_id, payload.secret, auth)
    db.commit()
    return {"status": "LINK_ALLOWED", "identity_id": identity.identity_id, "provider": identity.provider}
