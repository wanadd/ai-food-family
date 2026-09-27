from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.models import CoreHousehold, CoreMembership, CorePerson, CorePermissionGrant
from app.v2.errors import error
from app.v2.uuid7 import uuid7_str


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class HouseholdView:
    household: CoreHousehold
    membership: CoreMembership


def list_authorized_households(db: Session, person_id: str) -> list[HouseholdView]:
    rows = db.execute(
        select(CoreHousehold, CoreMembership)
        .join(CoreMembership, CoreMembership.household_id == CoreHousehold.household_id)
        .where(
            CoreMembership.person_id == person_id,
            CoreMembership.membership_status == "active",
            CoreHousehold.status == "active",
        )
        .order_by(CoreHousehold.created_at, CoreHousehold.household_id)
    ).all()
    return [HouseholdView(household, membership) for household, membership in rows]


def create_household(
    db: Session,
    *,
    account_id: str,
    person_id: str,
    name: str | None,
    idempotency_key: str,
) -> HouseholdView:
    existing = db.scalar(select(CoreHousehold).where(CoreHousehold.creation_idempotency_key == idempotency_key))
    if existing is not None:
        membership = db.scalar(
            select(CoreMembership).where(
                CoreMembership.household_id == existing.household_id,
                CoreMembership.person_id == person_id,
                CoreMembership.membership_status == "active",
            )
        )
        if membership is None:
            raise error("conflict", 409)
        return HouseholdView(existing, membership)
    household = CoreHousehold(
        household_id=uuid7_str(),
        name=name.strip() if name else None,
        status="active",
        created_by_account_id=account_id,
        creation_idempotency_key=idempotency_key,
    )
    db.add(household)
    db.flush()
    membership = CoreMembership(
        membership_id=uuid7_str(),
        person_id=person_id,
        household_id=household.household_id,
        membership_status="active",
        role_label="owner",
        created_by_account_id=account_id,
        idempotency_key=f"{idempotency_key}:owner",
        provenance_json={"source": "v2_household_create"},
    )
    db.add(membership)
    db.flush()
    return HouseholdView(household, membership)


def list_members(db: Session, household_id: str) -> list[tuple[CorePerson, CoreMembership]]:
    return list(
        db.execute(
            select(CorePerson, CoreMembership)
            .join(CoreMembership, CoreMembership.person_id == CorePerson.person_id)
            .where(
                CoreMembership.household_id == household_id,
                CoreMembership.membership_status == "active",
            )
            .order_by(CoreMembership.active_from, CoreMembership.membership_id)
        ).all()
    )


def add_member(
    db: Session,
    *,
    household_id: str,
    actor_person_id: str,
    person_id: str | None,
    display_name: str | None,
    role_label: str | None,
    idempotency_key: str,
    created_by_account_id: str | None = None,
) -> tuple[CorePerson, CoreMembership]:
    actor = db.scalar(
        select(CoreMembership).where(
            CoreMembership.household_id == household_id,
            CoreMembership.person_id == actor_person_id,
            CoreMembership.membership_status == "active",
        )
    )
    if actor is None or actor.role_label not in {"owner", "admin"}:
        raise error("forbidden", 403)
    existing_command = db.scalar(select(CoreMembership).where(CoreMembership.idempotency_key == idempotency_key))
    if existing_command is not None:
        person = db.get(CorePerson, existing_command.person_id)
        if person is None:
            raise error("conflict", 409)
        return person, existing_command
    person = db.get(CorePerson, person_id) if person_id else None
    if person is None:
        person = CorePerson(person_id=uuid7_str(), display_name=display_name, birth_date_precision="unknown", status="active")
        db.add(person)
        db.flush()
    active = db.scalar(
        select(CoreMembership).where(
            CoreMembership.household_id == household_id,
            CoreMembership.person_id == person.person_id,
            CoreMembership.membership_status == "active",
        )
    )
    if active is not None:
        raise error("conflict", 409)
    membership = CoreMembership(
        membership_id=uuid7_str(),
        person_id=person.person_id,
        household_id=household_id,
        membership_status="active",
        role_label=role_label or "member",
        created_by_account_id=created_by_account_id,
        idempotency_key=idempotency_key,
        provenance_json={"source": "v2_household_member_add", "actor_person_id": actor_person_id},
    )
    db.add(membership)
    db.flush()
    return person, membership
