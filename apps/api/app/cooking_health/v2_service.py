from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.models import CoreHousehold, CoreMembership, CorePermissionGrant, CorePerson
from app.planning.v2_models import Plan, PlanRevision, PlanSlot
from app.v2.authorization import AuthorizedContext
from app.v2.errors import error
from app.v2.uuid7 import uuid7_str

from .v2_models import CookingEvent, CookingSession, ConsumptionEvent, ConsumptionItem, HealthDeviation, HealthProjection, PreparedFood


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _household(db: Session, context: AuthorizedContext, household_id: str) -> CoreHousehold:
    household = db.get(CoreHousehold, household_id)
    actor = context.actor_person or context.person
    if household is None or actor is None:
        raise error("forbidden", 403)
    member = db.scalar(select(CoreMembership.membership_id).where(
        CoreMembership.household_id == household_id,
        CoreMembership.person_id == actor.person_id,
        CoreMembership.membership_status == "active",
    ))
    if member is None:
        raise error("forbidden", 403)
    return household


def _person(db: Session, context: AuthorizedContext, person_id: str, household_id: str | None, *, capability: str) -> tuple[CorePerson, str]:
    target = db.get(CorePerson, person_id)
    actor = context.actor_person or context.person
    if target is None or actor is None:
        raise error("forbidden", 403)
    member_query = select(CoreMembership).where(CoreMembership.person_id == person_id, CoreMembership.membership_status == "active")
    if household_id:
        member_query = member_query.where(CoreMembership.household_id == household_id)
    membership = db.scalar(member_query.order_by(CoreMembership.active_from.desc()))
    if membership is None:
        raise error("forbidden", 403)
    if actor.person_id != person_id:
        grant = db.scalar(select(CorePermissionGrant.permission_grant_id).where(
            CorePermissionGrant.subject_person_id == actor.person_id,
            CorePermissionGrant.target_person_id == person_id,
            or_(CorePermissionGrant.household_id == membership.household_id, CorePermissionGrant.household_id.is_(None)),
            func.lower(CorePermissionGrant.domain_scope).in_(["consumption", "health", "person", "core"]),
            CorePermissionGrant.capability.in_([capability, "core.person.read"]),
            CorePermissionGrant.grant_status == "active",
        ))
        if grant is None:
            raise error("forbidden", 403)
    return target, membership.household_id


def _slot_context(db: Session, slot_id: str | None, household_id: str) -> PlanSlot | None:
    if slot_id is None:
        return None
    slot = db.get(PlanSlot, slot_id)
    revision = db.get(PlanRevision, slot.revision_id) if slot else None
    plan = db.get(Plan, revision.plan_id) if revision else None
    if slot is None or plan is None or plan.household_id != household_id:
        raise error("forbidden", 403)
    return slot


def _session_payload(session: CookingSession, prepared: PreparedFood | None = None) -> dict[str, Any]:
    return {
        "cooking_session_id": session.cooking_session_id,
        "household_id": session.household_id,
        "recipe_version_id": session.recipe_version_id,
        "plan_slot_id": session.plan_slot_id,
        "state": session.state,
        "started_at": session.started_at.isoformat() if session.started_at else None,
        "completed_at": session.completed_at.isoformat() if session.completed_at else None,
        "prepared_food": None if prepared is None else {
            "prepared_food_id": prepared.prepared_food_id,
            "yield_quantity": prepared.yield_quantity,
            "yield_unit": prepared.yield_unit,
            "yield_servings": prepared.yield_servings,
            "state": prepared.state,
        },
    }


def start_cooking(db: Session, context: AuthorizedContext, household_id: str, *, idempotency_key: str, request: dict[str, Any]) -> dict[str, Any]:
    _household(db, context, household_id)
    prior = db.scalar(select(CookingSession).where(CookingSession.household_id == household_id, CookingSession.idempotency_key == idempotency_key))
    if prior:
        return _session_payload(prior, db.scalar(select(PreparedFood).where(PreparedFood.session_id == prior.cooking_session_id)))
    slot = _slot_context(db, request.get("plan_slot_id"), household_id)
    recipe_version_id = request.get("recipe_version_id") or (slot.recipe_version_id if slot else None)
    if slot and recipe_version_id and slot.recipe_version_id and recipe_version_id != slot.recipe_version_id:
        raise error("conflict", 409, details={"reason": "recipe_version_does_not_match_plan_slot"})
    now = _now()
    session = CookingSession(
        cooking_session_id=uuid7_str(), household_id=household_id, recipe_version_id=recipe_version_id,
        plan_slot_id=slot.slot_id if slot else None, state="STARTED", started_at=now,
        provenance_json={"source": "v2_cooking_start", "request": request}, idempotency_key=idempotency_key,
    )
    db.add(session)
    db.add(CookingEvent(cooking_event_id=uuid7_str(), session_id=session.cooking_session_id, household_id=household_id, event_kind="STARTED", occurred_at=now, payload_json={"recipe_version_id": recipe_version_id, "plan_slot_id": session.plan_slot_id}, idempotency_key=f"{idempotency_key}:started"))
    db.commit()
    return _session_payload(session)


def complete_cooking(db: Session, context: AuthorizedContext, session_id: str, *, idempotency_key: str, request: dict[str, Any]) -> dict[str, Any]:
    session = db.scalar(select(CookingSession).where(CookingSession.cooking_session_id == session_id).with_for_update())
    if session is None:
        raise error("not_found", 404)
    _household(db, context, session.household_id)
    if session.state == "COMPLETED":
        return _session_payload(session, db.scalar(select(PreparedFood).where(PreparedFood.session_id == session_id)))
    if session.state != "STARTED":
        raise error("conflict", 409, details={"reason": "cooking_session_not_started"})
    existing_event = db.scalar(select(CookingEvent).where(CookingEvent.household_id == session.household_id, CookingEvent.idempotency_key == idempotency_key))
    if existing_event:
        return _session_payload(session, db.scalar(select(PreparedFood).where(PreparedFood.session_id == session_id)))
    quantity = request.get("yield_quantity")
    servings = request.get("yield_servings")
    if quantity is not None and quantity <= 0 or servings is not None and servings <= 0:
        raise error("validation_error", 422, details={"yield": "must be positive"})
    now = _now()
    session.state = "COMPLETED"
    session.completed_at = now
    prepared = PreparedFood(
        prepared_food_id=uuid7_str(), session_id=session.cooking_session_id, household_id=session.household_id,
        recipe_version_id=session.recipe_version_id, display_name=request.get("display_name"),
        yield_quantity=quantity, yield_unit=request.get("yield_unit"), yield_servings=servings,
        provenance_json={"source": "v2_cooking_complete", "session_id": session_id},
    )
    if quantity is not None and not request.get("yield_unit"):
        raise error("validation_error", 422, details={"yield_unit": "required with yield_quantity"})
    db.add(prepared)
    db.add(CookingEvent(cooking_event_id=uuid7_str(), session_id=session_id, household_id=session.household_id, event_kind="COMPLETED", occurred_at=now, payload_json={"prepared_food_id": prepared.prepared_food_id, "yield_quantity": quantity, "yield_servings": servings}, idempotency_key=idempotency_key))
    db.commit()
    return _session_payload(session, prepared)


def _item_payload(item: ConsumptionItem) -> dict[str, Any]:
    return {"consumption_item_id": item.consumption_item_id, "display_text": item.display_text, "quantity": item.quantity, "unit": item.unit, "nutrition": item.nutrition_json, "nutrition_provenance": item.nutrition_provenance_json}


def _event_payload(event: ConsumptionEvent, items: list[ConsumptionItem]) -> dict[str, Any]:
    return {"consumption_event_id": event.consumption_event_id, "person_id": event.person_id, "household_id": event.household_id, "source_kind": event.source_kind, "state": event.state, "occurred_at": event.occurred_at.isoformat(), "portion_state": event.portion_state, "recipe_version_id": event.recipe_version_id, "plan_slot_id": event.plan_slot_id, "correction_of_event_id": event.correction_of_event_id, "items": [_item_payload(item) for item in items]}


def _normalize_items(request: dict[str, Any]) -> list[dict[str, Any]]:
    raw = request.get("items") or [{"display_text": request.get("external_description"), "quantity": request.get("portion"), "unit": request.get("portion_unit"), "nutrition": request.get("nutrition") or {}, "nutrition_provenance": request.get("nutrition_provenance") or {}}]
    if not raw:
        raise error("validation_error", 422, details={"items": "at least one item is required"})
    result = []
    for item in raw:
        quantity = item.get("quantity")
        if quantity is not None and quantity <= 0:
            raise error("validation_error", 422, details={"quantity": "must be positive"})
        if quantity is not None and not item.get("unit"):
            raise error("validation_error", 422, details={"unit": "required with quantity"})
        if not item.get("food_identity_key") and not item.get("product_instance_key") and not item.get("display_text"):
            raise error("validation_error", 422, details={"item": "identity or description required"})
        result.append(item)
    return result


def _recompute_health(db: Session, person_id: str, projection_date: date) -> None:
    events = db.scalars(select(ConsumptionEvent).where(ConsumptionEvent.person_id == person_id, ConsumptionEvent.occurred_at >= datetime.combine(projection_date, datetime.min.time(), tzinfo=timezone.utc), ConsumptionEvent.occurred_at < datetime.combine(projection_date, datetime.max.time(), tzinfo=timezone.utc), ConsumptionEvent.state == "CONFIRMED")).all()
    event_ids = [event.consumption_event_id for event in events]
    items = db.scalars(select(ConsumptionItem).where(ConsumptionItem.consumption_event_id.in_(event_ids))) .all() if event_ids else []
    totals: dict[str, float] = {}
    known = True
    for item in items:
        nutrition = item.nutrition_json or {}
        if not nutrition:
            known = False
        for key, value in nutrition.items():
            if isinstance(value, (int, float)):
                totals[key] = totals.get(key, 0.0) + float(value)
    completeness = "COMPLETE" if events and known else "PARTIAL" if events else "UNKNOWN"
    projection = db.scalar(select(HealthProjection).where(HealthProjection.person_id == person_id, HealthProjection.projection_date == projection_date, HealthProjection.calculation_version == "w6-v1").with_for_update())
    if projection is None:
        projection = HealthProjection(projection_id=uuid7_str(), person_id=person_id, projection_date=projection_date, calculation_version="w6-v1")
        db.add(projection)
    projection.completeness = completeness
    projection.planned_json = {"status": "UNKNOWN"}
    projection.actual_json = totals
    projection.deviation_json = {"status": "UNKNOWN", "reason": "nutrition_targets_or_plan_not_loaded"}
    projection.safety_status = "UNKNOWN"
    projection.source_refs_json = {"consumption_event_ids": event_ids, "provenance": "canonical_consumption_events"}
    db.flush()
    db.query(HealthDeviation).filter(HealthDeviation.projection_id == projection.projection_id).delete(synchronize_session=False)
    db.add(HealthDeviation(deviation_id=uuid7_str(), projection_id=projection.projection_id, person_id=person_id, deviation_kind="COMPLETENESS", severity="UNKNOWN" if completeness != "COMPLETE" else "INFO", known_json={"actual": totals}, unknown_json={} if completeness == "COMPLETE" else {"nutrition": "incomplete"}, provenance_json={"calculation_version": "w6-v1"}))


def record_consumption(db: Session, context: AuthorizedContext, person_id: str, *, idempotency_key: str, request: dict[str, Any]) -> dict[str, Any]:
    target, household_id = _person(db, context, person_id, request.get("household_id"), capability="consumption.write")
    prior = db.scalar(select(ConsumptionEvent).where(ConsumptionEvent.household_id == household_id, ConsumptionEvent.idempotency_key == idempotency_key))
    if prior:
        return _event_payload(prior, db.scalars(select(ConsumptionItem).where(ConsumptionItem.consumption_event_id == prior.consumption_event_id)).all())
    slot = _slot_context(db, request.get("plan_slot_id"), household_id)
    session = db.get(CookingSession, request.get("cooking_session_id")) if request.get("cooking_session_id") else None
    if session is not None and session.household_id != household_id:
        raise error("forbidden", 403)
    source_kind = request.get("source_kind", "MANUAL")
    if source_kind == "AI_PROPOSAL" and not request.get("confirmed", False):
        raise error("validation_error", 422, details={"confirmed": "AI proposal requires explicit confirmation"})
    correction_of = request.get("correction_of_event_id")
    if correction_of:
        previous = db.scalar(select(ConsumptionEvent).where(ConsumptionEvent.consumption_event_id == correction_of, ConsumptionEvent.person_id == person_id).with_for_update())
        if previous is None:
            raise error("not_found", 404)
        previous.state = "CORRECTED"
    items_data = _normalize_items(request)
    quantities = [item.get("quantity") for item in items_data]
    portion_state = "KNOWN" if all(value is not None for value in quantities) else "UNKNOWN"
    event = ConsumptionEvent(consumption_event_id=uuid7_str(), person_id=target.person_id, household_id=household_id, plan_slot_id=slot.slot_id if slot else None, recipe_version_id=request.get("recipe_version_id") or (slot.recipe_version_id if slot else None), cooking_session_id=session.cooking_session_id if session else None, source_kind=source_kind, state="CONFIRMED", occurred_at=request.get("occurred_at") or _now(), portion_state=portion_state, confidence="CONFIRMED", external_description=request.get("external_description"), correction_of_event_id=correction_of, provenance_json={"source": "v2_meal_checkin", "confirmed": True}, idempotency_key=idempotency_key)
    db.add(event)
    db.flush()
    items = []
    for data in items_data:
        item = ConsumptionItem(consumption_item_id=uuid7_str(), consumption_event_id=event.consumption_event_id, person_id=target.person_id, food_identity_key=data.get("food_identity_key"), product_instance_key=data.get("product_instance_key"), display_text=data.get("display_text"), quantity=data.get("quantity"), unit=data.get("unit"), nutrition_json=data.get("nutrition") or {}, nutrition_provenance_json=data.get("nutrition_provenance") or {})
        db.add(item)
        items.append(item)
    _recompute_health(db, target.person_id, event.occurred_at.date())
    db.commit()
    return _event_payload(event, items)


def list_health_deviations(db: Session, context: AuthorizedContext, person_id: str, *, date_from: date | None = None, date_to: date | None = None) -> dict[str, Any]:
    target, _ = _person(db, context, person_id, None, capability="health.read")
    query = select(HealthProjection).where(HealthProjection.person_id == target.person_id).order_by(HealthProjection.projection_date.desc())
    if date_from:
        query = query.where(HealthProjection.projection_date >= date_from)
    if date_to:
        query = query.where(HealthProjection.projection_date <= date_to)
    projections = db.scalars(query).all()
    projection_ids = [row.projection_id for row in projections]
    deviations = db.scalars(select(HealthDeviation).where(HealthDeviation.projection_id.in_(projection_ids))) .all() if projection_ids else []
    by_projection: dict[str, list[HealthDeviation]] = {}
    for deviation in deviations:
        by_projection.setdefault(deviation.projection_id, []).append(deviation)
    return {"person_id": target.person_id, "projections": [{"projection_id": row.projection_id, "date": row.projection_date.isoformat(), "completeness": row.completeness, "planned": row.planned_json, "actual": row.actual_json, "deviation": row.deviation_json, "safety_status": row.safety_status, "deviations": [{"deviation_id": item.deviation_id, "kind": item.deviation_kind, "severity": item.severity, "known": item.known_json, "unknown": item.unknown_json} for item in by_projection.get(row.projection_id, [])]} for row in projections]}
