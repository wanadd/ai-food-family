from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.models import (
    CoreAccount,
    CoreHousehold,
    CoreMembership,
    CorePermissionGrant,
    CorePerson,
    EntitlementConsumption,
    EntitlementGrant,
    EntitlementPlan,
)
from app.database import Base
from app.v2.authorization import authorized_context
from app.v2.entitlements import consume_entitlement, effective_entitlement
from app.v2.errors import V2Error
from app.v2.households import add_member, create_household, list_authorized_households
from app.v2.identity import issue_session
from app.v2.uuid7 import uuid7_str
from app.routers.v2_foundation import router


@pytest.fixture()
def db() -> Session:
    engine = create_engine("sqlite:///:memory:")
    names = (
        "core_persons", "core_accounts", "core_households", "core_memberships",
        "core_person_relationships", "core_permission_grants", "sessions",
        "external_identities", "verified_contacts", "identity_link_intents",
        "entitlement_plans", "entitlement_grants", "entitlement_consumptions",
    )
    Base.metadata.create_all(engine, tables=[Base.metadata.tables[name] for name in names])
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


def account(db: Session, name: str = "Owner") -> tuple[CoreAccount, CorePerson]:
    person = CorePerson(person_id=uuid7_str(), display_name=name, birth_date_precision="unknown")
    db.add(person)
    db.flush()
    owner = CoreAccount(account_id=uuid7_str(), primary_person_id=person.person_id)
    db.add(owner)
    db.flush()
    return owner, person


def test_personal_mode_does_not_require_household(db: Session):
    owner, person = account(db)
    issued = issue_session(db, owner.account_id, client_type="web")
    db.commit()

    context = authorized_context(db, authorization=f"Bearer {issued.access_token}")

    assert context.person.person_id == person.person_id
    assert context.household_id is None


def test_household_creation_is_idempotent_and_supports_multiple_households(db: Session):
    owner, person = account(db)
    first = create_household(db, account_id=owner.account_id, person_id=person.person_id, name="One", idempotency_key="create-1")
    replay = create_household(db, account_id=owner.account_id, person_id=person.person_id, name="Changed", idempotency_key="create-1")
    second = create_household(db, account_id=owner.account_id, person_id=person.person_id, name="Two", idempotency_key="create-2")
    db.commit()

    assert replay.household.household_id == first.household.household_id
    assert replay.household.name == "One"
    assert {item.household.name for item in list_authorized_households(db, person.person_id)} == {"One", "Two"}
    assert second.membership.role_label == "owner"


def test_dependent_requires_explicit_permission_and_stays_household_scoped(db: Session):
    owner, owner_person = account(db)
    household = create_household(db, account_id=owner.account_id, person_id=owner_person.person_id, name="Home", idempotency_key="home")
    dependent = CorePerson(person_id=uuid7_str(), display_name="Dependent", birth_date_precision="unknown")
    db.add(dependent)
    db.flush()
    db.add(CoreMembership(
        membership_id=uuid7_str(), person_id=dependent.person_id, household_id=household.household.household_id,
        membership_status="active", role_label="member",
    ))
    issued = issue_session(db, owner.account_id, client_type="web")
    db.commit()

    with pytest.raises(V2Error) as denied:
        authorized_context(
            db, authorization=f"Bearer {issued.access_token}",
            x_household_id=household.household.household_id, x_person_id=dependent.person_id,
        )
    assert denied.value.code == "forbidden"

    db.add(CorePermissionGrant(
        permission_grant_id=uuid7_str(), subject_person_id=owner_person.person_id,
        target_person_id=dependent.person_id, household_id=household.household.household_id,
        domain_scope="core", capability="core.person.read", grant_status="active",
    ))
    db.commit()
    context = authorized_context(
        db, authorization=f"Bearer {issued.access_token}",
        x_household_id=household.household.household_id, x_person_id=dependent.person_id,
    )
    assert context.person.person_id == dependent.person_id


def test_entitlement_precedence_limit_and_consumption_idempotency(db: Session):
    owner, person = account(db)
    household = create_household(db, account_id=owner.account_id, person_id=person.person_id, name="Home", idempotency_key="home")
    db.add(EntitlementPlan(plan_id=uuid7_str(), plan_key="core", version=1, status="active", policy_json={"source": "test"}))
    db.add(EntitlementGrant(
        grant_id=uuid7_str(), account_id=owner.account_id, capability="household.read", limit_value=99,
        source="account", idempotency_key="grant-account", provenance_json={},
    ))
    person_grant = EntitlementGrant(
        grant_id=uuid7_str(), person_id=person.person_id, capability="household.read", limit_value=2,
        source="person", idempotency_key="grant-person", provenance_json={},
    )
    db.add(person_grant)
    db.commit()

    decision = effective_entitlement(
        db, account_id=owner.account_id, household_id=household.household.household_id,
        person_id=person.person_id, capability="household.read",
    )
    assert decision.limit == 2
    assert decision.remaining == 2

    first = consume_entitlement(
        db, account_id=owner.account_id, household_id=household.household.household_id,
        person_id=person.person_id, capability="household.read", amount=1, idempotency_key="use-1",
    )
    replay = consume_entitlement(
        db, account_id=owner.account_id, household_id=household.household.household_id,
        person_id=person.person_id, capability="household.read", amount=99, idempotency_key="use-1",
    )
    db.commit()
    assert replay.consumption_id == first.consumption_id
    assert db.query(EntitlementConsumption).count() == 1
    assert effective_entitlement(
        db, account_id=owner.account_id, household_id=household.household.household_id,
        person_id=person.person_id, capability="household.read",
    ).remaining == 1

    with pytest.raises(V2Error) as over_limit:
        consume_entitlement(
            db, account_id=owner.account_id, household_id=household.household.household_id,
            person_id=person.person_id, capability="household.read", amount=2, idempotency_key="use-2",
        )
    assert over_limit.value.code == "entitlement_required"


def test_entitlement_grant_accepts_one_subject_only(db: Session):
    owner, person = account(db)
    with pytest.raises(Exception):
        db.add(EntitlementGrant(
            grant_id=uuid7_str(), account_id=owner.account_id, person_id=person.person_id,
            capability="invalid", source="test", provenance_json={},
        ))
        db.commit()


def test_wave_1_exposes_exactly_the_frozen_seven_routes():
    paths = {
        route.path.removeprefix("/api")
        for route in router.routes
        if route.path.startswith("/api/v2")
    }
    assert {
        "/v2/households",
        "/v2/households/{household_id}/members",
        "/v2/people/{person_id}",
        "/v2/account/identities/{identity_id}",
        "/v2/entitlements",
    }.issubset(paths)
    assert sum(
        1
        for route in router.routes
        if route.path.startswith("/api/v2")
        and route.path.removeprefix("/api") in {
            "/v2/households",
            "/v2/households/{household_id}/members",
            "/v2/people/{person_id}",
            "/v2/account/identities/{identity_id}",
            "/v2/entitlements",
        }
    ) == 7
