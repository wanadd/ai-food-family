from __future__ import annotations

from datetime import timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.models import (
    CoreAccount,
    CoreHousehold,
    CoreMembership,
    CorePerson,
    CoreSession,
    ExternalIdentity,
)
from app.database import Base
from app.platform.adapters import PlatformCapability, TelegramPlatformAdapter, WebPlatformAdapter
from app.platform.navigation import resolve_navigation_intent
from app.v2.authorization import authorized_context
from app.v2.errors import V2Error
from app.v2.identity import (
    AuthResult,
    complete_link_intent,
    create_link_intent,
    issue_session,
    resolve_session,
    utc_now,
)
from app.v2.uuid7 import is_uuid7, uuid7_str


@pytest.fixture()
def db() -> Session:
    engine = create_engine("sqlite:///:memory:")
    foundation_tables = [
        Base.metadata.tables[name]
        for name in (
            "core_persons",
            "core_accounts",
            "core_households",
            "core_memberships",
            "core_person_relationships",
            "core_permission_grants",
            "external_identities",
            "verified_contacts",
            "sessions",
            "identity_link_intents",
        )
    ]
    Base.metadata.create_all(engine, tables=foundation_tables)
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


def _account(db: Session, *, name: str = "person") -> tuple[CoreAccount, CorePerson]:
    person = CorePerson(person_id=uuid7_str(), display_name=name, birth_date_precision="unknown")
    db.add(person)
    db.flush()
    account = CoreAccount(account_id=uuid7_str(), primary_person_id=person.person_id)
    db.add(account)
    db.flush()
    return account, person


def test_wave_0_ids_are_uuid7_and_person_is_independent(db: Session):
    person = CorePerson(person_id=uuid7_str(), birth_date_precision="unknown")
    db.add(person)
    db.commit()

    assert is_uuid7(person.person_id)
    assert db.query(CoreAccount).count() == 0


def test_external_identity_provider_subject_is_unique(db: Session):
    account_a, person_a = _account(db, name="A")
    account_b, _ = _account(db, name="B")
    db.add_all(
        [
            ExternalIdentity(identity_id=uuid7_str(), account_id=account_a.account_id, provider="telegram", provider_subject="42"),
            ExternalIdentity(identity_id=uuid7_str(), account_id=account_b.account_id, provider="telegram", provider_subject="42"),
        ]
    )
    with pytest.raises(IntegrityError):
        db.commit()
    assert person_a.person_id != account_a.account_id


def test_session_expiry_and_revocation_are_server_side(db: Session):
    account, _ = _account(db)
    issued = issue_session(db, account.account_id, client_type="telegram")
    db.commit()
    assert resolve_session(db, issued.access_token).account_id == account.account_id

    session = db.get(CoreSession, issued.session.session_id)
    assert session is not None
    session.revoked_at = utc_now()
    db.commit()
    with pytest.raises(V2Error) as exc:
        resolve_session(db, issued.access_token)
    assert exc.value.code == "invalid_session"


def test_link_intent_is_one_time_and_conflicts_are_not_merged(db: Session):
    account_a, _ = _account(db, name="A")
    account_b, _ = _account(db, name="B")
    intent, secret = create_link_intent(db, account_a.account_id, "telegram")
    db.add(ExternalIdentity(identity_id=uuid7_str(), account_id=account_b.account_id, provider="telegram", provider_subject="99"))
    db.commit()

    with pytest.raises(V2Error) as conflict:
        complete_link_intent(
            db,
            intent.intent_id,
            secret,
            AuthResult("telegram", "99", "hash", {}),
        )
    assert conflict.value.code == "identity_conflict"
    db.rollback()

    intent, secret = create_link_intent(db, account_a.account_id, "telegram")
    identity = complete_link_intent(db, intent.intent_id, secret, AuthResult("telegram", "100", "hash", {}))
    db.commit()
    assert identity.account_id == account_a.account_id
    with pytest.raises(V2Error) as replay:
        complete_link_intent(db, intent.intent_id, secret, AuthResult("telegram", "100", "hash", {}))
    assert replay.value.code == "link_replayed"


def test_authorized_context_denies_cross_household_person(db: Session):
    account_a, person_a = _account(db, name="A")
    _, person_b = _account(db, name="B")
    household_a = CoreHousehold(household_id=uuid7_str(), name="A")
    household_b = CoreHousehold(household_id=uuid7_str(), name="B")
    db.add_all([household_a, household_b])
    db.flush()
    db.add_all(
        [
            CoreMembership(membership_id=uuid7_str(), person_id=person_a.person_id, household_id=household_a.household_id),
            CoreMembership(membership_id=uuid7_str(), person_id=person_b.person_id, household_id=household_b.household_id),
        ]
    )
    issued = issue_session(db, account_a.account_id, client_type="web")
    db.commit()

    with pytest.raises(V2Error) as denied:
        authorized_context(
            db,
            authorization=f"Bearer {issued.access_token}",
            x_household_id=household_b.household_id,
            x_person_id=person_b.person_id,
        )
    assert denied.value.code == "forbidden"
    assert db.query(CoreMembership).count() == 2


def test_platform_adapters_are_capability_scoped():
    assert TelegramPlatformAdapter().capabilities().supports(PlatformCapability.AUTH_BOOTSTRAP)
    assert not WebPlatformAdapter().capabilities().supports(PlatformCapability.AUTH_BOOTSTRAP)


def test_navigation_is_provider_neutral():
    assert resolve_navigation_intent("recipes/abc").kind == "recipe"
    assert resolve_navigation_intent("account-link/intent").kind == "account_link"
