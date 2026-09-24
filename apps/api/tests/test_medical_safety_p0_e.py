"""P0-E typed medical context and escalation regression coverage."""

from types import SimpleNamespace

import pytest

from app.nutrition.medical_safety import (
    DECISION_CLASSES,
    evaluate_medical_safety,
    normalize_medical_context_entries,
    resolve_sodium_target,
)
from app.services.normalization.profile import normalize_profile_dict


def _profile(entries, *, age_months=None, age=None):
    return SimpleNamespace(
        typed_medical_context=entries,
        age_months=age_months,
        age=age,
        medical_restrictions="PKU, CKD, diabetes, pregnancy",
    )


def _recipe(**values):
    return SimpleNamespace(**values)


def test_medical_context_is_explicit_and_free_text_does_not_diagnose():
    normalized = normalize_profile_dict(
        {
            "medical_restrictions": "PKU",
            "typed_medical_context": [],
        }
    )
    assert normalized["typed_medical_context"] == []

    entries = normalize_medical_context_entries(
        [{"condition_id": "diabetes", "origin": "user_declared"}]
    )
    assert entries[0].condition_id == "diabetes"
    assert entries[0].origin == "user_declared"


def test_ai_or_unknown_provenance_cannot_be_promoted_to_clinician():
    with pytest.raises(ValueError):
        normalize_medical_context_entries(
            [{"condition_id": "diabetes", "origin": "ai"}]
        )


def test_decision_contract_and_pku_escalation_without_specialist_target():
    decisions = evaluate_medical_safety(
        _recipe(phenylalanine_mg_per_serving=10),
        _profile(
            [
                {
                    "condition_id": "phenylketonuria_pah",
                    "origin": "clinician_recorded",
                    "provenance_status": "clinician_recorded",
                    "structured_context": {},
                    "specialist_plan_present": False,
                }
            ]
        ),
    )
    assert {d.decision_class for d in decisions} <= DECISION_CLASSES
    assert any(d.decision_class == "ESCALATE" for d in decisions)


def test_pku_missing_phenylalanine_and_aspartame_are_not_cleared():
    profile = _profile(
        [
            {
                "condition_id": "phenylketonuria_pah",
                "origin": "clinician_recorded",
                "specialist_plan_present": True,
                "structured_context": {"phenylalanine_target": {"value": 300, "unit": "mg/day"}},
            }
        ]
    )
    missing = evaluate_medical_safety(_recipe(), profile)
    assert any(d.decision_class == "UNKNOWN" for d in missing)
    unsafe = evaluate_medical_safety(
        _recipe(aspartame_present=True), profile
    )
    assert any(d.decision_class == "BLOCK" for d in unsafe)


def test_ckd_and_diabetes_require_individualized_context():
    decisions = evaluate_medical_safety(
        _recipe(),
        _profile(
            [
                {"condition_id": "chronic_kidney_disease", "origin": "user_declared"},
                {"condition_id": "diabetes", "origin": "user_declared"},
            ]
        ),
    )
    assert {d.condition_id for d in decisions} == {"chronic_kidney_disease", "diabetes"}
    assert all(d.decision_class == "ESCALATE" for d in decisions)


def test_sodium_keeps_units_and_does_not_invent_child_or_infant_formula():
    adult = resolve_sodium_target(age=30)
    assert adult["sodium_mg_per_day"]["value"] == 2000
    assert adult["salt_g_per_day"]["value"] == 5
    assert adult["sodium_mg_per_day"]["unit"] == "mg"
    assert adult["salt_g_per_day"]["unit"] == "g"
    assert resolve_sodium_target(age_months=60)["status"] == "ESCALATE"
    assert resolve_sodium_target(age_months=8)["status"] == "ESCALATE"


def test_pregnancy_unknown_and_unsafe_food_states_are_distinct():
    profile = _profile([{"condition_id": "pregnancy", "origin": "user_declared"}])
    unknown = evaluate_medical_safety(_recipe(), profile)
    assert unknown[0].decision_class == "UNKNOWN"
    raw = evaluate_medical_safety(
        _recipe(
            pasteurization_status="unpasteurized",
            raw_undercooked_status="raw",
            process_state="served",
        ),
        profile,
    )
    assert any(d.decision_class == "BLOCK" for d in raw)


def test_medical_context_survives_legacy_normalization_without_flattening():
    payload = normalize_profile_dict(
        {
            "restrictions": ["gluten_free"],
            "medical_restrictions": "CKD",
            "typed_medical_context": [
                {
                    "condition_id": "chronic_kidney_disease",
                    "origin": "guardian_declared",
                    "structured_context": {"stage": "3"},
                }
            ],
        }
    )
    assert payload["restrictions"] == ["gluten_free"]
    assert payload["typed_medical_context"][0]["condition_id"] == "chronic_kidney_disease"
    assert payload["medical_restrictions"] == "CKD"
