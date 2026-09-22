from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

API_ROOT = Path(__file__).resolve().parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app import database_migrations  # noqa: E402
from app.core.legacy_mapping import map_legacy_core_identities  # noqa: E402
from app.core.models import (  # noqa: E402
    CoreAccount,
    CoreAuthIdentity,
    CoreHousehold,
    CoreMembership,
    CorePermissionGrant,
    CorePerson,
    CorePersonRelationship,
    LegacyIdMapping,
)
from app.models.family import Family, FamilyMember, FamilyRole  # noqa: E402
from app.models.user import User  # noqa: E402
from app.v2.migration_authority import (  # noqa: E402
    V2_VERSIONED_MIGRATION_TABLES,
    current_schema_authority_snapshot,
)
from app.v2.uuid7 import is_uuid7, uuid7_str  # noqa: E402


CORE_TABLES = {
    "core_accounts",
    "core_auth_identities",
    "core_persons",
    "core_households",
    "core_memberships",
    "core_person_relationships",
    "core_permission_grants",
    "legacy_id_mappings",
}


@pytest.fixture()
def db():
    engine = create_engine("sqlite:///:memory:")
    for table in (User.__table__, Family.__table__):
        table.create(engine)
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE family_members (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    family_id INTEGER NOT NULL,
                    user_id INTEGER UNIQUE,
                    display_name VARCHAR(120) NOT NULL,
                    role VARCHAR(16) NOT NULL,
                    goals JSON NOT NULL DEFAULT '[]',
                    restrictions JSON NOT NULL DEFAULT '[]',
                    is_virtual BOOLEAN NOT NULL DEFAULT 0,
                    virtual_kind VARCHAR(32),
                    allow_admin_profile_edit BOOLEAN NOT NULL DEFAULT 0,
                    nutrition_profile JSON NOT NULL DEFAULT '{}',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        )
    for table in (
        CorePerson.__table__,
        CoreAccount.__table__,
        CoreAuthIdentity.__table__,
        CoreHousehold.__table__,
        CoreMembership.__table__,
        CorePersonRelationship.__table__,
        CorePermissionGrant.__table__,
        LegacyIdMapping.__table__,
    ):
        table.create(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def _seed_legacy_family(db):
    user = User(telegram_id=10001, username="owner", first_name="Owner")
    family = Family(name="Household")
    db.add_all([user, family])
    db.flush()
    db.execute(
        text(
            """
            INSERT INTO family_members (
                family_id, user_id, display_name, role, goals, restrictions,
                is_virtual, virtual_kind, allow_admin_profile_edit, nutrition_profile
            )
            VALUES (:family_id, :user_id, 'Owner', :role, '[]', '[]', 0, NULL, 0, '{}')
            """
        ),
        {"family_id": family.id, "user_id": user.id, "role": FamilyRole.ADMIN.value},
    )
    db.execute(
        text(
            """
            INSERT INTO family_members (
                family_id, user_id, display_name, role, goals, restrictions,
                is_virtual, virtual_kind, allow_admin_profile_edit, nutrition_profile
            )
            VALUES (:family_id, NULL, 'Child', :role, '[]', '[]', 1, 'child', 0, :profile)
            """
        ),
        {
            "family_id": family.id,
            "role": FamilyRole.CHILD.value,
            "profile": '{"age_months": 84, "allergies": ["peanut"]}',
        },
    )
    db.commit()
    owner_member = db.query(FamilyMember).filter_by(user_id=user.id).one()
    child_member = db.query(FamilyMember).filter_by(user_id=None).one()
    return user, family, owner_member, child_member


def test_wave_02_core_tables_are_v2_migration_owned_only():
    snapshot = current_schema_authority_snapshot()

    assert V2_VERSIONED_MIGRATION_TABLES == CORE_TABLES
    assert snapshot.authority_overlaps == {}
    assert CORE_TABLES.isdisjoint(database_migrations.CREATE_ALL_TABLES)
    assert CORE_TABLES.isdisjoint(database_migrations.CUSTOM_SQL_TABLES)
    assert CORE_TABLES.isdisjoint(database_migrations.RECIPE_ENGINE_TABLES)


def test_legacy_create_all_does_not_include_core_orm_tables():
    class Base:
        metadata = type(
            "Metadata",
            (),
            {"sorted_tables": [CoreAccount.__table__, CorePerson.__table__, User.__table__]},
        )()

    selected = database_migrations._metadata_tables_for_authority(
        Base,
        database_migrations.CREATE_ALL_TABLES,
    )

    assert [table.name for table in selected] == ["users"]


def test_core_ids_use_uuid7_and_account_person_are_separate(db):
    account_id = uuid7_str()
    person_id = uuid7_str()
    account = CoreAccount(account_id=account_id, status="active")
    person = CorePerson(person_id=person_id, display_name="Human")
    db.add_all([person, account])
    db.commit()

    assert is_uuid7(account.account_id)
    assert is_uuid7(person.person_id)
    assert account.account_id != person.person_id
    assert account.primary_person_id is None


def test_person_can_exist_without_account_and_without_birth_date(db):
    person = CorePerson(person_id=uuid7_str(), display_name="Dependent")
    db.add(person)
    db.commit()

    assert person.birth_date is None
    assert person.birth_date_precision == "unknown"
    assert db.query(CoreAccount).count() == 0


def test_auth_identity_provider_subject_is_unique(db):
    p1 = CorePerson(person_id=uuid7_str())
    p2 = CorePerson(person_id=uuid7_str())
    a1 = CoreAccount(account_id=uuid7_str(), primary_person_id=p1.person_id)
    a2 = CoreAccount(account_id=uuid7_str(), primary_person_id=p2.person_id)
    db.add_all([p1, p2, a1, a2])
    db.flush()
    db.add(CoreAuthIdentity(auth_identity_id=uuid7_str(), account_id=a1.account_id, provider="telegram", provider_subject="42"))
    db.add(CoreAuthIdentity(auth_identity_id=uuid7_str(), account_id=a2.account_id, provider="telegram", provider_subject="42"))

    with pytest.raises(IntegrityError):
        db.commit()


def test_relationship_and_permission_are_distinct_and_no_self_relationship(db):
    subject = CorePerson(person_id=uuid7_str(), display_name="A")
    target = CorePerson(person_id=uuid7_str(), display_name="B")
    db.add_all([subject, target])
    db.flush()

    db.add(
        CorePersonRelationship(
            relationship_id=uuid7_str(),
            subject_person_id=subject.person_id,
            target_person_id=subject.person_id,
            relationship_type="parent_of",
        )
    )
    with pytest.raises(IntegrityError):
        db.commit()

    db.rollback()
    db.add_all([subject, target])
    db.flush()
    db.add(
        CorePersonRelationship(
            relationship_id=uuid7_str(),
            subject_person_id=subject.person_id,
            target_person_id=target.person_id,
            relationship_type="parent_of",
        )
    )
    db.commit()

    assert db.query(CorePersonRelationship).count() == 1
    assert db.query(CorePermissionGrant).count() == 0


def test_permission_requires_explicit_scope(db):
    subject = CorePerson(person_id=uuid7_str())
    db.add(subject)
    db.flush()
    db.add(
        CorePermissionGrant(
            permission_grant_id=uuid7_str(),
            subject_person_id=subject.person_id,
            domain_scope="food",
            capability="view_menu",
        )
    )

    with pytest.raises(IntegrityError):
        db.commit()


def test_legacy_user_family_member_mapping_is_idempotent(db):
    user, family, owner_member, child_member = _seed_legacy_family(db)

    first = map_legacy_core_identities(db)
    ids_after_first = {
        "accounts": [row.account_id for row in db.query(CoreAccount).order_by(CoreAccount.account_id)],
        "persons": [row.person_id for row in db.query(CorePerson).order_by(CorePerson.person_id)],
        "households": [row.household_id for row in db.query(CoreHousehold).order_by(CoreHousehold.household_id)],
        "memberships": [row.membership_id for row in db.query(CoreMembership).order_by(CoreMembership.membership_id)],
        "mappings": [
            (row.legacy_table, row.legacy_id_text, row.target_table, row.target_id_uuid)
            for row in db.query(LegacyIdMapping).order_by(
                LegacyIdMapping.legacy_table,
                LegacyIdMapping.legacy_id_text,
                LegacyIdMapping.target_table,
            )
        ],
    }

    second = map_legacy_core_identities(db)
    ids_after_second = {
        "accounts": [row.account_id for row in db.query(CoreAccount).order_by(CoreAccount.account_id)],
        "persons": [row.person_id for row in db.query(CorePerson).order_by(CorePerson.person_id)],
        "households": [row.household_id for row in db.query(CoreHousehold).order_by(CoreHousehold.household_id)],
        "memberships": [row.membership_id for row in db.query(CoreMembership).order_by(CoreMembership.membership_id)],
        "mappings": [
            (row.legacy_table, row.legacy_id_text, row.target_table, row.target_id_uuid)
            for row in db.query(LegacyIdMapping).order_by(
                LegacyIdMapping.legacy_table,
                LegacyIdMapping.legacy_id_text,
                LegacyIdMapping.target_table,
            )
        ],
    }

    assert first.legacy_users_scanned == 1
    assert first.legacy_families_scanned == 1
    assert first.family_members_scanned == 2
    assert second.accounts_created == 0
    assert second.persons_created == 0
    assert second.households_created == 0
    assert second.memberships_created == 0
    assert ids_after_first == ids_after_second
    assert db.query(CoreAccount).count() == 1
    assert db.query(CoreAuthIdentity).count() == 1
    assert db.query(CorePerson).count() == 2
    assert db.query(CoreHousehold).count() == 1
    assert db.query(CoreMembership).count() == 2

    child_person_mapping = (
        db.query(LegacyIdMapping)
        .filter_by(
            legacy_table="family_members",
            legacy_id_text=str(child_member.id),
            target_table="core_persons",
        )
        .one()
    )
    child_person = db.get(CorePerson, child_person_mapping.target_id_uuid)
    assert child_person.birth_date is None
    assert child_person.birth_date_precision == "unknown"
    assert db.query(CoreAccount).filter(CoreAccount.primary_person_id == child_person.person_id).count() == 0


def test_ambiguous_unlinked_member_does_not_merge_or_create_fake_account(db):
    _user, _family, _owner_member, child_member = _seed_legacy_family(db)

    report = map_legacy_core_identities(db)

    assert report.ambiguous_reconfirm_cases == 0
    assert db.query(CoreAccount).count() == 1
    assert (
        db.query(LegacyIdMapping)
        .filter_by(
            legacy_table="family_members",
            legacy_id_text=str(child_member.id),
            target_table="core_persons",
        )
        .count()
        == 1
    )


def test_sqlite_concurrent_like_second_runner_hits_unique_mapping_safety(db):
    _seed_legacy_family(db)
    map_legacy_core_identities(db)
    existing = db.query(LegacyIdMapping).filter_by(legacy_table="users", target_table="core_accounts").one()

    db.add(
        LegacyIdMapping(
            mapping_id=uuid7_str(),
            legacy_table=existing.legacy_table,
            legacy_id_text=existing.legacy_id_text,
            target_table=existing.target_table,
            target_id_uuid=existing.target_id_uuid,
        )
    )

    with pytest.raises(IntegrityError):
        db.commit()


def test_wave_02_migration_has_no_foodprofile_recipe_or_importantdate_tables():
    source = (API_ROOT / "alembic" / "versions" / "20260922_0002_core_roots.py").read_text(encoding="utf-8")
    lowered = source.lower()

    assert "food_profiles" not in lowered
    assert "recipe_versions" not in lowered
    assert "important_dates" not in lowered
    assert "nutrition_targets" not in lowered


def test_core_birth_date_contract_does_not_store_age_columns():
    columns = set(CorePerson.__table__.columns.keys())

    assert "birth_date" in columns
    assert "age" not in columns
    assert "age_months" not in columns
