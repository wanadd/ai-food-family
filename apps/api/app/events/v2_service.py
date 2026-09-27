from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.models import CoreMembership, CorePermissionGrant, CorePerson
from app.events.v2_models import (
    Event, EventInvitation, EventMenuItem, EventMenuItemParticipant, EventMenuRevision,
    EventParticipant, EventParticipantFoodFact, EventShoppingDemand,
)
from app.recipes.v2_models import CanonicalRecipeIngredient, CanonicalRecipeVersion
from app.v2.authorization import AuthorizedContext
from app.v2.errors import error
from app.v2.uuid7 import uuid7_str
from app.food.wave2_domain import evaluate_safety


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _actor(context: AuthorizedContext) -> CorePerson:
    if context.actor_person is None:
        raise error("forbidden", 403)
    return context.actor_person


def _event(db: Session, event_id: str, context: AuthorizedContext, *, write: bool = False) -> Event:
    event = db.get(Event, event_id)
    if event is None:
        raise error("not_found", 404)
    actor = _actor(context)
    if event.organizer_person_id == actor.person_id:
        return event
    if write:
        raise error("forbidden", 403)
    participant = db.execute(select(EventParticipant).where(EventParticipant.event_id == event_id, EventParticipant.person_id == actor.person_id)).scalar_one_or_none()
    if participant is None:
        raise error("forbidden", 403)
    return event


def _touch(event: Event, expected_version: int | None = None) -> None:
    if expected_version is not None and event.version != expected_version:
        raise error("conflict", 409, details={"expected_version": expected_version, "actual_version": event.version})
    event.version += 1
    event.updated_at = _now()


def _participant_payload(db: Session, participant: EventParticipant) -> dict:
    fact = db.execute(select(EventParticipantFoodFact).where(EventParticipantFoodFact.participant_id == participant.participant_id)).scalar_one_or_none()
    return {
        "participant_id": participant.participant_id,
        "person_id": participant.person_id,
        "participant_kind": participant.participant_kind,
        "display_name": participant.display_name,
        "age_group": participant.age_group,
        "attendance_status": participant.attendance_status,
        "food_profile": {
            "knowledge_state": fact.knowledge_state if fact else "NOT_PROVIDED",
            "restrictions": fact.restrictions_json if fact else [],
        },
    }


def event_payload(db: Session, event: Event) -> dict:
    participants = db.execute(select(EventParticipant).where(EventParticipant.event_id == event.event_id).order_by(EventParticipant.created_at)).scalars().all()
    facts = db.execute(select(EventParticipantFoodFact).join(EventParticipant).where(EventParticipant.event_id == event.event_id)).scalars().all()
    accepted = [p for p in participants if p.attendance_status == "ACCEPTED"]
    known = {"KNOWN_NONE", "KNOWN_PRESENT"}
    complete = sum(1 for fact in facts if fact.knowledge_state in known)
    return {
        "event_id": event.event_id,
        "organizer_person_id": event.organizer_person_id,
        "household_id": event.household_id,
        "title": event.title,
        "event_type": event.event_type,
        "starts_at": event.starts_at,
        "ends_at": event.ends_at,
        "collaboration_mode": event.collaboration_mode,
        "status": event.status,
        "version": event.version,
        "headcount": {"expected": len([p for p in participants if p.attendance_status != "DECLINED"]), "confirmed": len(accepted)},
        "food_profile_completeness": {"accepted": len(accepted), "known": complete, "state": "COMPLETE" if complete >= len(accepted) else "INCOMPLETE"},
        "participants": [_participant_payload(db, p) for p in participants],
    }


def create_event(db: Session, context: AuthorizedContext, *, title: str, event_type: str, starts_at: datetime, ends_at: datetime | None, collaboration_mode: str, idempotency_key: str) -> dict:
    actor = _actor(context)
    existing = db.execute(select(Event).where(Event.creation_idempotency_key == idempotency_key)).scalar_one_or_none()
    if existing:
        if existing.organizer_person_id != actor.person_id:
            raise error("conflict", 409)
        return event_payload(db, existing)
    event = Event(event_id=uuid7_str(), organizer_person_id=actor.person_id, household_id=context.household_id, title=title, event_type=event_type, starts_at=starts_at, ends_at=ends_at, collaboration_mode=collaboration_mode, creation_idempotency_key=idempotency_key)
    db.add(event)
    db.flush()
    db.add(EventParticipant(participant_id=uuid7_str(), event_id=event.event_id, person_id=actor.person_id, participant_kind="ORGANIZER", display_name=actor.display_name or "Organizer", age_group="ADULT", attendance_status="ACCEPTED", created_by_person_id=actor.person_id))
    db.flush()
    return event_payload(db, event)


def update_event(db: Session, context: AuthorizedContext, event_id: str, data: dict) -> dict:
    event = _event(db, event_id, context, write=True)
    expected = data.pop("expected_version")
    _touch(event, expected)
    for key, value in data.items():
        if value is not None:
            setattr(event, key, value)
    db.flush()
    return event_payload(db, event)


_TRANSITIONS = {"DRAFT": {"OPEN", "PLANNING", "CANCELLED"}, "OPEN": {"PLANNING", "READY", "CANCELLED"}, "PLANNING": {"READY", "ACTIVE", "CANCELLED"}, "READY": {"ACTIVE", "CANCELLED"}, "ACTIVE": {"COMPLETED", "CANCELLED"}, "COMPLETED": set(), "CANCELLED": set()}


def transition_event(db: Session, context: AuthorizedContext, event_id: str, status: str, expected_version: int) -> dict:
    event = _event(db, event_id, context, write=True)
    if status != event.status and status not in _TRANSITIONS[event.status]:
        raise error("invalid_state_transition", 409, details={"from": event.status, "to": status})
    _touch(event, expected_version)
    event.status = status
    db.flush()
    return event_payload(db, event)


def add_participant(db: Session, context: AuthorizedContext, event_id: str, data: dict, idempotency_key: str | None) -> dict:
    event = _event(db, event_id, context, write=True)
    actor = _actor(context)
    if idempotency_key:
        existing = db.execute(select(EventParticipant).where(EventParticipant.event_id == event_id, EventParticipant.idempotency_key == idempotency_key)).scalar_one_or_none()
        if existing:
            return _participant_payload(db, existing)
    person_id = data.get("person_id")
    if person_id:
        if db.get(CorePerson, person_id) is None:
            raise error("not_found", 404)
        if db.execute(select(EventParticipant).where(EventParticipant.event_id == event_id, EventParticipant.person_id == person_id)).scalar_one_or_none():
            raise error("conflict", 409)
    participant = EventParticipant(participant_id=uuid7_str(), event_id=event_id, person_id=person_id, participant_kind="PERSON" if person_id else data["participant_kind"], display_name=data["display_name"], age_group=data["age_group"], attendance_status=data["attendance_status"], created_by_person_id=actor.person_id, idempotency_key=idempotency_key)
    db.add(participant)
    db.flush()
    _touch(event)
    return _participant_payload(db, participant)


def update_participant(db: Session, context: AuthorizedContext, event_id: str, participant_id: str, data: dict) -> dict:
    event = _event(db, event_id, context, write=True)
    participant = db.get(EventParticipant, participant_id)
    if participant is None or participant.event_id != event_id:
        raise error("not_found", 404)
    _touch(event, data.pop("expected_version"))
    for key, value in data.items():
        if value is not None:
            setattr(participant, key, value)
    db.flush()
    return _participant_payload(db, participant)


def create_invitation(db: Session, context: AuthorizedContext, event_id: str, expires_at: datetime | None, idempotency_key: str) -> dict:
    event = _event(db, event_id, context, write=True)
    actor = _actor(context)
    existing = db.execute(select(EventInvitation).where(EventInvitation.event_id == event_id, EventInvitation.creation_idempotency_key == idempotency_key)).scalar_one_or_none()
    if existing:
        return {"invitation_id": existing.invitation_id, "status": existing.status, "token": None, "invitation_url": None, "retry": True}
    raw = secrets.token_urlsafe(32)
    invitation = EventInvitation(invitation_id=uuid7_str(), event_id=event_id, created_by_person_id=actor.person_id, token_hash=_hash_token(raw), token_hint=raw[-8:], expires_at=expires_at, creation_idempotency_key=idempotency_key)
    db.add(invitation)
    db.flush()
    return {"invitation_id": invitation.invitation_id, "status": invitation.status, "token": raw, "invitation_url": f"/events/invite?token={raw}", "expires_at": expires_at}


def inspect_invitation(db: Session, token: str) -> dict:
    invitation = db.execute(select(EventInvitation).where(EventInvitation.token_hash == _hash_token(token))).scalar_one_or_none()
    if invitation is None or invitation.status in {"REVOKED", "EXPIRED"} or invitation.expires_at and invitation.expires_at <= _now():
        raise error("not_found", 404)
    event = db.get(Event, invitation.event_id)
    return {"invitation_id": invitation.invitation_id, "event_id": event.event_id, "title": event.title, "starts_at": event.starts_at, "status": invitation.status, "expires_at": invitation.expires_at}


def respond_invitation(db: Session, token: str, participants: list[dict], idempotency_key: str) -> dict:
    invitation = db.execute(select(EventInvitation).where(EventInvitation.token_hash == _hash_token(token))).scalar_one_or_none()
    if invitation is None or invitation.status in {"REVOKED", "EXPIRED"} or invitation.expires_at and invitation.expires_at <= _now():
        raise error("not_found", 404)
    if invitation.response_idempotency_key and invitation.status == "RESPONDED":
        if invitation.response_idempotency_key != idempotency_key:
            raise error("conflict", 409)
        rows = db.execute(select(EventParticipant).where(EventParticipant.invitation_id == invitation.invitation_id)).scalars().all()
        return {"invitation_id": invitation.invitation_id, "participants": [_participant_payload(db, row) for row in rows], "retry": True}
    event = db.get(Event, invitation.event_id)
    rows = []
    for data in participants:
        state = data["knowledge_state"]
        restrictions = data["restrictions"] if state == "KNOWN_PRESENT" else []
        participant = EventParticipant(participant_id=uuid7_str(), event_id=event.event_id, invitation_id=invitation.invitation_id, participant_kind="GUEST", display_name=data["display_name"], age_group=data["age_group"], attendance_status="ACCEPTED", idempotency_key=f"{idempotency_key}:{len(rows)}")
        db.add(participant)
        db.flush()
        db.add(EventParticipantFoodFact(fact_id=uuid7_str(), participant_id=participant.participant_id, knowledge_state=state, restrictions_json=restrictions, source_kind="EVENT_RSVP", provenance_json={"invitation_id": invitation.invitation_id}, idempotency_key=f"{idempotency_key}:food:{len(rows)}"))
        rows.append(participant)
    invitation.status = "RESPONDED"
    invitation.response_idempotency_key = idempotency_key
    invitation.responded_at = _now()
    db.flush()
    return {"invitation_id": invitation.invitation_id, "participants": [_participant_payload(db, row) for row in rows]}


def set_food_facts(db: Session, context: AuthorizedContext, event_id: str, participant_id: str, state: str, restrictions: list[dict], idempotency_key: str) -> dict:
    event = _event(db, event_id, context)
    participant = db.get(EventParticipant, participant_id)
    if participant is None or participant.event_id != event.event_id:
        raise error("not_found", 404)
    if state != "KNOWN_PRESENT":
        restrictions = []
    fact = db.execute(select(EventParticipantFoodFact).where(EventParticipantFoodFact.participant_id == participant_id)).scalar_one_or_none()
    if fact is None:
        fact = EventParticipantFoodFact(fact_id=uuid7_str(), participant_id=participant_id)
        db.add(fact)
    fact.knowledge_state = state
    fact.restrictions_json = restrictions
    fact.source_kind = "MANUAL"
    fact.provenance_json = {"event_id": event_id}
    fact.idempotency_key = idempotency_key
    db.flush()
    return _participant_payload(db, participant)


def create_menu_revision(db: Session, context: AuthorizedContext, event_id: str, expected_version: int, items: list[dict], idempotency_key: str) -> dict:
    event = _event(db, event_id, context, write=True)
    existing = db.execute(select(EventMenuRevision).where(EventMenuRevision.idempotency_key == idempotency_key)).scalar_one_or_none()
    if existing:
        return menu_payload(db, event, existing)
    _touch(event, expected_version)
    previous = db.execute(select(func.max(EventMenuRevision.revision_number)).where(EventMenuRevision.event_id == event_id)).scalar_one() or 0
    revision = EventMenuRevision(revision_id=uuid7_str(), event_id=event_id, revision_number=previous + 1, lifecycle_status="ACTIVE", expected_event_version=expected_version, created_by_person_id=_actor(context).person_id, idempotency_key=idempotency_key, provenance_json={"source": "EVENT"})
    db.add(revision)
    db.flush()
    for data in items:
        recipe_id = data.get("recipe_version_id")
        if recipe_id and db.get(CanonicalRecipeVersion, recipe_id) is None:
            raise error("not_found", 404, details={"recipe_version_id": recipe_id})
        safety_state, _ = evaluate_safety(profile_facts=[], food_relations=[], evidence_backed=False, process_known=False)
        item = EventMenuItem(menu_item_id=uuid7_str(), revision_id=revision.revision_id, slot_key=data["slot_key"], state="ASSIGNED" if recipe_id else "EMPTY", recipe_version_id=recipe_id, servings=data.get("servings"), safety_state=safety_state.value, coverage_json={"reason": "W2 evidence and participant food facts remain authoritative"}, provenance_json={"recipe_version_id": recipe_id})
        db.add(item)
        db.flush()
        for participant_id in data.get("participant_ids", []):
            participant = db.get(EventParticipant, participant_id)
            if participant is None or participant.event_id != event_id:
                raise error("not_found", 404)
            db.add(EventMenuItemParticipant(menu_item_id=item.menu_item_id, participant_id=participant_id))
    db.flush()
    return menu_payload(db, event, revision)


def menu_payload(db: Session, event: Event, revision: EventMenuRevision | None = None) -> dict:
    revision = revision or db.execute(select(EventMenuRevision).where(EventMenuRevision.event_id == event.event_id).order_by(EventMenuRevision.revision_number.desc())).scalars().first()
    if revision is None:
        return {"event_id": event.event_id, "revision": None, "items": []}
    items = db.execute(select(EventMenuItem).where(EventMenuItem.revision_id == revision.revision_id)).scalars().all()
    return {"event_id": event.event_id, "revision": {"revision_id": revision.revision_id, "revision_number": revision.revision_number, "lifecycle_status": revision.lifecycle_status}, "items": [{"menu_item_id": item.menu_item_id, "slot_key": item.slot_key, "state": item.state, "recipe_version_id": item.recipe_version_id, "servings": item.servings, "safety_state": item.safety_state} for item in items]}


def generate_shopping(db: Session, context: AuthorizedContext, event_id: str, items: list[dict], expected_version: int | None, idempotency_key: str) -> dict:
    event = _event(db, event_id, context, write=True)
    if expected_version is not None:
        _touch(event, expected_version)
    if not items:
        revision = db.execute(select(EventMenuRevision).where(EventMenuRevision.event_id == event_id).order_by(EventMenuRevision.revision_number.desc())).scalars().first()
        menu_items = db.execute(select(EventMenuItem).where(EventMenuItem.revision_id == revision.revision_id)).scalars().all() if revision else []
        items = []
        for menu_item in menu_items:
            if not menu_item.recipe_version_id:
                continue
            ingredients = db.execute(select(CanonicalRecipeIngredient).where(CanonicalRecipeIngredient.recipe_version_id == menu_item.recipe_version_id)).scalars().all()
            items.extend({"display_text": ingredient.shopping_name or ingredient.display_text, "quantity": ingredient.normalized_quantity or ingredient.quantity, "unit": ingredient.normalized_unit or ingredient.unit, "uncertainty": "KNOWN" if ingredient.quantity is not None else "UNKNOWN", "source_key": f"{menu_item.menu_item_id}:{ingredient.ingredient_id}"} for ingredient in ingredients)
    for data in items:
        existing = db.execute(select(EventShoppingDemand).where(EventShoppingDemand.event_id == event_id, EventShoppingDemand.source_key == data["source_key"])).scalar_one_or_none()
        if existing:
            continue
        db.add(EventShoppingDemand(demand_id=uuid7_str(), event_id=event_id, display_text=data["display_text"], quantity=data.get("quantity"), unit=data.get("unit"), uncertainty=data["uncertainty"], state="NEEDED", source_kind="EVENT_MENU", source_key=data["source_key"], provenance_json={"event_id": event_id, "idempotency_key": idempotency_key}))
    db.flush()
    demands = db.execute(select(EventShoppingDemand).where(EventShoppingDemand.event_id == event_id).order_by(EventShoppingDemand.created_at)).scalars().all()
    return {"event_id": event_id, "shopping_list_id": None, "items": [{"demand_id": d.demand_id, "display_text": d.display_text, "quantity": d.quantity, "unit": d.unit, "uncertainty": d.uncertainty, "state": d.state, "source_kind": d.source_kind} for d in demands]}
