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
from app.food.profile_migration import migrate_legacy_food_profiles  # noqa: E402
from app.food.profile_models import FoodProfile, FoodProfileFact, FoodProfileReconfirmation  # noqa: E402
from app.models.family import Family, FamilyRole  # noqa: E402
from app.models.user import User  # noqa: E402
from app.v2.migration_authority import V2_VERSIONED_MIGRATION_TABLES, current_schema_authority_snapshot  # noqa: E402
from app.v2.reference_contracts import KnowledgeState  # noqa: E402
from app.v2.uuid7 import uuid7_str  # noqa: E402


FOOD_TABLES = {"food_profiles", "food_profile_facts", "food_profile_reconfirmations"}


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
        connection.execute(
            text(
                """
                CREATE TABLE user_profiles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER UNIQUE NOT NULL,
                    current_step INTEGER DEFAULT 0,
                    completed BOOLEAN DEFAULT 0,
                    goals JSON DEFAULT '[]',
                    diets JSON DEFAULT '[]',
                    allergies JSON DEFAULT '[]',
                    restrictions JSON DEFAULT '[]',
                    typed_safety_profile JSON DEFAULT '[]',
                    typed_medical_context JSON DEFAULT '[]',
                    favorite_foods TEXT DEFAULT '',
                    disliked_foods TEXT DEFAULT '',
                    budget VARCHAR(32),
                    cooking_time VARCHAR(32),
                    age INTEGER,
                    age_months INTEGER,
                    gender VARCHAR(24),
                    height_cm INTEGER,
                    weight_kg FLOAT,
                    nutrition_goal VARCHAR(32),
                    activity_level VARCHAR(32),
                    physical_activity_group VARCHAR(32),
                    life_stage VARCHAR(32),
                    medical_restrictions TEXT DEFAULT '',
                    banned_foods TEXT DEFAULT '',
                    dish_complexity VARCHAR(32),
                    pro_data JSON DEFAULT '{}',
                    goal_details JSON DEFAULT '{}',
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
        FoodProfile.__table__,
        FoodProfileFact.__table__,
        FoodProfileReconfirmation.__table__,
    ):
        table.create(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


def _seed_family(db):
    owner = User(telegram_id=333001, username="owner", first_name="Owner")
    family = Family(name="Food Household")
    db.add_all([owner, family])
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
        {"family_id": family.id, "user_id": owner.id, "role": FamilyRole.ADMIN.value},
    )
    db.execute(
        text(
            """
            INSERT INTO family_members (
                family_id, user_id, display_name, role, goals, restrictions,
                is_virtual, virtual_kind, allow_admin_profile_edit, nutrition_profile
            )
            VALUES (:family_id, NULL, 'Child', :role, '[]', :restrictions, 1, 'child', 0, :profile)
            """
        ),
        {
            "family_id": family.id,
            "role": FamilyRole.CHILD.value,
            "restrictions": '["lactose_intolerance"]',
            "profile": (
                '{"age_months": 84, "allergies": [], '
                '"typed_medical_context": [{"kind": "medical_condition", "concept_id": "celiac"}], '
                '"notes": "Avoid red sauces"}'
            ),
        },
    )
    db.execute(
        text(
            """
            INSERT INTO user_profiles (
                user_id, allergies, restrictions, diets, typed_safety_profile,
                medical_restrictions, banned_foods, age, age_months,
                nutrition_goal, activity_level, life_stage
            )
            VALUES (
                :user_id, :allergies, :restrictions, :diets, :typed_safety_profile,
                :medical_restrictions, :banned_foods, :age, :age_months,
                :nutrition_goal, :activity_level, :life_stage
            )
            """
        ),
        {
            "user_id": owner.id,
            "allergies": '["peanut", "tree_nut", "none"]',
            "restrictions": '["lactose_intolerance"]',
            "diets": "[]",
            "typed_safety_profile": '[{"kind": "allergy", "concept_id": "fish"}]',
            "medical_restrictions": "Doctor mentioned possible celiac history",
            "banned_foods": "mushrooms",
            "age": 35,
            "age_months": None,
            "nutrition_goal": "maintain",
            "activity_level": "moderate",
            "life_stage": "adult",
        },
    )
    db.commit()
    map_legacy_core_identities(db)
    return owner


def _facts(db):
    return {
        (row.fact_type, row.fact_key, row.knowledge_state): row
        for row in db.query(FoodProfileFact).order_by(FoodProfileFact.fact_type, FoodProfileFact.fact_key)
    }


def test_food_profile_tables_are_v2_migration_owned_only():
    snapshot = current_schema_authority_snapshot()

    assert FOOD_TABLES <= V2_VERSIONED_MIGRATION_TABLES
    assert snapshot.authority_overlaps == {}
    assert FOOD_TABLES.isdisjoint(database_migrations.CREATE_ALL_TABLES)
    assert FOOD_TABLES.isdisjoint(database_migrations.CUSTOM_SQL_TABLES)
    assert FOOD_TABLES.isdisjoint(database_migrations.RECIPE_ENGINE_TABLES)


def test_unknown_semantics_empty_array_is_not_known_none_and_explicit_none_is_known_none(db):
    _seed_family(db)

    report = migrate_legacy_food_profiles(db)
    facts = _facts(db)

    assert report.ambiguous_empty_legacy_values >= 2
    assert ("allergy", "peanut", KnowledgeState.KNOWN_PRESENT.value) in facts
    assert ("allergy", "tree_nut", KnowledgeState.KNOWN_PRESENT.value) in facts
    assert ("allergy", "none", KnowledgeState.KNOWN_NONE.value) in facts
    assert all(
        not (
            row.fact_type == "allergy"
            and row.fact_key == "legacy_empty_value"
            and row.knowledge_state == KnowledgeState.KNOWN_NONE.value
        )
        for row in db.query(FoodProfileFact)
    )
    assert (
        db.query(FoodProfileReconfirmation)
        .filter_by(fact_type="allergy", reason="empty_legacy_value_not_known_none")
        .count()
        == 1
    )


def test_allergy_intolerance_and_celiac_remain_separate_typed_facts(db):
    _seed_family(db)

    migrate_legacy_food_profiles(db)
    facts = _facts(db)

    assert ("allergy", "fish", KnowledgeState.KNOWN_PRESENT.value) in facts
    assert ("intolerance", "lactose", KnowledgeState.KNOWN_PRESENT.value) in facts
    assert ("medical_food_context", "celiac", KnowledgeState.KNOWN_PRESENT.value) in facts
    assert ("allergy", "lactose", KnowledgeState.KNOWN_PRESENT.value) not in facts
    assert ("intolerance", "celiac", KnowledgeState.KNOWN_PRESENT.value) not in facts


def test_legacy_age_and_free_text_create_reconfirmation_not_safety_facts(db):
    _seed_family(db)

    report = migrate_legacy_food_profiles(db)
    reconfirmations = {
        (row.fact_type, row.fact_key, row.reason)
        for row in db.query(FoodProfileReconfirmation).order_by(FoodProfileReconfirmation.fact_type)
    }
    fact_columns = set(FoodProfileFact.__table__.columns.keys())

    assert report.free_text_reconfirmation_cases >= 2
    assert ("age_context", "legacy_declared_age", "legacy_age_not_core_birth_date") in reconfirmations
    assert ("medical_restrictions", "legacy_free_text", "free_text_requires_user_reconfirmation") in reconfirmations
    assert "age" not in fact_columns
    assert "age_months" not in fact_columns
    assert "birth_date" not in fact_columns


def test_food_profile_migration_is_idempotent(db):
    _seed_family(db)

    first = migrate_legacy_food_profiles(db)
    first_counts = (
        db.query(FoodProfile).count(),
        db.query(FoodProfileFact).count(),
        db.query(FoodProfileReconfirmation).count(),
    )
    second = migrate_legacy_food_profiles(db)
    second_counts = (
        db.query(FoodProfile).count(),
        db.query(FoodProfileFact).count(),
        db.query(FoodProfileReconfirmation).count(),
    )

    assert first.food_profiles_created == 2
    assert second.food_profiles_created == 0
    assert second.facts_created == 0
    assert second.reconfirmations_created == 0
    assert first_counts == second_counts


def test_pending_reconfirmation_source_uniqueness_is_enforced(db):
    _seed_family(db)
    migrate_legacy_food_profiles(db)
    existing = db.query(FoodProfileReconfirmation).first()

    db.add(
        FoodProfileReconfirmation(
            reconfirmation_id=uuid7_str(),
            food_profile_id=existing.food_profile_id,
            fact_type=existing.fact_type,
            fact_key=existing.fact_key,
            reason=existing.reason,
            status=existing.status,
            source_kind=existing.source_kind,
            source_legacy_table=existing.source_legacy_table,
            source_legacy_id_text=existing.source_legacy_id_text,
            provenance_json=existing.provenance_json,
        )
    )

    with pytest.raises(IntegrityError):
        db.commit()


def test_wave_03_migration_has_no_wave_04_or_ri2_tables():
    source = (API_ROOT / "alembic" / "versions" / "20260922_0003_food_profiles.py").read_text(encoding="utf-8")
    lowered = source.lower()

    assert "food_identities" not in lowered
    assert "food_compositions" not in lowered
    assert "food_safety_evidence" not in lowered
    assert "packaged_products" not in lowered
    assert "recipe_versions" not in lowered
    assert "nutrition_targets" not in lowered
