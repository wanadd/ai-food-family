from __future__ import annotations

from dataclasses import dataclass

from fastapi import Header
from sqlalchemy.orm import Session

from app.core.models import CoreAccount, CoreMembership, CorePerson, CoreSession
from app.v2.errors import error
from app.v2.identity import resolve_session


@dataclass(frozen=True)
class AuthorizedContext:
    account: CoreAccount
    session: CoreSession
    person: CorePerson | None
    household_id: str | None


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
) -> AuthorizedContext:
    token = get_v2_access_token(authorization, x_planam_session)
    session = resolve_session(db, token)
    account = db.get(CoreAccount, session.account_id)
    if account is None or account.status != "active":
        raise error("forbidden", 403)
    person = db.get(CorePerson, x_person_id or account.primary_person_id) if (x_person_id or account.primary_person_id) else None
    if x_person_id and person is None:
        raise error("forbidden", 403)
    if person is not None and person.person_id != account.primary_person_id:
        raise error("forbidden", 403)
    household_id = x_household_id
    if household_id or person is not None:
        query = db.query(CoreMembership).filter(
            CoreMembership.membership_status == "active",
            CoreMembership.household_id == household_id if household_id else True,
            CoreMembership.person_id == person.person_id if person is not None else True,
        )
        membership = query.order_by(CoreMembership.active_from.desc()).first()
        if membership is None:
            raise error("forbidden", 403)
        household_id = membership.household_id
    return AuthorizedContext(account=account, session=session, person=person, household_id=household_id)


def session_context_dependency(
    db: Session,
    authorization: str | None = None,
    x_planam_session: str | None = None,
    x_household_id: str | None = None,
    x_person_id: str | None = None,
) -> AuthorizedContext:
    return authorized_context(
        db,
        authorization=authorization,
        x_planam_session=x_planam_session,
        x_household_id=x_household_id,
        x_person_id=x_person_id,
    )
