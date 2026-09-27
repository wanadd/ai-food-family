from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel, Field
from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import get_db
from app.food.evidence_models import FoodAlias, FoodCompositionFact
from app.food.profile_models import FoodProfile, FoodProfileFact, FoodProfileReconfirmation
from app.food.wave2_domain import ConfirmationState, KnowledgeState, aggregate_safety, evaluate_safety, match_food
from app.food.wave2_models import FoodIdentity, SafetyDecision
from app.v2.authorization import AuthorizedContext, authorized_context
from app.v2.errors import error
from app.v2.uuid7 import uuid7_str

router = APIRouter(prefix="/api/v2", tags=["v2-food"])


class ProfileFactInput(BaseModel):
    fact_type: str = Field(min_length=1, max_length=64)
    fact_key: str = Field(min_length=1, max_length=160)
    knowledge_state: KnowledgeState
    value_json: dict | list | str | int | float | bool | None = None
    confirmation_status: ConfirmationState = ConfirmationState.UNCONFIRMED
    effective_from: datetime | None = None
    effective_to: datetime | None = None


class ProfilePutRequest(BaseModel):
    facts: list[ProfileFactInput] = Field(default_factory=list)


class ReconfirmRequest(BaseModel):
    fact_ids: list[str] = Field(min_length=1)
    evidence_context: dict = Field(default_factory=dict)


class SafetyEvaluateRequest(BaseModel):
    person_id: str
    food_identity_id: str | None = None
    profile_facts: list[dict] = Field(default_factory=list)
    food_relations: list[dict] = Field(default_factory=list)
    process_state: str | None = None
    evidence_backed: bool = False


def _context(db: Session, person_id: str, authorization: str | None, session_token: str | None, household_id: str | None, capability: str) -> AuthorizedContext:
    return authorized_context(
        db,
        authorization=authorization,
        x_planam_session=session_token,
        x_household_id=household_id,
        x_person_id=person_id,
        required_capability=capability,
    )


def _profile(db: Session, person_id: str) -> FoodProfile:
    profile = db.scalar(select(FoodProfile).where(FoodProfile.person_id == person_id))
    if profile is None:
        profile = FoodProfile(food_profile_id=uuid7_str(), person_id=person_id, profile_status="ACTIVE", provenance_json={})
        db.add(profile)
        db.flush()
    return profile


def _fact_payload(fact: FoodProfileFact) -> dict:
    return {
        "fact_id": fact.fact_id,
        "fact_type": fact.fact_type,
        "fact_key": fact.fact_key,
        "knowledge_state": fact.knowledge_state,
        "value_json": fact.value_json,
        "confirmation_status": fact.confirmation_status,
        "effective_from": fact.effective_from.isoformat() if fact.effective_from else None,
        "effective_to": fact.effective_to.isoformat() if fact.effective_to else None,
    }


@router.get("/people/{person_id}/food-profile")
def get_food_profile(
    person_id: str,
    db: Session = Depends(get_db),
    authorization: str | None = Header(default=None),
    session_token: str | None = Header(default=None, alias="X-Planam-Session"),
    household_id: str | None = Header(default=None, alias="X-Planam-Household-Id"),
) -> dict:
    context = _context(db, person_id, authorization, session_token, household_id, "food.profile.read")
    profile = db.scalar(select(FoodProfile).where(FoodProfile.person_id == context.person.person_id))
    if profile is None:
        return {"person_id": person_id, "food_profile_id": None, "facts": [], "profile_status": "ACTIVE"}
    facts = db.scalars(select(FoodProfileFact).where(FoodProfileFact.food_profile_id == profile.food_profile_id).order_by(FoodProfileFact.fact_key)).all()
    pending = db.scalars(select(FoodProfileReconfirmation).where(FoodProfileReconfirmation.food_profile_id == profile.food_profile_id, FoodProfileReconfirmation.status == "PENDING")).all()
    return {"person_id": person_id, "food_profile_id": profile.food_profile_id, "profile_status": profile.profile_status, "facts": [_fact_payload(fact) for fact in facts], "reconfirmation_required": [item.reconfirmation_id for item in pending]}


@router.put("/people/{person_id}/food-profile")
def put_food_profile(
    person_id: str,
    payload: ProfilePutRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    db: Session = Depends(get_db),
    authorization: str | None = Header(default=None),
    session_token: str | None = Header(default=None, alias="X-Planam-Session"),
    household_id: str | None = Header(default=None, alias="X-Planam-Household-Id"),
) -> dict:
    if not idempotency_key:
        raise error("validation_error", 422, details={"header": "Idempotency-Key is required"})
    context = _context(db, person_id, authorization, session_token, household_id, "food.profile.write")
    profile = _profile(db, context.person.person_id)
    fingerprint = hashlib.sha256(json.dumps(payload.model_dump(mode="json"), sort_keys=True).encode()).hexdigest()
    prior = (profile.provenance_json or {}).get("last_food_profile_mutation")
    if prior and prior.get("key") == idempotency_key:
        return get_food_profile(person_id, db, authorization, session_token, household_id)
    now = datetime.now(timezone.utc)
    for previous in db.scalars(select(FoodProfileFact).where(FoodProfileFact.food_profile_id == profile.food_profile_id, FoodProfileFact.effective_to.is_(None))).all():
        previous.confirmation_status = ConfirmationState.SUPERSEDED.value
        previous.effective_to = now
    for item in payload.facts:
        if item.knowledge_state == KnowledgeState.KNOWN_PRESENT and item.value_json is None:
            raise error("validation_error", 422, details={"fact": "KNOWN_PRESENT requires value_json"})
        if item.knowledge_state == KnowledgeState.KNOWN_NONE and item.value_json is not None:
            raise error("validation_error", 422, details={"fact": "KNOWN_NONE requires null value_json"})
        fact = FoodProfileFact(
            fact_id=uuid7_str(), food_profile_id=profile.food_profile_id, fact_type=item.fact_type,
            fact_key=item.fact_key, knowledge_state=item.knowledge_state.value, value_json=item.value_json,
            effective_from=item.effective_from or datetime.now(timezone.utc), effective_to=item.effective_to,
            provenance_json={"source": "v2_profile_command", "idempotency_key": idempotency_key},
            source_kind="USER_ASSERTED", source_legacy_table="v2_food_profile", source_legacy_id_text=idempotency_key,
            confirmation_status=item.confirmation_status.value,
        )
        db.add(fact)
    profile.provenance_json = {**(profile.provenance_json or {}), "last_food_profile_mutation": {"key": idempotency_key, "fingerprint": fingerprint}}
    db.commit()
    return get_food_profile(person_id, db, authorization, session_token, household_id)


@router.post("/people/{person_id}/food-profile/reconfirm")
def reconfirm_food_profile(
    person_id: str,
    payload: ReconfirmRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    db: Session = Depends(get_db),
    authorization: str | None = Header(default=None),
    session_token: str | None = Header(default=None, alias="X-Planam-Session"),
    household_id: str | None = Header(default=None, alias="X-Planam-Household-Id"),
) -> dict:
    if not idempotency_key or not payload.evidence_context:
        raise error("validation_error", 422, details={"reconfirmation": "Idempotency-Key and evidence_context are required"})
    context = _context(db, person_id, authorization, session_token, household_id, "food.profile.write")
    profile = db.scalar(select(FoodProfile).where(FoodProfile.person_id == context.person.person_id))
    if profile is None:
        raise error("not_found", 404)
    facts = db.scalars(select(FoodProfileFact).where(FoodProfileFact.food_profile_id == profile.food_profile_id, FoodProfileFact.fact_id.in_(payload.fact_ids))).all()
    if len(facts) != len(set(payload.fact_ids)):
        raise error("not_found", 404)
    for fact in facts:
        if fact.confirmation_status not in {ConfirmationState.UNCONFIRMED.value, ConfirmationState.NEEDS_RECONFIRMATION.value}:
            continue
        fact.confirmation_status = ConfirmationState.CONFIRMED.value
        fact.provenance_json = {**(fact.provenance_json or {}), "reconfirmed_by": context.account.account_id, "reconfirmation_key": idempotency_key, "evidence_context": payload.evidence_context}
    db.commit()
    return {"person_id": person_id, "confirmed_fact_ids": [fact.fact_id for fact in facts]}


@router.get("/foods/search")
def search_foods(query: str = "", db: Session = Depends(get_db), authorization: str | None = Header(default=None), session_token: str | None = Header(default=None, alias="X-Planam-Session")) -> list[dict]:
    _context(db, "", authorization, session_token, None, "food.read")
    identities = db.scalars(select(FoodIdentity).where(FoodIdentity.lifecycle_status.notin_(["archived", "deprecated"]))).all()
    normalized = query.casefold().strip()
    return [{"food_identity_id": item.food_identity_id, "identity_key": item.identity_key, "display_name": item.display_name, "food_kind": item.food_kind} for item in identities if not normalized or normalized in item.display_name.casefold() or normalized == item.identity_key.casefold()]


@router.get("/foods/{food_id}")
def get_food(food_id: str, db: Session = Depends(get_db), authorization: str | None = Header(default=None), session_token: str | None = Header(default=None, alias="X-Planam-Session")) -> dict:
    _context(db, "", authorization, session_token, None, "food.read")
    identity = db.get(FoodIdentity, food_id)
    if identity is None:
        raise error("not_found", 404)
    return {"food_identity_id": identity.food_identity_id, "identity_key": identity.identity_key, "display_name": identity.display_name, "food_kind": identity.food_kind, "provenance_status": identity.provenance_status}


@router.post("/safety/evaluate")
def evaluate_food_safety(
    payload: SafetyEvaluateRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    db: Session = Depends(get_db),
    authorization: str | None = Header(default=None),
    session_token: str | None = Header(default=None, alias="X-Planam-Session"),
    household_id: str | None = Header(default=None, alias="X-Planam-Household-Id"),
) -> dict:
    if not idempotency_key:
        raise error("validation_error", 422, details={"header": "Idempotency-Key is required"})
    context = _context(db, payload.person_id, authorization, session_token, household_id, "food.safety.evaluate")
    profile = db.scalar(select(FoodProfile).where(FoodProfile.person_id == context.person.person_id))
    server_facts = []
    if profile is not None:
        server_facts = [_fact_payload(fact) for fact in db.scalars(select(FoodProfileFact).where(FoodProfileFact.food_profile_id == profile.food_profile_id, FoodProfileFact.effective_to.is_(None))).all()]
    server_relations: list[dict] = []
    evidence_backed = False
    if payload.food_identity_id is not None:
        try:
            rows = db.execute(text("SELECT concept_id, relation_type, fact_status, provenance_status FROM food_safety_facts WHERE food_identity_id = :food_id AND is_current = TRUE"), {"food_id": payload.food_identity_id}).mappings().all()
            server_relations = [{"concept": row["concept_id"], "relation": row["relation_type"]} for row in rows if row["fact_status"] in {"present", "known_present", "contains", "may_contain", "cross_contact", "unknown"}]
            evidence_backed = bool(rows) and all(row["provenance_status"] in {"source_backed", "verified", "SOURCE_BACKED"} for row in rows)
        except SQLAlchemyError:
            server_relations = []
    # profile_facts, food_relations and evidence_backed are intentionally not
    # trusted as client-supplied safety authority.
    decision, reasons = evaluate_safety(profile_facts=server_facts, food_relations=server_relations, evidence_backed=evidence_backed, process_known=payload.process_state is not None)
    existing = db.scalar(select(SafetyDecision).where(SafetyDecision.person_id == context.person.person_id, SafetyDecision.idempotency_key == idempotency_key))
    if existing is None:
        existing = SafetyDecision(safety_decision_id=uuid7_str(), person_id=context.person.person_id, food_identity_id=payload.food_identity_id, process_state=payload.process_state, decision=decision.value, reason_codes_json=reasons, evidence_claim_ids_json=[], idempotency_key=idempotency_key)
        db.add(existing)
        db.commit()
    return {"safety_decision_id": existing.safety_decision_id, "person_id": existing.person_id, "food_identity_id": existing.food_identity_id, "decision": existing.decision, "reason_codes": existing.reason_codes_json, "evidence_claim_ids": existing.evidence_claim_ids_json}
