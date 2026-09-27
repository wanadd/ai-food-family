from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.models import CoreHousehold, CoreMembership, CorePermissionGrant, CorePerson
from app.recipes.v2_models import CanonicalRecipeVersion
from app.v2.authorization import AuthorizedContext
from app.v2.errors import error
from app.v2.uuid7 import uuid7_str

from .v2_models import Plan, PlanAssignment, PlanParticipant, PlanPortion, PlanRevision, PlanSlot


SAFETY_ORDER = {"SAFE": 0, "WARN": 1, "UNKNOWN": 2, "ESCALATE": 3, "BLOCK": 4}


def fingerprint(payload: Any) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode()
    return hashlib.sha256(raw).hexdigest()


def _actor_can_access_person(db: Session, context: AuthorizedContext, person_id: str, capability: str) -> bool:
    actor = context.actor_person or context.person
    if actor is None:
        return False
    if actor.person_id == person_id:
        return True
    now = datetime.now(timezone.utc)
    return db.scalar(
        select(CorePermissionGrant.permission_grant_id).where(
            CorePermissionGrant.subject_person_id == actor.person_id,
            CorePermissionGrant.target_person_id == person_id,
            CorePermissionGrant.capability == capability,
            CorePermissionGrant.grant_status == "active",
            CorePermissionGrant.effective_from <= now,
            (CorePermissionGrant.effective_to.is_(None) | (CorePermissionGrant.effective_to > now)),
        )
    ) is not None


def _actor_in_household(db: Session, context: AuthorizedContext, household_id: str) -> bool:
    actor = context.actor_person or context.person
    if actor is None:
        return False
    return db.scalar(
        select(CoreMembership.membership_id).where(
            CoreMembership.person_id == actor.person_id,
            CoreMembership.household_id == household_id,
            CoreMembership.membership_status == "active",
        )
    ) is not None


def authorize_plan_owner(db: Session, context: AuthorizedContext, plan: Plan, *, write: bool = False) -> None:
    capability = "planning.write" if write else "planning.read"
    if plan.person_id is not None:
        if not _actor_can_access_person(db, context, plan.person_id, capability):
            raise error("forbidden", 403)
        return
    if plan.household_id is not None:
        if not _actor_in_household(db, context, plan.household_id):
            raise error("forbidden", 403)
        return
    raise error("forbidden", 403)


def get_plan(db: Session, context: AuthorizedContext, plan_id: str, *, write: bool = False) -> Plan:
    plan = db.get(Plan, plan_id)
    if plan is None:
        raise error("not_found", 404)
    authorize_plan_owner(db, context, plan, write=write)
    return plan


def _version(db: Session, recipe_version_id: str) -> CanonicalRecipeVersion:
    version = db.get(CanonicalRecipeVersion, recipe_version_id)
    if version is None or version.lifecycle_status != "PUBLISHED":
        raise error("validation_error", 422, details={"recipe_version_id": "published RecipeVersion required"})
    return version


def recipe_safety_state(version: CanonicalRecipeVersion) -> str:
    claims = version.safety_claims_json or {}
    payload = version.gold_v3_payload_json or {}
    state = claims.get("decision") or claims.get("state") or payload.get("safety_state")
    state = str(state or "UNKNOWN").upper()
    return state if state in SAFETY_ORDER else "UNKNOWN"


def _aggregate_safety(states: list[str]) -> str:
    if not states:
        return "UNKNOWN"
    return max(states, key=lambda state: SAFETY_ORDER.get(state, SAFETY_ORDER["UNKNOWN"]))


def _validate_candidate(db: Session, plan: Plan, recipe_version_id: str, participant_ids: list[str]) -> tuple[CanonicalRecipeVersion, str]:
    version = _version(db, recipe_version_id)
    state = recipe_safety_state(version)
    if plan.person_id is not None and participant_ids and plan.person_id not in participant_ids:
        raise error("forbidden", 403)
    if plan.household_id is not None and participant_ids:
        member_ids = set(
            db.scalars(
                select(CoreMembership.person_id).where(
                    CoreMembership.household_id == plan.household_id,
                    CoreMembership.membership_status == "active",
                    CoreMembership.person_id.in_(participant_ids),
                )
            ).all()
        )
        if member_ids != set(participant_ids):
            raise error("forbidden", 403)
    if state in {"BLOCK", "UNKNOWN", "ESCALATE"}:
        raise error("safety_block" if state == "BLOCK" else "safety_unknown", 422, details={"decision": state})
    return version, state


def _active_revision(db: Session, plan_id: str) -> PlanRevision | None:
    return db.scalar(
        select(PlanRevision)
        .where(PlanRevision.plan_id == plan_id, PlanRevision.lifecycle_status == "ACTIVE")
        .with_for_update()
        .order_by(PlanRevision.revision_number.desc())
    )


def _revision_slots(db: Session, revision_id: str) -> list[PlanSlot]:
    return list(db.scalars(select(PlanSlot).where(PlanSlot.revision_id == revision_id).order_by(PlanSlot.planned_date, PlanSlot.slot_key)).all())


def _revision_payload(db: Session, plan: Plan, revision: PlanRevision | None) -> dict[str, Any]:
    if revision is None:
        return {"plan_id": plan.plan_id, "owner_scope": "PERSON" if plan.person_id else "HOUSEHOLD", "person_id": plan.person_id, "household_id": plan.household_id, "active_revision": None, "slots": []}
    slots = []
    for slot in _revision_slots(db, revision.revision_id):
        assignment = db.scalar(select(PlanAssignment).where(PlanAssignment.slot_id == slot.slot_id))
        participants = db.scalars(select(PlanParticipant).where(PlanParticipant.slot_id == slot.slot_id)).all()
        portions = db.scalars(select(PlanPortion).where(PlanPortion.slot_id == slot.slot_id)).all()
        slots.append({
            "slot_id": slot.slot_id,
            "slot_key": slot.slot_key,
            "date": slot.planned_date.isoformat(),
            "meal_type": slot.meal_type,
            "state": slot.slot_state,
            "recipe_version_id": assignment.recipe_version_id if assignment else None,
            "safety_state": assignment.safety_state if assignment else None,
            "manual": bool(assignment and assignment.source_kind == "MANUAL"),
            "origin": assignment.source_kind if assignment else None,
            "participants": [{"person_id": item.person_id, "state": item.participation_state} for item in participants],
            "portions": [{"person_id": item.person_id, "value": item.portion_value, "unit": item.portion_unit, "source": item.source_kind} for item in portions],
        })
    return {
        "plan_id": plan.plan_id,
        "owner_scope": "PERSON" if plan.person_id else "HOUSEHOLD",
        "person_id": plan.person_id,
        "household_id": plan.household_id,
        "active_revision": {"revision_id": revision.revision_id, "number": revision.revision_number, "status": revision.lifecycle_status, "source": revision.source_kind, "safety": revision.safety_snapshot_json},
        "slots": slots,
    }


def create_plan(db: Session, context: AuthorizedContext, *, owner_scope: str, person_id: str | None, household_id: str | None, idempotency_key: str, request: dict[str, Any]) -> dict[str, Any]:
    scope = owner_scope.upper()
    if scope not in {"PERSON", "HOUSEHOLD"}:
        raise error("validation_error", 422, details={"owner_scope": "PERSON or HOUSEHOLD required"})
    if (scope == "PERSON") != bool(person_id) or (scope == "HOUSEHOLD") != bool(household_id):
        raise error("validation_error", 422, details={"owner_scope": "exactly one owner is required"})
    if person_id is not None:
        if db.get(CorePerson, person_id) is None or not _actor_can_access_person(db, context, person_id, "planning.write"):
            raise error("forbidden", 403)
    if household_id is not None:
        if db.get(CoreHousehold, household_id) is None:
            raise error("not_found", 404)
        if not _actor_in_household(db, context, household_id):
            raise error("forbidden", 403)
    existing = db.scalar(select(Plan).where(Plan.idempotency_key == idempotency_key))
    request_hash = fingerprint(request)
    if existing is not None:
        if existing.request_fingerprint != request_hash:
            raise error("conflict", 409)
        authorize_plan_owner(db, context, existing, write=True)
        return _revision_payload(db, existing, _active_revision(db, existing.plan_id))
    plan = Plan(plan_id=uuid7_str(), person_id=person_id, household_id=household_id, idempotency_key=idempotency_key, request_fingerprint=request_hash)
    db.add(plan)
    db.flush()
    db.commit()
    return _revision_payload(db, plan, None)


def create_revision(db: Session, context: AuthorizedContext, plan: Plan, *, source_kind: str, idempotency_key: str, request: dict[str, Any], slots: list[dict[str, Any]], expected_revision_id: str | None = None) -> dict[str, Any]:
    authorize_plan_owner(db, context, plan, write=True)
    request_hash = fingerprint(request)
    existing = db.scalar(select(PlanRevision).where(PlanRevision.idempotency_key == idempotency_key))
    if existing is not None:
        if existing.input_snapshot_json.get("request_hash") != request_hash:
            raise error("conflict", 409)
        return _revision_payload(db, plan, existing)
    previous = _active_revision(db, plan.plan_id)
    if expected_revision_id is not None and (previous is None or previous.revision_id != expected_revision_id):
        raise error("conflict", 409, details={"reason": "stale_revision"})
    revision_number = (previous.revision_number + 1) if previous else 1
    revision = PlanRevision(
        revision_id=uuid7_str(), plan_id=plan.plan_id, revision_number=revision_number, source_kind=source_kind,
        lifecycle_status="ACTIVE", actor_person_id=context.actor_person.person_id if context.actor_person else None,
        input_snapshot_json={"request_hash": request_hash, "request": request}, safety_snapshot_json={}, idempotency_key=idempotency_key,
        activated_at=datetime.now(timezone.utc),
    )
    db.add(revision)
    db.flush()
    safety_states: list[str] = []
    for item in slots:
        state = str(item.get("state") or ("ASSIGNED" if item.get("recipe_version_id") else "FREE")).upper()
        if state not in {"ASSIGNED", "EMPTY", "FREE", "CANCELLED"}:
            raise error("validation_error", 422, details={"state": state})
        participant_ids = [str(value["person_id"]) for value in item.get("participants", [])]
        if plan.person_id and not participant_ids:
            participant_ids = [plan.person_id]
        if plan.person_id and any(value != plan.person_id for value in participant_ids):
            raise error("forbidden", 403)
        recipe_version_id = item.get("recipe_version_id")
        assignment = None
        safety_state = None
        if state == "ASSIGNED":
            if not recipe_version_id:
                raise error("validation_error", 422, details={"recipe_version_id": "required for ASSIGNED"})
            _, safety_state = _validate_candidate(db, plan, str(recipe_version_id), participant_ids)
            safety_states.append(safety_state)
        elif recipe_version_id:
            raise error("validation_error", 422, details={"recipe_version_id": "only valid for ASSIGNED"})
        slot = PlanSlot(slot_id=uuid7_str(), revision_id=revision.revision_id, slot_key=str(item["slot_key"]), planned_date=item["planned_date"], meal_type=str(item["meal_type"]), slot_state=state, recipe_version_id=None, manual_override=source_kind == "MANUAL", provenance_json=item.get("provenance") or {})
        db.add(slot)
        db.flush()
        if state == "ASSIGNED":
            assignment = PlanAssignment(assignment_id=uuid7_str(), slot_id=slot.slot_id, recipe_version_id=str(recipe_version_id), source_kind="GENERATED" if source_kind == "AI_GENERATED" else source_kind, safety_state=safety_state or "UNKNOWN", provenance_json={"revision_id": revision.revision_id}, idempotency_key=f"{idempotency_key}:{slot.slot_key}")
            db.add(assignment)
        for participant in item.get("participants", []):
            db.add(PlanParticipant(slot_id=slot.slot_id, person_id=str(participant["person_id"]), participation_state=str(participant.get("state", "PARTICIPATING"))))
        for portion in item.get("portions", []):
            db.add(PlanPortion(slot_id=slot.slot_id, person_id=str(portion["person_id"]), portion_value=portion.get("value"), portion_unit=portion.get("unit"), source_kind=str(portion.get("source", "UNKNOWN"))))
    if previous is not None:
        previous.lifecycle_status = "SUPERSEDED"
        previous.superseded_at = datetime.now(timezone.utc)
    revision.safety_snapshot_json = {"states": safety_states, "aggregate": _aggregate_safety(safety_states)}
    db.commit()
    return _revision_payload(db, plan, revision)
