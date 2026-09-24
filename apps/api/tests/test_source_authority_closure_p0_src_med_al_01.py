from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

API_DIR = Path(__file__).resolve().parents[1]
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

from app.nutrition.allergen_ontology import (
    AllergenFact,
    TypedSafetyEntry,
    decide_celiac_gluten_free,
)
from app.nutrition.medical_safety import (
    evaluate_medical_safety,
    resolve_sodium_target,
)
from app.nutrition.restriction_safety import recipe_is_allowed_for_profile
from app.services.nutrition.evidence_registry import (
    ALLERGEN_SAFETY_EVIDENCE_REGISTRY,
    CANONICAL_SOURCE_REGISTRY,
    MEDICAL_SAFETY_EVIDENCE_REGISTRY,
    RULE_SOURCE_TRACEABILITY,
    SOURCE_ALIAS_MATRIX,
    SOURCE_APPLICABILITY,
    SOURCE_AUTHORITY_CLASSES,
    SOURCE_ROLES,
    all_evidence_rule_records,
    resolve_source_id,
    validate_source_authority_registry,
)


AFFECTED_RULE_IDS = {
    "V2-AL-001",
    "V2-AL-002",
    "V2-AL-003",
    "V2-AL-004",
    "V2-AL-006",
    "V2-MD-001",
    "V2-MD-002",
    "V2-MD-003",
    "V2-MD-004",
    "V2-MD-005",
    "V2-MD-006",
    "V2-MD-007",
    "V2-XD-001",
    "V2-XD-002",
}


def _profile(*, typed=None, medical=None):
    return SimpleNamespace(
        typed_safety_profile=typed or [],
        typed_medical_context=medical or [],
        allergies=[],
        restrictions=[],
        diets=[],
        medical_restrictions="",
        age_months=None,
        age=None,
    )


def _recipe(**values):
    defaults = {
        "ingredients": [],
        "allergen_facts": [],
        "tags": [],
        "diets": [],
        "restrictions": [],
        "allergens": [],
        "gluten_free_status": None,
        "gluten_free_provenance_status": None,
    }
    defaults.update(values)
    return SimpleNamespace(**defaults)


def test_source_authority_registry_integrity_passes():
    assert validate_source_authority_registry() == []


def test_source_ids_are_unique_and_alias_targets_exist():
    assert len(CANONICAL_SOURCE_REGISTRY) == len(set(CANONICAL_SOURCE_REGISTRY))
    for alias in SOURCE_ALIAS_MATRIX:
        assert alias["canonical_source_id"] in CANONICAL_SOURCE_REGISTRY
    assert resolve_source_id("SRC-WHO-0005") == "SRC-WHO-SODIUM"
    assert resolve_source_id("SRC-HANDOFF-RU-FOOD-SAFETY-CORE") == "SRC-PLANAM-SAFETY-POLICY"


def test_supersession_integrity_and_no_active_source_supersedes_itself():
    for source_id, source in CANONICAL_SOURCE_REGISTRY.items():
        assert source_id not in source.get("supersedes", [])
        assert source_id not in source.get("superseded_by", [])
        for target in source.get("superseded_by", []):
            assert target in CANONICAL_SOURCE_REGISTRY

    old_sanpin = CANONICAL_SOURCE_REGISTRY["SRC-RU-SANPIN-3590-20"]
    new_sanpin = CANONICAL_SOURCE_REGISTRY["SRC-RU-SANPIN-4282-26"]
    assert old_sanpin["status"] == "SUPERSEDED"
    assert old_sanpin["superseded_by"] == ["SRC-RU-SANPIN-4282-26"]
    assert new_sanpin["status"] == "VERIFIED"
    assert new_sanpin["supersedes"] == ["SRC-RU-SANPIN-3590-20"]


def test_authority_and_applicability_enums_are_valid():
    for source in CANONICAL_SOURCE_REGISTRY.values():
        assert source["authority_class"] in SOURCE_AUTHORITY_CLASSES
        assert set(source["applicability"]) <= SOURCE_APPLICABILITY

    for claims in RULE_SOURCE_TRACEABILITY.values():
        for claim in claims:
            assert claim["authority_class"] in SOURCE_AUTHORITY_CLASSES
            assert claim["applicability"] in SOURCE_APPLICABILITY
            assert claim["source_role"] in SOURCE_ROLES


def test_affected_rules_have_traceability_and_sources_resolve():
    assert AFFECTED_RULE_IDS <= set(RULE_SOURCE_TRACEABILITY)
    for rule_id in AFFECTED_RULE_IDS:
        claims = RULE_SOURCE_TRACEABILITY[rule_id]
        assert claims
        for claim in claims:
            assert claim["source_id"] in CANONICAL_SOURCE_REGISTRY

    for evidence_id, record in all_evidence_rule_records().items():
        if not (evidence_id.startswith("EV-AL-") or evidence_id.startswith("EV-MD-")):
            continue
        source_id = record.get("source_id")
        if source_id is None:
            continue
        assert resolve_source_id(source_id) in CANONICAL_SOURCE_REGISTRY


def test_review_required_sources_cannot_masquerade_as_fully_verified():
    for source in CANONICAL_SOURCE_REGISTRY.values():
        if source["status"] == "REVIEW_REQUIRED":
            assert not str(source.get("review_status") or "").startswith("verified")

    for claims in RULE_SOURCE_TRACEABILITY.values():
        for claim in claims:
            source = CANONICAL_SOURCE_REGISTRY[claim["source_id"]]
            if source["status"] == "REVIEW_REQUIRED":
                assert claim["verification_status"] == "REVIEW_REQUIRED"


def test_public_catering_and_institutional_scope_is_not_household_law():
    for source_id in ("SRC-RU-SANPIN-4282-26", "SRC-RU-SANPIN-3590-20"):
        source = CANONICAL_SOURCE_REGISTRY[source_id]
        assert "PUBLIC_CATERING_REFERENCE" in source["applicability"]
        assert "HOUSEHOLD_REFERENCE" not in source["applicability"]
        assert "NOT_DIRECT_HOUSEHOLD_LAW" in source["applicability"]


def test_international_source_role_is_explicit_and_not_removed():
    expected = {
        "SRC-NIAID-FOOD-ALLERGY",
        "SRC-NIDDK-CELIAC",
        "SRC-CODEX-CXS1",
        "SRC-NCBI-PAH-2025",
        "SRC-KDIGO-CKD-2024",
        "SRC-ADA-2026",
        "SRC-CDC-PREGNANCY-FOOD-SAFETY",
        "SRC-WHO-SODIUM",
    }
    assert expected <= set(CANONICAL_SOURCE_REGISTRY)

    for source_id in expected:
        assert any(
            claim["source_id"] == source_id and claim["source_role"] in SOURCE_ROLES
            for claims in RULE_SOURCE_TRACEABILITY.values()
            for claim in claims
        )


def test_existing_allergen_and_celiac_semantics_remain_unchanged():
    try:
        TypedSafetyEntry(
            kind="allergy",
            concept_id="lactose_intolerance",
            origin="user_declared",
        )
        assert False, "lactose intolerance must not become allergy"
    except ValueError:
        pass

    lactose_free_milk = _recipe(ingredients=[{"name": "молоко безлактозное"}])
    milk_allergy = _profile(
        typed=[{"kind": "allergy", "concept_id": "milk_protein", "origin": "user_declared"}]
    )
    lactose_intolerance = _profile(
        typed=[
            {
                "kind": "intolerance",
                "concept_id": "lactose_intolerance",
                "origin": "user_declared",
            }
        ]
    )
    assert recipe_is_allowed_for_profile(lactose_free_milk, lactose_intolerance)
    assert not recipe_is_allowed_for_profile(lactose_free_milk, milk_allergy)

    tagged = decide_celiac_gluten_free(_recipe(tags=["gluten_free"]))
    verified = decide_celiac_gluten_free(
        _recipe(
            gluten_free_status="verified_gluten_free",
            gluten_free_provenance_status="product_label",
        )
    )
    cross_contact = decide_celiac_gluten_free(
        _recipe(
            allergen_facts=[
                AllergenFact("wheat", "cross_contact", "product_label").to_dict()
            ]
        )
    )
    assert tagged.status == "unknown"
    assert verified.safe_for_celiac is True
    assert cross_contact.status == "cross_contact_risk"


def test_existing_medical_safety_semantics_remain_unchanged():
    pku_profile = _profile(
        medical=[
            {
                "condition_id": "phenylketonuria_pah",
                "origin": "clinician_recorded",
                "specialist_plan_present": True,
                "structured_context": {"phenylalanine_target": {"value": 300, "unit": "mg/day"}},
            }
        ]
    )
    assert any(
        decision.decision_class == "UNKNOWN"
        for decision in evaluate_medical_safety(_recipe(), pku_profile)
    )
    assert any(
        decision.decision_class == "BLOCK"
        for decision in evaluate_medical_safety(_recipe(aspartame_present=True), pku_profile)
    )

    diabetes_profile = _profile(
        medical=[{"condition_id": "diabetes", "origin": "user_declared"}]
    )
    assert evaluate_medical_safety(_recipe(), diabetes_profile)[0].decision_class == "ESCALATE"

    pregnancy_profile = _profile(
        medical=[{"condition_id": "pregnancy", "origin": "user_declared"}]
    )
    assert evaluate_medical_safety(_recipe(), pregnancy_profile)[0].decision_class == "UNKNOWN"
    assert resolve_sodium_target(age=30)["sodium_mg_per_day"]["value"] == 2000
    assert resolve_sodium_target(age_months=60)["status"] == "ESCALATE"


def test_registry_links_existing_ev_records_without_changing_statuses():
    assert ALLERGEN_SAFETY_EVIDENCE_REGISTRY["EV-AL-001"]["status"] == "match"
    assert ALLERGEN_SAFETY_EVIDENCE_REGISTRY["EV-AL-006"]["status"] == "match"
    assert MEDICAL_SAFETY_EVIDENCE_REGISTRY["EV-MD-002"]["status"] == "strong_partial_foundation"
    assert MEDICAL_SAFETY_EVIDENCE_REGISTRY["EV-MD-005"]["source_id"] == "SRC-WHO-SODIUM"
