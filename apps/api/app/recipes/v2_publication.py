from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.recipes.recipe_gold_v3_quality_gate import evaluate_recipe_gold_v3_quality_gate
from app.recipes.recipe_gold_v3_validation import validate_recipe_gold_v3


@dataclass(frozen=True)
class PublicationGateResult:
    allowed: bool
    reasons: tuple[str, ...] = ()
    quality_score: int = 0
    validation: dict[str, Any] = field(default_factory=dict)


def evaluate_publication_gate(candidate: dict[str, Any]) -> PublicationGateResult:
    validation = validate_recipe_gold_v3(candidate)
    quality = evaluate_recipe_gold_v3_quality_gate([candidate])
    score = int((quality.get("per_recipe") or [{}])[0].get("score") or validation.score or 0)
    reasons: list[str] = []
    if not validation.ok:
        reasons.extend(issue.code for issue in validation.errors)
    if score < 85:
        reasons.append("quality_below_85")
    if not candidate.get("source_signal_ids") and candidate.get("source_type") == "generated_original":
        reasons.append("missing_source_provenance")
    if candidate.get("ontology_state") in {"UNKNOWN", "AMBIGUOUS"}:
        reasons.append("ontology_review_required")
    if candidate.get("safety_state") in {"BLOCK", "UNKNOWN", "ESCALATE"}:
        reasons.append(f"safety_{str(candidate['safety_state']).lower()}")
    if (candidate.get("ai_override") or {}).get("safe") is True:
        reasons.append("ai_safe_override_forbidden")
    return PublicationGateResult(
        allowed=not reasons,
        reasons=tuple(dict.fromkeys(reasons)),
        quality_score=score,
        validation={"ok": validation.ok, "errors": [issue.code for issue in validation.errors], "warnings": [issue.code for issue in validation.warnings]},
    )
