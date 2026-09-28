from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from fastapi import Header
from sqlalchemy.orm import Session

from app.core.models import CoreAccount, CoreMembership, CorePerson, CorePermissionGrant, CoreSession
from app.v2.errors import error
from app.v2.identity import resolve_or_create_audit_session, resolve_session


@dataclass(frozen=True)
class AuthorizedContext:
    account: CoreAccount
    session: CoreSession
    person: CorePerson | None
    household_id: str | None
    actor_person: CorePerson | None = None

    @property
    def target_person(self) -> CorePerson | None:
        return self.person


def get_v2_access_token(authorization: str | None, x_planam_session: str | None) -> str:
    if authorization:
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() == "bearer" and token:
            return token
    if x_planam_session:
        return x_planam_session
    raise error("authentication_required", 401)


def authorized_context(
    db: Session,
    *,
    authorization: str | None = None,
    x_planam_session: str | None = None,
    x_household_id: str | None = None,
    x_person_id: str | None = None,
    required_capability: str | None = None,
    x_telegram_init_data: str | None = None,
) -> AuthorizedContext:
    if authorization or x_planam_session:
        token = get_v2_access_token(authorization, x_planam_session)
        session = resolve_session(db, token)
    elif x_telegram_init_data:
        session = resolve_or_create_audit_session(db, x_telegram_init_data)
    else:
        raise error("authentication_required", 401)
    account = db.get(CoreAccount, session.account_id)
    if account is None or account.status != "active":
        raise error("forbidden", 403)
    actor_person = db.get(CorePerson, account.primary_person_id) if account.primary_person_id else None
    person = db.get(CorePerson, x_person_id or account.primary_person_id) if (x_person_id or account.primary_person_id) else None
    if x_person_id and person is None:
        raise error("forbidden", 403)
    if person is not None and person.person_id != account.primary_person_id:
        if actor_person is None or not _has_permission(
            db,
            actor_person.person_id,
            person.person_id,
            x_household_id,
            required_capability or "core.person.read",
        ):
            raise error("forbidden", 403)
    household_id = x_household_id
    if household_id or x_person_id:
        query = db.query(CoreMembership).filter(
            CoreMembership.membership_status == "active",
            CoreMembership.household_id == household_id if household_id else True,
            CoreMembership.person_id == person.person_id if person is not None else actor_person.person_id if actor_person else True,
        )
        membership = query.order_by(CoreMembership.active_from.desc()).first()
        if membership is None:
            raise error("forbidden", 403)
        household_id = membership.household_id
    return AuthorizedContext(account=account, session=session, person=person, household_id=household_id, actor_person=actor_person)


def _has_permission(
    db: Session,
    subject_person_id: str,
    target_person_id: str,
    household_id: str | None,
    capability: str,
) -> bool:
    now = datetime.now(timezone.utc)
    query = db.query(CorePermissionGrant).filter(
        CorePermissionGrant.subject_person_id == subject_person_id,
        CorePermissionGrant.target_person_id == target_person_id,
        CorePermissionGrant.capability == capability,
        CorePermissionGrant.grant_status == "active",
        CorePermissionGrant.effective_from <= now,
        (CorePermissionGrant.effective_to.is_(None) | (CorePermissionGrant.effective_to > now)),
    )
    if household_id:
        query = query.filter(
            (CorePermissionGrant.household_id == household_id) | CorePermissionGrant.household_id.is_(None)
        )
    return query.first() is not None


def session_context_dependency(
    db: Session,
    authorization: str | None = None,
    x_planam_session: str | None = None,
    x_household_id: str | None = None,
    x_person_id: str | None = None,
    required_capability: str | None = None,
) -> AuthorizedContext:
    return authorized_context(
        db,
        authorization=authorization,
        x_planam_session=x_planam_session,
        x_household_id=x_household_id,
        x_person_id=x_person_id,
        required_capability=required_capability,
    )
