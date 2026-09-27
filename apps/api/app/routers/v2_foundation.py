from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Header, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.models import CoreSession
from app.database import get_db
from app.v2.authorization import AuthorizedContext, authorized_context
from app.v2.entitlements import list_effective_entitlements
from app.v2.households import add_member, create_household, list_authorized_households, list_members
from app.v2.identity import (
    complete_link_intent,
    create_link_intent,
    issue_session,
    resolve_or_create_account,
    resolve_session_by_refresh,
    rotate_session,
    unlink_identity,
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


class HouseholdCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=160)


class MemberAddRequest(BaseModel):
    person_id: str | None = None
    display_name: str | None = Field(default=None, max_length=160)
    role_label: str | None = Field(default=None, max_length=64)


class PersonPatchRequest(BaseModel):
    display_name: str | None = Field(default=None, max_length=160)
    birth_date: date | None = None
    birth_date_precision: str | None = Field(default=None, max_length=24)


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


def _headers_context(
    db: Session,
    *,
    authorization: str | None,
    x_planam_session: str | None,
    household_id: str | None = None,
    person_id: str | None = None,
    required_capability: str | None = None,
) -> AuthorizedContext:
    return authorized_context(
        db,
        authorization=authorization,
        x_planam_session=x_planam_session,
        x_household_id=household_id,
        x_person_id=person_id,
        required_capability=required_capability,
    )


def _require_key(value: str | None):
    if not value:
        from app.v2.errors import error

        raise error("validation_error", 422, details={"header": "Idempotency-Key is required"})
    return value


@router.get("/households")
def households(
    db: Session = Depends(get_db),
    authorization: str | None = Header(default=None),
    x_planam_session: str | None = Header(default=None, alias="X-Planam-Session"),
) -> list[dict]:
    context = _headers_context(db, authorization=authorization, x_planam_session=x_planam_session)
    if context.actor_person is None:
        return []
    return [
        {"household_id": item.household.household_id, "name": item.household.name, "status": item.household.status, "role": item.membership.role_label}
        for item in list_authorized_households(db, context.actor_person.person_id)
    ]


@router.post("/households")
def household_create(
    payload: HouseholdCreateRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    db: Session = Depends(get_db),
    authorization: str | None = Header(default=None),
    x_planam_session: str | None = Header(default=None, alias="X-Planam-Session"),
) -> dict:
    key = _require_key(idempotency_key)
    context = _headers_context(db, authorization=authorization, x_planam_session=x_planam_session)
    if context.actor_person is None:
        from app.v2.errors import error

        raise error("forbidden", 403)
    result = create_household(
        db,
        account_id=context.account.account_id,
        person_id=context.actor_person.person_id,
        name=payload.name,
        idempotency_key=key,
    )
    db.commit()
    return {"household_id": result.household.household_id, "name": result.household.name, "role": result.membership.role_label}


@router.get("/households/{household_id}/members")
def household_members(
    household_id: str,
    db: Session = Depends(get_db),
    authorization: str | None = Header(default=None),
    x_planam_session: str | None = Header(default=None, alias="X-Planam-Session"),
) -> list[dict]:
    _headers_context(db, authorization=authorization, x_planam_session=x_planam_session, household_id=household_id)
    return [
        {"person_id": person.person_id, "display_name": person.display_name, "birth_date_precision": person.birth_date_precision, "membership_id": membership.membership_id, "role": membership.role_label}
        for person, membership in list_members(db, household_id)
    ]


@router.post("/households/{household_id}/members")
def household_member_add(
    household_id: str,
    payload: MemberAddRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    db: Session = Depends(get_db),
    authorization: str | None = Header(default=None),
    x_planam_session: str | None = Header(default=None, alias="X-Planam-Session"),
) -> dict:
    key = _require_key(idempotency_key)
    context = _headers_context(db, authorization=authorization, x_planam_session=x_planam_session, household_id=household_id)
    if context.actor_person is None:
        from app.v2.errors import error

        raise error("forbidden", 403)
    person, membership = add_member(
        db,
        household_id=household_id,
        actor_person_id=context.actor_person.person_id,
        person_id=payload.person_id,
        display_name=payload.display_name,
        role_label=payload.role_label,
        idempotency_key=key,
        created_by_account_id=context.account.account_id,
    )
    db.commit()
    return {"person_id": person.person_id, "membership_id": membership.membership_id, "role": membership.role_label}


@router.patch("/people/{person_id}")
def person_patch(
    person_id: str,
    payload: PersonPatchRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    x_household_id: str | None = Header(default=None, alias="X-Planam-Household-Id"),
    db: Session = Depends(get_db),
    authorization: str | None = Header(default=None),
    x_planam_session: str | None = Header(default=None, alias="X-Planam-Session"),
) -> dict:
    key = _require_key(idempotency_key)
    context = _headers_context(
        db,
        authorization=authorization,
        x_planam_session=x_planam_session,
        household_id=x_household_id,
        person_id=person_id,
        required_capability="core.person.write",
    )
    person = context.person
    if person is None:
        from app.v2.errors import error

        raise error("not_found", 404)
    if person.last_mutation_idempotency_key == key:
        return {"person_id": person.person_id, "display_name": person.display_name, "birth_date_precision": person.birth_date_precision}
    if payload.birth_date_precision == "declared_age_only" and payload.birth_date is not None:
        from app.v2.errors import error

        raise error("validation_error", 422, details={"birth_date": "must_be_null_for_declared_age_only"})
    if payload.display_name is not None:
        person.display_name = payload.display_name
    if payload.birth_date_precision is not None:
        if payload.birth_date_precision not in {"unknown", "exact", "year_month", "year", "declared_age_only"}:
            from app.v2.errors import error

            raise error("validation_error", 422, details={"birth_date_precision": "unsupported"})
        person.birth_date_precision = payload.birth_date_precision
    if "birth_date" in payload.model_fields_set:
        person.birth_date = payload.birth_date
    person.last_mutation_idempotency_key = key
    db.commit()
    return {"person_id": person.person_id, "display_name": person.display_name, "birth_date": person.birth_date, "birth_date_precision": person.birth_date_precision}


@router.delete("/account/identities/{identity_id}")
def identity_unlink(
    identity_id: str,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    db: Session = Depends(get_db),
    authorization: str | None = Header(default=None),
    x_planam_session: str | None = Header(default=None, alias="X-Planam-Session"),
) -> dict:
    _require_key(idempotency_key)
    context = _headers_context(db, authorization=authorization, x_planam_session=x_planam_session)
    identity = unlink_identity(db, account_id=context.account.account_id, identity_id=identity_id)
    db.commit()
    return {"identity_id": identity.identity_id, "status": identity.status}


@router.get("/entitlements")
def entitlements(
    db: Session = Depends(get_db),
    authorization: str | None = Header(default=None),
    x_planam_session: str | None = Header(default=None, alias="X-Planam-Session"),
    x_household_id: str | None = Header(default=None, alias="X-Planam-Household-Id"),
    x_person_id: str | None = Header(default=None, alias="X-Planam-Person-Id"),
) -> list[dict]:
    context = _headers_context(db, authorization=authorization, x_planam_session=x_planam_session, household_id=x_household_id, person_id=x_person_id)
    return [decision.__dict__ for decision in list_effective_entitlements(
        db,
        account_id=context.account.account_id,
        household_id=context.household_id,
        person_id=context.person.person_id if context.person else None,
    )]
