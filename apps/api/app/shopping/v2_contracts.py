from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

@dataclass(frozen=True)
class ShoppingDemandV2:
    display_text: str
    quantity: float | None
    unit: str | None
    source_kind: str
    plan_revision_id: str | None = None
    plan_slot_id: str | None = None
    recipe_version_id: str | None = None
    participant_person_id: str | None = None
    product_requirement: dict[str, Any] = field(default_factory=dict)
    @property
    def quantity_state(self) -> str:
        return "KNOWN" if self.quantity is not None and self.unit else "UNKNOWN"

def can_merge_demands(left: ShoppingDemandV2, right: ShoppingDemandV2) -> bool:
    return left.unit == right.unit and left.product_requirement == right.product_requirement and left.source_kind != "MANUAL" and right.source_kind != "MANUAL"

def merge_demands(left: ShoppingDemandV2, right: ShoppingDemandV2) -> ShoppingDemandV2 | None:
    if not can_merge_demands(left, right):
        return None
    quantity = left.quantity + right.quantity if left.quantity is not None and right.quantity is not None else None
    return ShoppingDemandV2(left.display_text, quantity, left.unit, "PLAN", left.plan_revision_id, left.plan_slot_id, left.recipe_version_id, left.participant_person_id, left.product_requirement)

def checked_item_proves_pantry(item_state: str) -> bool:
    return False

@dataclass(frozen=True)
class PantryMovementV2:
    movement_type: str
    quantity_delta: float | None
    idempotency_key: str

@dataclass(frozen=True)
class ReceiptProposalV2:
    extraction_kind: str
    status: str = "REVIEW_REQUIRED"
    confidence: str = "UNKNOWN"
    verified: bool = False

def ocr_is_verified_purchase(proposal: ReceiptProposalV2) -> bool:
    return proposal.verified and proposal.status == "VERIFIED"

def expiration_state(expiration_date: Any | None) -> str:
    return "KNOWN" if expiration_date is not None else "UNKNOWN"
