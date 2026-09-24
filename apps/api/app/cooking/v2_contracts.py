from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

@dataclass(frozen=True)
class CookingBatchV2:
    cooking_batch_id: str
    recipe_version_id: str | None = None
    plan_slot_id: str | None = None
    status: str = "PLANNED"
    actual_product_instance_ids: tuple[str, ...] = ()
    substitutions: tuple[dict[str, Any], ...] = ()

def recipe_instruction_is_cooking_proof(_: str) -> bool:
    return False

def cooking_completion_creates_consumption(_: CookingBatchV2) -> bool:
    return False

@dataclass(frozen=True)
class ConsumptionEventV2:
    person_id: str
    source_kind: str
    status: str = "PROPOSED"
    actual_portion: float | None = None
    actual_portion_unit: str | None = None
    nutrition_state: str = "UNKNOWN"
    provenance: dict[str, Any] = field(default_factory=dict)

    @property
    def portion_state(self) -> str:
        return "KNOWN" if self.actual_portion is not None and self.actual_portion_unit else "UNKNOWN"

def ai_food_report_is_authoritative(_: dict[str, Any]) -> bool:
    return False

def actual_substitution_changes_safety_input(substitution: dict[str, Any]) -> bool:
    return bool(substitution.get("actual_food_identity_key") or substitution.get("actual_product_instance_id"))
