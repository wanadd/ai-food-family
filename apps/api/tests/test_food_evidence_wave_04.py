from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

API_ROOT = Path(__file__).resolve().parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app import database_migrations  # noqa: E402
from app.food.evidence_contracts import (  # noqa: E402
    CompositionInput,
    SourceProvenance,
    ai_match_review_status,
    allergen_absence_status,
    can_create_authoritative_composition_fact,
    can_use_protein_as_authoritative_phe,
    missing_nutrient_value,
    pasteurization_status,
    recipe_instruction_proves_actual_cooking,
    resolve_conflicting_values,
    verified_gf_status,
)
from app.food.evidence_models import (  # noqa: E402
    EvidenceClaim,
    EvidenceRecord,
    EvidenceSource,
    FoodCompositionFact,
    ProductLabelFact,
    SourceSnapshot,
)
from app.v2.migration_authority import V2_VERSIONED_MIGRATION_TABLES, current_schema_authority_snapshot  # noqa: E402
from app.v2.uuid7 import uuid7_str  # noqa: E402


WAVE4_TABLES = {
    "evidence_sources",
    "source_snapshots",
    "evidence_records",
    "evidence_claims",
    "evidence_applicability",
    "food_aliases",
    "food_composition_facts",
    "food_evidence_fact_links",
    "product_label_facts",
}


@pytest.fixture()
def db():
    engine = create_engine("sqlite:///:memory:")
    for table in (
        EvidenceSource.__table__,
        SourceSnapshot.__table__,
        EvidenceRecord.__table__,
        EvidenceClaim.__table__,
        FoodCompositionFact.__table__,
        ProductLabelFact.__table__,
    ):
        table.create(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


def _source_chain(db):
    source = EvidenceSource(
        source_id=uuid7_str(),
        source_code="SRC-USDA-FDC",
        authority_tier="AUTHORITATIVE_DATASET",
        publisher="USDA",
        status="ACTIVE",
    )
    db.add(source)
    db.flush()
    snapshot = SourceSnapshot(
        snapshot_id=uuid7_str(),
        source_id=source.source_id,
        source_version="fdc-2026-04",
        content_hash="sha256:fdc-release",
    )
    db.add(snapshot)
    db.flush()
    record = EvidenceRecord(
        record_id=uuid7_str(),
        snapshot_id=snapshot.snapshot_id,
        source_record_locator="fdc:171688",
        title="Oats",
        status="ACTIVE",
    )
    db.add(record)
    db.flush()
    return source, snapshot, record


def test_wave_04_tables_have_v2_authority_and_zero_overlap():
    snapshot = current_schema_authority_snapshot()

    assert WAVE4_TABLES <= V2_VERSIONED_MIGRATION_TABLES
    assert snapshot.authority_overlaps == {}
    assert WAVE4_TABLES.isdisjoint(database_migrations.CREATE_ALL_TABLES)
    assert WAVE4_TABLES.isdisjoint(database_migrations.CUSTOM_SQL_TABLES)
    assert WAVE4_TABLES.isdisjoint(database_migrations.RECIPE_ENGINE_TABLES)


def test_source_snapshot_release_is_unique_and_versioned(db):
    source, snapshot, _record = _source_chain(db)
    db.add(
        SourceSnapshot(
            snapshot_id=uuid7_str(),
            source_id=source.source_id,
            source_version=snapshot.source_version,
            content_hash=snapshot.content_hash,
        )
    )

    with pytest.raises(IntegrityError):
        db.commit()


def test_authoritative_composition_requires_source_release_and_record(db):
    provenance = SourceProvenance(
        source_code="SRC-USDA-FDC",
        authority_tier="AUTHORITATIVE_DATASET",
        source_version="fdc-2026-04",
        source_record_locator="fdc:171688",
    )
    fact = CompositionInput(
        food_identity_key="oats",
        nutrient_key="fiber_g",
        value=10.6,
        unit="g",
        basis_amount=100,
        basis_unit="g",
        food_state="raw",
        provenance=provenance,
    )

    assert can_create_authoritative_composition_fact(fact)
    assert missing_nutrient_value(fact) == "KNOWN_PRESENT"


def test_missing_nutrient_is_unknown_not_zero():
    fact = CompositionInput(
        food_identity_key="oats",
        nutrient_key="phenylalanine_mg",
        value=None,
        unit="mg",
        basis_amount=100,
        basis_unit="g",
        food_state="raw",
        provenance=SourceProvenance("SRC-USDA-FDC", "AUTHORITATIVE_DATASET", "fdc-2026-04", "fdc:171688"),
    )

    assert missing_nutrient_value(fact) == "UNKNOWN"
    assert not can_create_authoritative_composition_fact(fact)


def test_explicit_zero_requires_provenance_and_is_not_missing(db):
    source, snapshot, _record = _source_chain(db)
    fact = FoodCompositionFact(
        composition_fact_id=uuid7_str(),
        food_identity_key="water",
        nutrient_key="fat_g",
        value=0.0,
        unit="g",
        basis_amount=100,
        basis_unit="g",
        food_state="liquid",
        source_id=source.source_id,
        snapshot_id=snapshot.snapshot_id,
        source_record_locator="fdc:water",
        confidence="SOURCE_BACKED",
        review_status="REVIEWED_ACCEPTED",
    )
    db.add(fact)
    db.commit()

    assert db.query(FoodCompositionFact).one().value == 0.0


def test_composition_value_without_source_cannot_be_inserted(db):
    db.add(
        FoodCompositionFact(
            composition_fact_id=uuid7_str(),
            food_identity_key="rice",
            nutrient_key="protein_g",
            value=2.7,
            unit="g",
            basis_amount=100,
            basis_unit="g",
            food_state="cooked",
            source_record_locator="missing-source",
        )
    )

    with pytest.raises(IntegrityError):
        db.commit()


def test_phe_requires_source_reported_not_protein_approximation():
    assert can_use_protein_as_authoritative_phe("phenylalanine_mg", "SOURCE_REPORTED")
    assert not can_use_protein_as_authoritative_phe("phenylalanine_mg", "PROTEIN_COEFFICIENT")


def test_conflicting_source_values_are_retained_not_averaged():
    provenance = SourceProvenance("SRC-USDA-FDC", "AUTHORITATIVE_DATASET", "v1", "a")
    left = CompositionInput("milk", "calcium_mg", 120, "mg", 100, "g", "liquid", provenance)
    right = CompositionInput("milk", "calcium_mg", 130, "mg", 100, "g", "liquid", provenance)

    assert resolve_conflicting_values([left, right]) == {
        "status": "CONFLICT_RETAINED",
        "averaged": False,
        "source_count": 2,
    }


def test_ai_food_match_does_not_become_verified():
    assert ai_match_review_status("AI_SUGGESTED", "REVIEWED_ACCEPTED") == "NEEDS_REVIEW"


def test_missing_allergen_row_is_not_absence():
    assert allergen_absence_status(None, None) == "UNKNOWN"


def test_verified_absence_requires_source_backing():
    provenance = SourceProvenance("SRC-LABEL", "PRODUCT_LABEL", "label-2026-09", "gtin:123")

    assert allergen_absence_status("ABSENT_VERIFIED", provenance) == "ABSENT_VERIFIED"
    assert allergen_absence_status("ABSENT_VERIFIED", None) == "UNKNOWN"


def test_generic_oats_are_not_verified_gluten_free():
    assert verified_gf_status("oats", None) == "UNKNOWN"


def test_product_label_can_prove_verified_gf_with_provenance():
    provenance = SourceProvenance("SRC-LABEL", "PRODUCT_LABEL", "label-2026-09", "gtin:123")

    assert (
        verified_gf_status(
            "oats",
            {
                "fact_type": "gluten_free_claim",
                "knowledge_state": "KNOWN_PRESENT",
                "provenance": provenance,
            },
        )
        == "VERIFIED_GF"
    )


def test_generic_milk_does_not_prove_pasteurization_but_label_can():
    provenance = SourceProvenance("SRC-LABEL", "PRODUCT_LABEL", "label-2026-09", "gtin:milk")

    assert pasteurization_status("milk", None) == "UNKNOWN"
    assert (
        pasteurization_status(
            "milk",
            {
                "fact_type": "pasteurization",
                "knowledge_state": "KNOWN_PRESENT",
                "provenance": provenance,
            },
        )
        == "PASTEURIZED"
    )


def test_recipe_instruction_does_not_prove_actual_cooking():
    assert not recipe_instruction_proves_actual_cooking("boil chicken until done")


def test_wave_04_migration_does_not_create_later_wave_tables():
    source = (API_ROOT / "alembic" / "versions" / "20260922_0004_food_evidence.py").read_text(encoding="utf-8")
    lowered = source.lower()

    assert "nutrition_targets" not in lowered
    assert "recipe_versions" not in lowered
    assert "planning" not in lowered
    assert "cooking_event" not in lowered
    assert "important_dates" not in lowered
