from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

SAFETY_PRECEDENCE = {"BLOCK": 5, "ESCALATE": 4, "UNKNOWN": 3, "WARN": 2, "SAFE": 1}

@dataclass(frozen=True)
class HealthProjectionV2:
    person_id: str
    completeness: str
    planned: dict[str, Any] = field(default_factory=dict)
    actual: dict[str, Any] = field(default_factory=dict)
    deviation: dict[str, Any] = field(default_factory=dict)
    safety_status: str = "UNKNOWN"

def resolve_safety_status(current: str, candidate: str) -> str:
    return candidate if SAFETY_PRECEDENCE.get(candidate, 0) > SAFETY_PRECEDENCE.get(current, 0) else current

def ai_can_override_safety(current: str, proposed: str) -> bool:
    return SAFETY_PRECEDENCE.get(proposed, 0) > SAFETY_PRECEDENCE.get(current, 0) and current not in {"BLOCK", "UNKNOWN"}

def missing_consumption_means_skipped(_: bool) -> bool:
    return False

def family_nutrition_is_average(_: list[HealthProjectionV2]) -> bool:
    return False

def recommendation_provenance(trigger: str, person_id: str, known: list[str], unknown: list[str]) -> dict[str, Any]:
    return {"trigger": trigger, "person_id": person_id, "known": known, "unknown": unknown}
