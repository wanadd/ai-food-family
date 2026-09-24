from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.core.models import (
    CoreAccount,
    CoreAuthIdentity,
    CoreHousehold,
    CoreMembership,
    CorePerson,
    LegacyIdMapping,
)
from app.models.family import Family, FamilyMember, FamilyRole
from app.models.user import User
from app.v2.uuid7 import uuid7_str


@dataclass
class CoreMappingReport:
    legacy_users_scanned: int = 0
    accounts_created: int = 0
    accounts_reused: int = 0
    auth_identities_created: int = 0
    auth_identities_reused: int = 0
    persons_created: int = 0
    persons_reused: int = 0
    legacy_families_scanned: int = 0
    households_created: int = 0
    households_reused: int = 0
    family_members_scanned: int = 0
    memberships_created: int = 0
    memberships_reused: int = 0
    relationships_created: int = 0
    relationships_reused: int = 0
    permission_grants_created: int = 0
    permission_grants_reused: int = 0
    ambiguous_reconfirm_cases: int = 0
    skipped_cases: int = 0
    errors: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "legacy_users_scanned": self.legacy_users_scanned,
            "accounts_created": self.accounts_created,
            "accounts_reused": self.accounts_reused,
            "auth_identities_created": self.auth_identities_created,
            "auth_identities_reused": self.auth_identities_reused,
            "persons_created": self.persons_created,
            "persons_reused": self.persons_reused,
            "legacy_families_scanned": self.legacy_families_scanned,
            "households_created": self.households_created,
            "households_reused": self.households_reused,
            "family_members_scanned": self.family_members_scanned,
            "memberships_created": self.memberships_created,
            "memberships_reused": self.memberships_reused,
            "relationships_created": self.relationships_created,
            "relationships_reused": self.relationships_reused,
            "permission_grants_created": self.permission_grants_created,
            "permission_grants_reused": self.permission_grants_reused,
            "ambiguous_reconfirm_cases": self.ambiguous_reconfirm_cases,
            "skipped_cases": self.skipped_cases,
            "errors": list(self.errors),
        }


def map_legacy_core_identities(db: Session, *, dry_run: bool = False) -> CoreMappingReport:
    report = CoreMappingReport()
    bind = db.get_bind()
    if bind.dialect.name == "postgresql" and not dry_run:
        db.execute(text("SELECT pg_advisory_xact_lock(:lock_id)"), {"lock_id": 906_220_002})
    for user in db.scalars(select(User).order_by(User.id)).all():
        report.legacy_users_scanned += 1
        account = _account_for_user(db, user, report, dry_run=dry_run)
        person = _person_for_user(db, user, report, dry_run=dry_run)
        if account is not None and person is not None and account.primary_person_id is None and not dry_run:
            account.primary_person_id = person.person_id
        if account is not None:
            _auth_identity_for_user(db, user, account, report, dry_run=dry_run)

    for family in db.scalars(select(Family).order_by(Family.id)).all():
        report.legacy_families_scanned += 1
        _household_for_family(db, family, report, dry_run=dry_run)

    for member in db.scalars(select(FamilyMember).order_by(FamilyMember.id)).all():
        report.family_members_scanned += 1
        person = _person_for_member(db, member, report, dry_run=dry_run)
        household = _household_for_family_id(db, member.family_id)
        if person is None or household is None:
            report.skipped_cases += 1
            continue
        _membership_for_member(db, member, person, household, report, dry_run=dry_run)

    if not dry_run:
        db.commit()
    return report


def _mapping(db: Session, legacy_table: str, legacy_id: int, target_table: str) -> LegacyIdMapping | None:
    return db.scalar(
        select(LegacyIdMapping).where(
            LegacyIdMapping.legacy_table == legacy_table,
            LegacyIdMapping.legacy_id_text == str(legacy_id),
            LegacyIdMapping.target_table == target_table,
        )
    )


def _create_mapping(
    db: Session,
    legacy_table: str,
    legacy_id: int,
    target_table: str,
    target_id: str,
    provenance: dict[str, Any],
    *,
    dry_run: bool,
) -> None:
    if dry_run:
        return
    db.add(
        LegacyIdMapping(
            mapping_id=uuid7_str(),
            legacy_table=legacy_table,
            legacy_id_text=str(legacy_id),
            target_table=target_table,
            target_id_uuid=target_id,
            confidence="source_backed",
            migration_status="auto_migrated_with_provenance",
            provenance_json=provenance,
        )
    )


def _account_for_user(db: Session, user: User, report: CoreMappingReport, *, dry_run: bool) -> CoreAccount | None:
    existing = _mapping(db, "users", user.id, "core_accounts")
    if existing is not None:
        report.accounts_reused += 1
        return db.get(CoreAccount, existing.target_id_uuid)
    report.accounts_created += 1
    if dry_run:
        return None
    account = CoreAccount(
        account_id=uuid7_str(),
        status="deleted" if user.is_deleted else "disabled" if user.is_blocked else "active",
    )
    db.add(account)
    db.flush()
    _create_mapping(
        db,
        "users",
        user.id,
        "core_accounts",
        account.account_id,
        {"source": "users", "legacy_user_id": user.id},
        dry_run=dry_run,
    )
    return account


def _person_for_user(db: Session, user: User, report: CoreMappingReport, *, dry_run: bool) -> CorePerson | None:
    existing = _mapping(db, "users", user.id, "core_persons")
    if existing is not None:
        report.persons_reused += 1
        return db.get(CorePerson, existing.target_id_uuid)
    report.persons_created += 1
    if dry_run:
        return None
    display_name = " ".join(part for part in (user.first_name, user.last_name) if part) or user.username
    person = CorePerson(
        person_id=uuid7_str(),
        display_name=display_name,
        birth_date=None,
        birth_date_precision="unknown",
        birth_date_provenance_json={"migration_status": "not_available_from_users"},
        status="deleted" if user.is_deleted else "disabled" if user.is_blocked else "active",
    )
    db.add(person)
    db.flush()
    _create_mapping(
        db,
        "users",
        user.id,
        "core_persons",
        person.person_id,
        {"source": "users", "legacy_user_id": user.id, "dob_fabricated": False},
        dry_run=dry_run,
    )
    return person


def _auth_identity_for_user(
    db: Session,
    user: User,
    account: CoreAccount,
    report: CoreMappingReport,
    *,
    dry_run: bool,
) -> CoreAuthIdentity | None:
    provider_subject = str(user.telegram_id)
    existing = db.scalar(
        select(CoreAuthIdentity).where(
            CoreAuthIdentity.provider == "telegram",
            CoreAuthIdentity.provider_subject == provider_subject,
        )
    )
    if existing is not None:
        report.auth_identities_reused += 1
        return existing
    report.auth_identities_created += 1
    if dry_run:
        return None
    identity = CoreAuthIdentity(
        auth_identity_id=uuid7_str(),
        account_id=account.account_id,
        provider="telegram",
        provider_subject=provider_subject,
        provider_metadata_json={"legacy_user_id": user.id},
    )
    db.add(identity)
    return identity


def _household_for_family(db: Session, family: Family, report: CoreMappingReport, *, dry_run: bool) -> CoreHousehold | None:
    existing = _mapping(db, "families", family.id, "core_households")
    if existing is not None:
        report.households_reused += 1
        return db.get(CoreHousehold, existing.target_id_uuid)
    report.households_created += 1
    if dry_run:
        return None
    household = CoreHousehold(
        household_id=uuid7_str(),
        name=family.name,
        status="disabled" if family.is_blocked else "active",
    )
    db.add(household)
    db.flush()
    _create_mapping(
        db,
        "families",
        family.id,
        "core_households",
        household.household_id,
        {"source": "families", "legacy_family_id": family.id},
        dry_run=dry_run,
    )
    return household


def _household_for_family_id(db: Session, family_id: int) -> CoreHousehold | None:
    existing = _mapping(db, "families", family_id, "core_households")
    return db.get(CoreHousehold, existing.target_id_uuid) if existing is not None else None


def _person_for_member(db: Session, member: FamilyMember, report: CoreMappingReport, *, dry_run: bool) -> CorePerson | None:
    existing = _mapping(db, "family_members", member.id, "core_persons")
    if existing is not None:
        report.persons_reused += 1
        return db.get(CorePerson, existing.target_id_uuid)
    if member.user_id is not None:
        user_mapping = _mapping(db, "users", member.user_id, "core_persons")
        if user_mapping is not None:
            report.persons_reused += 1
            if not dry_run:
                _create_mapping(
                    db,
                    "family_members",
                    member.id,
                    "core_persons",
                    user_mapping.target_id_uuid,
                    {
                        "source": "family_members",
                        "legacy_family_member_id": member.id,
                        "equivalence": "linked_user_id",
                        "food_profile_migrated": False,
                    },
                    dry_run=dry_run,
                )
            return db.get(CorePerson, user_mapping.target_id_uuid)

    report.persons_created += 1
    if member.user_id is not None:
        report.ambiguous_reconfirm_cases += 1
    if dry_run:
        return None
    person = CorePerson(
        person_id=uuid7_str(),
        display_name=member.display_name,
        birth_date=None,
        birth_date_precision="unknown",
        birth_date_provenance_json={
            "migration_status": "legacy_age_not_canonical_dob",
            "dob_fabricated": False,
        },
        status="active",
    )
    db.add(person)
    db.flush()
    _create_mapping(
        db,
        "family_members",
        member.id,
        "core_persons",
        person.person_id,
        {
            "source": "family_members",
            "legacy_family_member_id": member.id,
            "food_profile_migrated": False,
            "dependent_without_account": member.user_id is None,
        },
        dry_run=dry_run,
    )
    return person


def _membership_for_member(
    db: Session,
    member: FamilyMember,
    person: CorePerson,
    household: CoreHousehold,
    report: CoreMappingReport,
    *,
    dry_run: bool,
) -> CoreMembership | None:
    existing = _mapping(db, "family_members", member.id, "core_memberships")
    if existing is not None:
        report.memberships_reused += 1
        return db.get(CoreMembership, existing.target_id_uuid)
    report.memberships_created += 1
    if dry_run:
        return None
    created_by_account_id = None
    if member.role == FamilyRole.ADMIN.value and member.user_id is not None:
        account_mapping = _mapping(db, "users", member.user_id, "core_accounts")
        created_by_account_id = account_mapping.target_id_uuid if account_mapping is not None else None
    membership = CoreMembership(
        membership_id=uuid7_str(),
        person_id=person.person_id,
        household_id=household.household_id,
        membership_status="active",
        role_label=member.role,
        created_by_account_id=created_by_account_id,
        provenance_json={
            "source": "family_members",
            "legacy_family_member_id": member.id,
            "permission_inferred": False,
            "relationship_inferred": False,
        },
    )
    db.add(membership)
    db.flush()
    _create_mapping(
        db,
        "family_members",
        member.id,
        "core_memberships",
        membership.membership_id,
        {"source": "family_members", "legacy_family_member_id": member.id},
        dry_run=dry_run,
    )
    return membership
