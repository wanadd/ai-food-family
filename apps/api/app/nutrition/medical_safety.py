"""Typed medical context and deterministic escalation decisions.

This module deliberately does not diagnose from free text, AI output, history,
or laboratory values. Medical decisions require an explicit person-scoped
condition and evidence-aware structured facts.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

MEDICAL_CONDITION_IDS = {
    "phenylketonuria_pah",
    "chronic_kidney_disease",
    "diabetes",
    "pregnancy",
}
MEDICAL_ORIGINS = {
    "user_declared",
    "guardian_declared",
    "clinician_recorded",
    "legacy_unstructured",
    "system_migration",
}
MEDICAL_PROVENANCE = {
    "unreviewed",
    "manual_reviewed",
    "clinician_recorded",
    "external_verified",
    "internal_legacy_unsourced",
    "needs_review",
}
DECISION_CLASSES = {"BLOCK", "WARN", "TARGET", "ADJUST", "ESCALATE", "UNKNOWN"}

MedicalDecisionClass = Literal[
    "BLOCK", "WARN", "TARGET", "ADJUST", "ESCALATE", "UNKNOWN"
]

EVIDENCE_BY_CONDITION = {
    "phenylketonuria_pah": "SRC-NCBI-PAH-2025",
    "chronic_kidney_disease": "SRC-KDIGO-CKD-2024",
    "diabetes": "SRC-ADA-2026",
    "pregnancy": "SRC-CDC-PREGNANCY-FOOD-SAFETY",
}


@dataclass(frozen=True)
class MedicalContextEntry:
    condition_id: str
    origin: str
    provenance_status: str
    structured_context: dict[str, Any] = field(default_factory=dict)
    specialist_plan_present: bool | None = None
    escalation_state: str | None = None
    escalation_reason: str | None = None


@dataclass(frozen=True)
class MedicalDecision:
    condition_id: str
    decision_class: MedicalDecisionClass
    reason: str
    evidence_id: str | None = None
    source_id: str | None = None
    provenance_status: str = "needs_review"
    person_scoped: bool = True

    @property
    def status(self) -> str:
        return self.decision_class


def normalize_medical_context_entries(values: Any) -> list[MedicalContextEntry]:
    """Normalize explicit typed entries; reject unsupported/unsafe identities."""
    if not values:
        return []
    if isinstance(values, dict):
        values = [values]
    result: list[MedicalContextEntry] = []
    seen: set[str] = set()
    for raw in values:
        if isinstance(raw, MedicalContextEntry):
            raw = {
                "condition_id": raw.condition_id,
                "origin": raw.origin,
                "provenance_status": raw.provenance_status,
                "structured_context": raw.structured_context,
                "specialist_plan_present": raw.specialist_plan_present,
                "escalation_state": raw.escalation_state,
                "escalation_reason": raw.escalation_reason,
            }
        if not isinstance(raw, dict):
            raise ValueError("typed_medical_context entries must be objects")
        condition_id = str(raw.get("condition_id") or "").strip().lower()
        if condition_id not in MEDICAL_CONDITION_IDS:
            raise ValueError(f"Unsupported medical condition: {condition_id}")
        if condition_id in seen:
            continue
        origin = str(raw.get("origin") or "").strip().lower()
        if origin not in MEDICAL_ORIGINS:
            raise ValueError(f"Unsupported medical context origin: {origin}")
        provenance = str(
            raw.get("provenance_status") or raw.get("provenance") or "unreviewed"
        ).strip().lower()
        if provenance not in MEDICAL_PROVENANCE:
            raise ValueError(f"Unsupported medical provenance: {provenance}")
        # AI, history, and free-text values may carry context for review, but
        # cannot be promoted to a diagnosis or clinician/external provenance.
        if origin == "legacy_unstructured":
            provenance = "internal_legacy_unsourced"
        structured = raw.get("structured_context")
        if structured is None:
            structured = {}
        if not isinstance(structured, dict):
            raise ValueError("structured_context must be an object")
        specialist = raw.get("specialist_plan_present")
        if specialist is not None:
            specialist = bool(specialist)
        result.append(
            MedicalContextEntry(
                condition_id=condition_id,
                origin=origin,
                provenance_status=provenance,
                structured_context=dict(structured),
                specialist_plan_present=specialist,
                escalation_state=raw.get("escalation_state"),
                escalation_reason=raw.get("escalation_reason"),
            )
        )
        seen.add(condition_id)
    return result


def medical_context_to_dicts(values: Any) -> list[dict[str, Any]]:
    return [
        {
            "condition_id": entry.condition_id,
            "origin": entry.origin,
            "provenance_status": entry.provenance_status,
            "structured_context": entry.structured_context,
            "specialist_plan_present": entry.specialist_plan_present,
            "escalation_state": entry.escalation_state,
            "escalation_reason": entry.escalation_reason,
        }
        for entry in normalize_medical_context_entries(values)
    ]


def typed_medical_context_from_profile(profile: Any) -> list[MedicalContextEntry]:
    return normalize_medical_context_entries(
        getattr(profile, "typed_medical_context", None)
        or getattr(profile, "medical_context", None)
        or []
    )


def format_medical_context(entries: Any) -> str:
    """Render identity and review state for prompts; never render a diagnosis."""
    parts = []
    for entry in typed_medical_context_from_profile(entries):
        state = entry.escalation_state or "review_required"
        parts.append(
            f"{entry.condition_id}({entry.origin}; {entry.provenance_status}; {state})"
        )
    return ", ".join(parts)


def _fact(recipe: Any, key: str, default: Any = None) -> Any:
    facts = getattr(recipe, "medical_safety_facts_json", None) or getattr(
        recipe, "medical_safety_facts", None
    )
    if isinstance(facts, dict) and key in facts:
        return facts[key]
    return getattr(recipe, key, default)


def _provenance(recipe: Any, key: str) -> str:
    facts = getattr(recipe, "medical_safety_facts_json", None) or getattr(
        recipe, "medical_safety_facts", None
    )
    if isinstance(facts, dict):
        value = facts.get(f"{key}_provenance_status") or facts.get("provenance_status")
        if value:
            return str(value)
    return "needs_review"


def resolve_sodium_target(*, age_months: int | None = None, age: int | None = None) -> dict[str, Any]:
    """Return only the sourced adult target; child/infant adjustment is unresolved."""
    months = age_months if age_months is not None else (age * 12 if age is not None else None)
    if months is None or months >= 192:
        return {
            "status": "TARGET",
            "sodium_mg_per_day": {"operator": "<", "value": 2000, "unit": "mg"},
            "salt_g_per_day": {"operator": "<", "value": 5, "unit": "g"},
            "source_id": "SRC-WHO-SODIUM",
            "provenance_status": "external_verified",
        }
    if months >= 24:
        return {
            "status": "ESCALATE",
            "reason": "Для детей 2-15 лет нужна точная energy-adjusted evidence resolver; формула не задана.",
            "source_id": "SRC-WHO-SODIUM",
            "provenance_status": "needs_review",
        }
    return {
        "status": "ESCALATE",
        "reason": "Infant sodium scope is separate and has no adult/child fall-through target.",
        "source_id": "SRC-WHO-SODIUM",
        "provenance_status": "needs_review",
    }


def evaluate_medical_safety(recipe: Any, profile: Any) -> list[MedicalDecision]:
    """Evaluate explicit medical context without turning unknown into safe."""
    decisions: list[MedicalDecision] = []
    for entry in typed_medical_context_from_profile(profile):
        context = entry.structured_context
        source = EVIDENCE_BY_CONDITION[entry.condition_id]
        if entry.condition_id == "phenylketonuria_pah":
            target = context.get("phenylalanine_target")
            if not target or not entry.specialist_plan_present:
                decisions.append(MedicalDecision(entry.condition_id, "ESCALATE", "Missing individualized specialist phenylalanine target/plan.", source_id=source))
            phe = _fact(recipe, "phenylalanine_mg_per_serving")
            if phe is None:
                decisions.append(MedicalDecision(entry.condition_id, "UNKNOWN", "Recipe phenylalanine fact is unavailable; PKU safety cannot be certified.", source_id=source))
            if _fact(recipe, "aspartame_present") is True:
                decisions.append(MedicalDecision(entry.condition_id, "BLOCK", "Structured recipe fact indicates aspartame; PKU review is required.", source_id=source, provenance_status=_provenance(recipe, "aspartame_present")))
        elif entry.condition_id == "chronic_kidney_disease":
            if not context.get("clinician_targets") or not context.get("stage"):
                decisions.append(MedicalDecision(entry.condition_id, "ESCALATE", "CKD stage and individualized clinician targets are required for a clinical nutrition decision.", source_id=source))
            elif context.get("stage") in {"unknown", "unspecified"}:
                decisions.append(MedicalDecision(entry.condition_id, "UNKNOWN", "CKD stage is explicitly unresolved; no generic macros are applied.", source_id=source))
        elif entry.condition_id == "diabetes":
            if not context.get("individualized_mnt"):
                decisions.append(MedicalDecision(entry.condition_id, "ESCALATE", "Individualized diabetes nutrition therapy context is absent; general targets are not treatment targets.", source_id=source))
            else:
                decisions.append(MedicalDecision(entry.condition_id, "ADJUST", "Use individualized nutrition therapy context; no universal carb percentage or fixed grams.", source_id=source, provenance_status=entry.provenance_status))
        elif entry.condition_id == "pregnancy":
            pasteurization = _fact(recipe, "pasteurization_status")
            cooking = _fact(recipe, "raw_undercooked_status")
            process = _fact(recipe, "process_state")
            if pasteurization == "unpasteurized" or cooking in {"raw", "undercooked"}:
                decisions.append(MedicalDecision(entry.condition_id, "BLOCK", "Structured pregnancy food-state fact indicates an unsafe raw/unpasteurized state.", source_id=source, provenance_status=_provenance(recipe, "process_state")))
            elif pasteurization in {"unknown", None} or cooking in {"unknown", None} or process in {"unknown", None}:
                decisions.append(MedicalDecision(entry.condition_id, "UNKNOWN", "Material pregnancy food-state/process fact is unknown or unsafe; keyword absence cannot certify safety.", source_id=source))
            else:
                decisions.append(MedicalDecision(entry.condition_id, "WARN", "Pregnancy food-state facts are present; preserve source review in downstream serving decisions.", source_id=source, provenance_status=_provenance(recipe, "process_state")))
    return decisions


def medical_decision_conflicts(recipe: Any, profile: Any) -> list[Any]:
    """Adapt medical decisions to restriction_safety's conflict contract."""
    from app.nutrition.restriction_safety import RestrictionConflict

    conflicts = []
    for decision in evaluate_medical_safety(recipe, profile):
        severity = "hard" if decision.decision_class == "BLOCK" else "soft"
        if decision.decision_class in {"UNKNOWN", "ESCALATE"}:
            severity = "hard"
        conflicts.append(
            RestrictionConflict(
                restriction_key=f"medical:{decision.condition_id}:{decision.decision_class.lower()}",
                label_ru=decision.condition_id,
                severity=severity,
                reason=decision.reason,
                source="typed_safety",
                evidence_status=decision.provenance_status,
            )
        )
    return conflicts


__all__ = [
    "DECISION_CLASSES",
    "EVIDENCE_BY_CONDITION",
    "MEDICAL_CONDITION_IDS",
    "MedicalContextEntry",
    "MedicalDecision",
    "evaluate_medical_safety",
    "format_medical_context",
    "medical_context_to_dicts",
    "medical_decision_conflicts",
    "normalize_medical_context_entries",
    "resolve_sodium_target",
    "typed_medical_context_from_profile",
]
