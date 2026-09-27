from __future__ import annotations

from pathlib import Path

from app.planning.v2_models import Plan
from app.planning.v2_service import _aggregate_safety, fingerprint, recipe_safety_state
from app.recipes.v2_models import CanonicalRecipeVersion


ROOT = Path(__file__).parents[1]
MIGRATION = ROOT / "alembic" / "versions" / "20260927_0015_wave_4_planning.py"


def test_plan_owner_is_exactly_person_or_household():
    constraint = next(item for item in Plan.__table__.constraints if item.name == "ck_plans_owner_xor")
    assert "person_id IS NOT NULL AND household_id IS NULL" in str(constraint.sqltext)
    assert "person_id IS NULL AND household_id IS NOT NULL" in str(constraint.sqltext)


def test_recipe_version_safety_defaults_to_unknown_and_preserves_known_states():
    unknown = CanonicalRecipeVersion(
        recipe_version_id="v1",
        recipe_id="r1",
        version_number=1,
        lifecycle_status="PUBLISHED",
        title="Recipe",
    )
    assert recipe_safety_state(unknown) == "UNKNOWN"
    unknown.safety_claims_json = {"decision": "warn"}
    assert recipe_safety_state(unknown) == "WARN"
    assert _aggregate_safety(["SAFE", "UNKNOWN"]) == "UNKNOWN"
    assert _aggregate_safety(["SAFE", "BLOCK"]) == "BLOCK"


def test_request_fingerprint_is_deterministic_and_ordered_by_keys():
    assert fingerprint({"b": 2, "a": 1}) == fingerprint({"a": 1, "b": 2})
    assert fingerprint({"a": 1}) != fingerprint({"a": 2})


def test_wave_4_migration_contains_canonical_scope_and_safety_guards():
    text = MIGRATION.read_text(encoding="utf-8")
    for table in ("plans", "plan_assignments", "plan_participants", "plan_portions"):
        assert f'"{table}"' in text
    assert "ck_plans_owner_xor" in text
    assert "ck_plan_assignments_safety" in text
    assert "prevent_plan_revision_content_update" in text
    assert "DROP TRIGGER IF EXISTS trg_plan_revisions_immutable" in text


def test_wave_4_migration_keeps_legacy_planning_tables_as_compatibility_inputs():
    text = MIGRATION.read_text(encoding="utf-8")
    upgrade = text.split("def downgrade()", 1)[0]
    assert 'op.drop_table("plans_v2")' not in upgrade
    assert 'op.drop_table("plan_slot_participants")' not in upgrade
    assert 'op.drop_table("plan_slot_portions")' not in upgrade


def test_wave_4_exposes_only_the_four_amended_command_routes():
    router = (ROOT / "app" / "routers" / "v2_planning.py").read_text(encoding="utf-8")
    assert router.count("@router.post(") == 4
    assert '"/plans"' in router
    assert '"/plans/{plan_id}/generate"' in router
    assert '"/plans/{plan_id}/revisions/{revision_id}/replace"' in router
    assert '"/plans/{plan_id}/slots/{slot_id}/empty"' in router
