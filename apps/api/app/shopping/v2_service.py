from __future__ import annotations
import hashlib, json
from datetime import date, datetime, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.models import CoreHousehold, CoreMembership, CorePermissionGrant, CorePerson
from app.planning.v2_models import Plan, PlanAssignment, PlanRevision, PlanSlot
from app.recipes.v2_models import CanonicalRecipeIngredient
from app.v2.authorization import AuthorizedContext
from app.v2.errors import error
from app.v2.uuid7 import uuid7_str
from .v2_models import (PantryInventory, PantryMovement, PurchaseEvent, ReceiptDocument,
    ReceiptLine, ReceiptProposal, ShoppingDemand, ShoppingItem, ShoppingList)


def _hash(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()


def authorize_household(db: Session, context: AuthorizedContext, household_id: str, *, write: bool = False) -> CoreHousehold:
    household = db.get(CoreHousehold, household_id)
    actor = context.actor_person or context.person
    if household is None or actor is None:
        raise error("forbidden", 403)
    member = db.scalar(select(CoreMembership.membership_id).where(
        CoreMembership.household_id == household_id, CoreMembership.person_id == actor.person_id,
        CoreMembership.membership_status == "active"))
    if member is None:
        raise error("forbidden", 403)
    return household


def authorize_scope(db: Session, context: AuthorizedContext, household_id: str | None, person_id: str | None, *, write: bool = False) -> None:
    if (household_id is None) == (person_id is None):
        raise error("forbidden", 403)
    if household_id is not None:
        authorize_household(db, context, household_id, write=write)
        return
    actor = context.actor_person or context.person
    if db.get(CorePerson, person_id) is None or actor is None:
        raise error("forbidden", 403)
    if actor.person_id == person_id:
        return
    now = datetime.now(timezone.utc)
    capability = "shopping.write" if write else "shopping.read"
    grant = db.scalar(select(CorePermissionGrant.permission_grant_id).where(
        CorePermissionGrant.subject_person_id == actor.person_id,
        CorePermissionGrant.target_person_id == person_id,
        CorePermissionGrant.capability == capability,
        CorePermissionGrant.grant_status == "active",
        CorePermissionGrant.effective_from <= now,
        (CorePermissionGrant.effective_to.is_(None) | (CorePermissionGrant.effective_to > now)),
    ))
    if grant is None:
        raise error("forbidden", 403)


def _list(db: Session, context: AuthorizedContext, household_id: str | None, *, person_id: str | None = None, write: bool = False) -> ShoppingList:
    authorize_scope(db, context, household_id, person_id, write=write)
    value = db.scalar(select(ShoppingList).where(ShoppingList.household_id == household_id, ShoppingList.person_id == person_id, ShoppingList.status == "ACTIVE"))
    if value is None:
        value = ShoppingList(shopping_list_id=uuid7_str(), household_id=household_id, person_id=person_id, idempotency_key="system-active")
        db.add(value)
        db.flush()
    return value


def _unit(value: str | None) -> str | None:
    if not value:
        return None
    return {"kilogram": "kg", "kilograms": "kg", "gram": "g", "grams": "g", "liter": "l", "liters": "l", "milliliter": "ml", "milliliters": "ml", "pcs": "piece"}.get(value.casefold().strip(), value.casefold().strip())


def _normal_quantity(quantity: float | None, unit: str | None) -> tuple[float | None, str | None, str | None]:
    unit = _unit(unit)
    if quantity is None or unit is None:
        return None, unit, "UNKNOWN"
    if unit in {"g", "kg", "ml", "l", "piece", "pcs"}:
        return quantity, unit, "KNOWN"
    return quantity, unit, "UNKNOWN"


def _payload(db: Session, shopping_list: ShoppingList) -> dict:
    demands = db.scalars(select(ShoppingDemand).where(ShoppingDemand.shopping_list_id == shopping_list.shopping_list_id)).all()
    items = db.scalars(select(ShoppingItem).where(ShoppingItem.shopping_list_id == shopping_list.shopping_list_id, ShoppingItem.state != "REMOVED")).all()
    return {
        "shopping_list_id": shopping_list.shopping_list_id,
        "owner_scope": "PERSON" if shopping_list.person_id else "HOUSEHOLD",
        "person_id": shopping_list.person_id,
        "household_id": shopping_list.household_id,
        "demands": [{"demand_id": d.demand_id, "display_text": d.display_text, "quantity": d.quantity, "unit": d.unit, "uncertainty": d.uncertainty, "source": d.source_kind, "plan_revision_id": d.plan_revision_id, "recipe_version_id": d.recipe_version_id} for d in demands],
        "items": [{"shopping_item_id": i.shopping_item_id, "display_text": i.display_text, "quantity": i.quantity, "unit": i.unit, "uncertainty": i.uncertainty, "category": i.category, "state": i.state, "source": i.source_kind} for i in items],
    }


def list_shopping(db: Session, context: AuthorizedContext, household_id: str | None = None, *, person_id: str | None = None) -> dict:
    return _payload(db, _list(db, context, household_id, person_id=person_id))


def add_manual_item(db: Session, context: AuthorizedContext, household_id: str | None = None, *, person_id: str | None = None, idempotency_key: str, request: dict) -> dict:
    shopping_list = _list(db, context, household_id, person_id=person_id, write=True)
    existing = db.scalar(select(ShoppingItem).where(ShoppingItem.shopping_list_id == shopping_list.shopping_list_id, ShoppingItem.idempotency_key == idempotency_key))
    if existing:
        return _payload(db, shopping_list)
    quantity, unit, uncertainty = _normal_quantity(request.get("quantity"), request.get("unit"))
    db.add(ShoppingItem(shopping_item_id=uuid7_str(), shopping_list_id=shopping_list.shopping_list_id, display_text=request["display_text"].strip(), quantity=quantity, unit=unit, uncertainty=uncertainty, category=request.get("category"), state="NEEDED", source_kind="MANUAL", provenance_json={"request_hash": _hash(request)}, idempotency_key=idempotency_key))
    db.commit()
    return _payload(db, shopping_list)


def derive_from_revision(db: Session, context: AuthorizedContext, household_id: str | None, revision_id: str, *, person_id: str | None = None, idempotency_key: str) -> dict:
    shopping_list = _list(db, context, household_id, person_id=person_id, write=True)
    revision = db.get(PlanRevision, revision_id)
    plan = db.get(Plan, revision.plan_id) if revision else None
    if revision is None or plan is None or plan.household_id != household_id or plan.person_id != person_id:
        raise error("forbidden", 403)
    prior = db.scalar(select(ShoppingDemand).where(ShoppingDemand.shopping_list_id == shopping_list.shopping_list_id, ShoppingDemand.source_key == f"plan:{revision_id}"))
    if prior:
        return _payload(db, shopping_list)
    slots = db.scalars(select(PlanSlot).where(PlanSlot.revision_id == revision_id)).all()
    for slot in slots:
        if slot.slot_state != "ASSIGNED":
            continue
        assignment = db.scalar(select(PlanAssignment).where(PlanAssignment.slot_id == slot.slot_id))
        if assignment is None:
            continue
        ingredients = db.scalars(select(CanonicalRecipeIngredient).where(CanonicalRecipeIngredient.recipe_version_id == assignment.recipe_version_id).order_by(CanonicalRecipeIngredient.sort_order)).all()
        for index, ingredient in enumerate(ingredients):
            quantity, unit, uncertainty = _normal_quantity(ingredient.normalized_quantity if ingredient.normalized_quantity is not None else ingredient.quantity, ingredient.normalized_unit or ingredient.unit)
            if ingredient.optional:
                uncertainty = "OPTIONAL"
            if ingredient.quantity_mode in {"TO_TASTE", "UNKNOWN"}:
                uncertainty = "TO_TASTE" if ingredient.quantity_mode == "TO_TASTE" else "UNKNOWN"
                quantity = None
            source_key = f"plan:{revision_id}:{slot.slot_id}:{index}"
            db.add(ShoppingDemand(demand_id=uuid7_str(), shopping_list_id=shopping_list.shopping_list_id, plan_revision_id=revision_id, plan_slot_id=slot.slot_id, recipe_version_id=assignment.recipe_version_id, display_text=ingredient.shopping_name or ingredient.display_text, quantity=quantity, unit=unit, uncertainty=uncertainty, source_kind="PLAN", source_key=source_key, idempotency_key=f"{idempotency_key}:{source_key}", provenance_json={"plan_revision_id": revision_id, "recipe_version_id": assignment.recipe_version_id}))
    db.add(ShoppingDemand(demand_id=uuid7_str(), shopping_list_id=shopping_list.shopping_list_id, source_kind="OTHER", source_key=f"plan:{revision_id}", idempotency_key=idempotency_key, display_text="__revision_marker__", uncertainty="UNKNOWN", provenance_json={"idempotency_key": idempotency_key}))
    db.commit()
    return _payload(db, shopping_list)


def purchase(db: Session, context: AuthorizedContext, household_id: str | None, item_id: str, *, person_id: str | None = None, idempotency_key: str, add_to_pantry: bool = False) -> dict:
    item = db.scalar(select(ShoppingItem).where(ShoppingItem.shopping_item_id == item_id).with_for_update())
    if item is None:
        raise error("not_found", 404)
    shopping_list = db.get(ShoppingList, item.shopping_list_id)
    if shopping_list is None:
        raise error("not_found", 404)
    if household_id is not None and shopping_list.household_id != household_id:
        raise error("forbidden", 403)
    if person_id is not None and shopping_list.person_id != person_id:
        raise error("forbidden", 403)
    authorize_scope(db, context, shopping_list.household_id, shopping_list.person_id, write=True)
    prior = db.scalar(select(PurchaseEvent).where(PurchaseEvent.shopping_item_id == item_id, PurchaseEvent.idempotency_key == idempotency_key))
    if prior:
        return _payload(db, shopping_list)
    item.state = "PURCHASED"
    db.add(PurchaseEvent(purchase_event_id=uuid7_str(), shopping_item_id=item.shopping_item_id, household_id=shopping_list.household_id, quantity=item.quantity, unit=item.unit, idempotency_key=idempotency_key, provenance_json={"source": "shopping_purchase", "pantry_effect": add_to_pantry}))
    if add_to_pantry:
        _apply_pantry(db, shopping_list.household_id, shopping_list.person_id, item.display_text, item.quantity, item.unit, "SHOPPING_PURCHASE", idempotency_key, {"shopping_item_id": item_id})
    db.commit()
    return _payload(db, shopping_list)


def remove_item(db: Session, context: AuthorizedContext, item_id: str, *, idempotency_key: str) -> dict:
    item = db.scalar(select(ShoppingItem).where(ShoppingItem.shopping_item_id == item_id).with_for_update())
    if item is None:
        raise error("not_found", 404)
    shopping_list = db.get(ShoppingList, item.shopping_list_id)
    if shopping_list is None:
        raise error("not_found", 404)
    authorize_scope(db, context, shopping_list.household_id, shopping_list.person_id, write=True)
    if item.state != "REMOVED":
        item.state = "REMOVED"
        item.provenance_json = {**(item.provenance_json or {}), "removed_idempotency_key": idempotency_key}
        db.commit()
    return _payload(db, shopping_list)


def _apply_pantry(db: Session, household_id: str | None, person_id: str | None, display_text: str, quantity: float | None, unit: str | None, kind: str, key: str, provenance: dict) -> PantryInventory:
    inventory = db.scalar(select(PantryInventory).where(PantryInventory.household_id == household_id, PantryInventory.person_id == person_id, PantryInventory.display_text == display_text, PantryInventory.unit == unit).with_for_update())
    if inventory is None:
        inventory = PantryInventory(pantry_inventory_id=uuid7_str(), household_id=household_id, person_id=person_id, display_text=display_text, quantity=quantity, unit=unit, uncertainty="KNOWN" if quantity is not None and unit else "UNKNOWN", provenance_json=provenance)
        db.add(inventory); db.flush()
    elif quantity is not None and inventory.quantity is not None:
        inventory.quantity += quantity
    db.add(PantryMovement(pantry_movement_id=uuid7_str(), pantry_inventory_id=inventory.pantry_inventory_id, household_id=household_id, movement_kind=kind, quantity_delta=quantity, unit=unit, idempotency_key=key, provenance_json=provenance))
    return inventory


def list_pantry(db: Session, context: AuthorizedContext, household_id: str | None = None, *, person_id: str | None = None) -> dict:
    authorize_scope(db, context, household_id, person_id)
    rows = db.scalars(select(PantryInventory).where(PantryInventory.household_id == household_id, PantryInventory.person_id == person_id).order_by(PantryInventory.display_text)).all()
    return {"owner_scope": "PERSON" if person_id else "HOUSEHOLD", "person_id": person_id, "household_id": household_id, "items": [{"pantry_inventory_id": r.pantry_inventory_id, "display_text": r.display_text, "quantity": r.quantity, "unit": r.unit, "uncertainty": r.uncertainty, "lot_code": r.lot_code, "expiry_date": r.expiry_date.isoformat() if r.expiry_date else None} for r in rows]}


def adjust_pantry(db: Session, context: AuthorizedContext, household_id: str | None = None, *, person_id: str | None = None, idempotency_key: str, request: dict) -> dict:
    authorize_scope(db, context, household_id, person_id, write=True)
    prior = db.scalar(select(PantryMovement).join(PantryInventory).where(PantryInventory.household_id == household_id, PantryInventory.person_id == person_id, PantryMovement.idempotency_key == idempotency_key))
    if prior:
        return list_pantry(db, context, household_id, person_id=person_id)
    if request.get("quantity_delta") is None:
        raise error("validation_error", 422, details={"quantity_delta": "required"})
    inventory = _apply_pantry(db, household_id, person_id, request["display_text"], request["quantity_delta"], _unit(request.get("unit")), "MANUAL", idempotency_key, {"source": "manual"})
    if inventory.quantity is not None and inventory.quantity < 0:
        db.rollback()
        raise error("validation_error", 422, details={"quantity_delta": "negative stock"})
    db.commit()
    return list_pantry(db, context, household_id, person_id=person_id)


def create_receipt(db: Session, context: AuthorizedContext, household_id: str | None = None, *, person_id: str | None = None, idempotency_key: str, request: dict) -> dict:
    authorize_scope(db, context, household_id, person_id, write=True)
    document = db.scalar(select(ReceiptDocument).where(ReceiptDocument.household_id == household_id, ReceiptDocument.person_id == person_id, ReceiptDocument.idempotency_key == idempotency_key))
    if document:
        proposal = db.scalar(select(ReceiptProposal).where(ReceiptProposal.receipt_document_id == document.receipt_document_id))
        return {"receipt_document_id": document.receipt_document_id, "receipt_proposal_id": proposal.receipt_proposal_id if proposal else None, "state": document.state}
    document = ReceiptDocument(receipt_document_id=uuid7_str(), household_id=household_id, person_id=person_id, media_asset_id=request.get("media_asset_id"), provider_metadata_json=request.get("provider_metadata") or {}, state="REVIEW", idempotency_key=idempotency_key)
    db.add(document); db.flush()
    proposal = ReceiptProposal(receipt_proposal_id=uuid7_str(), receipt_document_id=document.receipt_document_id, household_id=household_id, state="REVIEW_REQUIRED", confidence="UNKNOWN", idempotency_key=f"{idempotency_key}:proposal")
    db.add(proposal); db.flush()
    for position, line in enumerate(request.get("lines", [])):
        db.add(ReceiptLine(receipt_line_id=uuid7_str(), receipt_proposal_id=proposal.receipt_proposal_id, household_id=household_id, position=position, raw_text=str(line.get("raw_text", "")), confidence=str(line.get("confidence", "UNKNOWN")), state="UNRESOLVED", quantity=line.get("quantity"), unit=_unit(line.get("unit")), provenance_json={"source": "observation"}))
    db.commit()
    return {"receipt_document_id": document.receipt_document_id, "receipt_proposal_id": proposal.receipt_proposal_id, "state": document.state}


def accept_receipt(db: Session, context: AuthorizedContext, household_id: str | None, receipt_id: str, proposal_id: str, *, person_id: str | None = None, idempotency_key: str, line_ids: list[str]) -> dict:
    document = db.get(ReceiptDocument, receipt_id)
    if document is None:
        raise error("not_found", 404)
    if household_id is not None and document.household_id != household_id:
        raise error("forbidden", 403)
    if person_id is not None and document.person_id != person_id:
        raise error("forbidden", 403)
    authorize_scope(db, context, document.household_id, document.person_id, write=True)
    proposal = db.scalar(select(ReceiptProposal).where(ReceiptProposal.receipt_proposal_id == proposal_id, ReceiptProposal.receipt_document_id == receipt_id).with_for_update())
    if proposal is None:
        raise error("not_found", 404)
    if proposal.state == "VERIFIED":
        return {"receipt_proposal_id": proposal_id, "state": "VERIFIED", "replayed": True}
    prior = db.scalar(select(PantryMovement).join(PantryInventory).where(PantryInventory.household_id == document.household_id, PantryInventory.person_id == document.person_id, PantryMovement.idempotency_key == idempotency_key))
    if prior:
        return {"receipt_proposal_id": proposal_id, "state": "VERIFIED", "replayed": True}
    lines = db.scalars(select(ReceiptLine).where(ReceiptLine.receipt_proposal_id == proposal_id, ReceiptLine.receipt_line_id.in_(line_ids)).with_for_update()).all()
    if len(lines) != len(set(line_ids)) or any(line.state != "UNRESOLVED" for line in lines):
        raise error("conflict", 409)
    for line in lines:
        if line.confidence not in {"HIGH", "MEDIUM"}:
            raise error("validation_error", 422, details={"line": "review required"})
        line.state = "CONFIRMED"
        _apply_pantry(db, document.household_id, document.person_id, line.raw_text, line.quantity, line.unit, "RECEIPT_CONFIRMATION", f"{idempotency_key}:{line.receipt_line_id}", {"receipt_id": receipt_id, "proposal_id": proposal_id, "line_id": line.receipt_line_id})
    proposal.state = "VERIFIED"; proposal.confidence = "HIGH"
    document.state = "CONFIRMED"
    db.commit()
    return {"receipt_proposal_id": proposal_id, "state": "VERIFIED", "confirmed_lines": line_ids}
