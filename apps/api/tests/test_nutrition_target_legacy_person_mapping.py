from __future__ import annotations

from sqlalchemy import Column, Integer, MetaData, String, Table, create_engine, insert

from app.cutover.nutrition_target_runtime import NutritionTargetRuntime, PersonResolution


def _runtime():
    engine = create_engine("sqlite://")
    metadata = MetaData()
    mappings = Table(
        "legacy_id_mappings", metadata,
        Column("mapping_id", Integer, primary_key=True),
        Column("legacy_table", String), Column("legacy_id_text", String),
        Column("target_table", String), Column("target_id_uuid", String),
    )
    metadata.create_all(engine)
    return engine, mappings


def test_null_person_unique_user_linkage_resolves():
    engine, mappings = _runtime()
    with engine.begin() as conn:
        conn.execute(insert(mappings), {"mapping_id": 1, "legacy_table": "users", "legacy_id_text": "40", "target_table": "core_persons", "target_id_uuid": "person-40"})
    result = NutritionTargetRuntime(engine).resolve_person({"id": 1, "person_id": None, "user_id": 40, "family_id": None})
    assert result.classification is PersonResolution.UNIQUE_USER_PERSON
    assert result.person_id == "person-40"


def test_multiple_user_person_mappings_require_reconfirm():
    engine, mappings = _runtime()
    with engine.begin() as conn:
        conn.execute(insert(mappings), [
            {"mapping_id": 1, "legacy_table": "users", "legacy_id_text": "40", "target_table": "core_persons", "target_id_uuid": "person-a"},
            {"mapping_id": 2, "legacy_table": "users", "legacy_id_text": "40", "target_table": "core_persons", "target_id_uuid": "person-b"},
        ])
    result = NutritionTargetRuntime(engine).resolve_person({"id": 1, "person_id": None, "user_id": 40})
    assert result.classification is PersonResolution.RECONFIRM_REQUIRED


def test_explicit_member_relation_resolves():
    engine, mappings = _runtime()
    with engine.begin() as conn:
        conn.execute(insert(mappings), {"mapping_id": 1, "legacy_table": "family_members", "legacy_id_text": "7", "target_table": "core_persons", "target_id_uuid": "person-7"})
    result = NutritionTargetRuntime(engine).resolve_person({"id": 1, "person_id": 7, "user_id": None})
    assert result.classification is PersonResolution.UNIQUE_MEMBER_PERSON
    assert result.person_id == "person-7"


def test_no_evidence_requires_reconfirm():
    engine, _ = _runtime()
    result = NutritionTargetRuntime(engine).resolve_person({"id": 1, "person_id": None, "user_id": None, "family_id": None})
    assert result.classification is PersonResolution.RECONFIRM_REQUIRED


def test_conflicting_user_and_member_evidence_requires_reconfirm():
    engine, mappings = _runtime()
    with engine.begin() as conn:
        conn.execute(insert(mappings), [
            {"mapping_id": 1, "legacy_table": "users", "legacy_id_text": "40", "target_table": "core_persons", "target_id_uuid": "person-user"},
            {"mapping_id": 2, "legacy_table": "family_members", "legacy_id_text": "7", "target_table": "core_persons", "target_id_uuid": "person-member"},
        ])
    result = NutritionTargetRuntime(engine).resolve_person({"id": 1, "person_id": 7, "user_id": 40})
    assert result.classification is PersonResolution.CONFLICT
    assert result.person_id is None


def test_valid_direct_person_is_unchanged_and_invalid_explicit_is_not_substituted():
    engine, _ = _runtime()
    runtime = NutritionTargetRuntime(engine)
    direct = runtime.resolve_person({"id": 1, "person_id": "person-direct", "target_kind": "CALORIES", "effective_from": "2026-01-01"})
    invalid = runtime.resolve_person({"id": 2, "person_id": 999, "user_id": 40})
    assert direct.classification is PersonResolution.DIRECT_PERSON
    assert direct.person_id == "person-direct"
    assert invalid.classification is PersonResolution.INVALID_SOURCE
    assert invalid.person_id is None


def test_resolution_is_deterministic_across_repeated_calls():
    engine, mappings = _runtime()
    with engine.begin() as conn:
        conn.execute(insert(mappings), {"mapping_id": 1, "legacy_table": "users", "legacy_id_text": "40", "target_table": "core_persons", "target_id_uuid": "person-40"})
    row = {"id": 1, "person_id": None, "user_id": 40}
    runtime = NutritionTargetRuntime(engine)
    assert runtime.resolve_person(row) == runtime.resolve_person(row)
