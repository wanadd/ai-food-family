from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any


@dataclass(frozen=True)
class PlanSlotV2:
    slot_key: str
    planned_date: date
    meal_type: str
    slot_state: str = "EMPTY"
    recipe_version_id: str | None = None
    manual_override: bool = False
    provenance: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.slot_state == "EMPTY" and self.recipe_version_id is not None:
            raise ValueError("explicit empty slot cannot reference a recipe version")
        if self.slot_state == "ASSIGNED" and self.recipe_version_id is None:
            raise ValueError("assigned slot requires a recipe version")


@dataclass(frozen=True)
class SlotParticipant:
    person_id: str
    participation_state: str = "PARTICIPATING"


@dataclass(frozen=True)
class SlotPortion:
    person_id: str
    value: float | None = None
    unit: str | None = None
    source_kind: str = "UNKNOWN"


def enrich_slot_without_reanimation(slot: PlanSlotV2, suggestion_recipe_version_id: str | None) -> PlanSlotV2:
    """Catalog enrichment may fill only an unassigned slot, never explicit EMPTY."""
    if slot.slot_state == "EMPTY":
        return slot
    if slot.recipe_version_id is not None or suggestion_recipe_version_id is None:
        return slot
    return PlanSlotV2(
        slot.slot_key,
        slot.planned_date,
        slot.meal_type,
        "ASSIGNED",
        suggestion_recipe_version_id,
        slot.manual_override,
        dict(slot.provenance),
    )


def clear_slot(slot: PlanSlotV2, *, reason: str = "manual_clear") -> PlanSlotV2:
    provenance = dict(slot.provenance)
    provenance.update({"clear_reason": reason, "explicit_empty": True})
    return PlanSlotV2(slot.slot_key, slot.planned_date, slot.meal_type, "EMPTY", None, slot.manual_override, provenance)


def per_person_portions(portions: list[SlotPortion]) -> dict[str, SlotPortion]:
    return {portion.person_id: portion for portion in portions}
