from __future__ import annotations

from datetime import date
from typing import Any, Literal

from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.v2.authorization import AuthorizedContext, authorized_context
from app.v2.errors import error
from app.planning.v2_models import Plan, PlanRevision
from app.planning.v2_service import _revision_payload, create_plan, create_revision, get_plan

router = APIRouter(prefix="/api/v2", tags=["v2-planning"])


class PlanCreateRequest(BaseModel):
    owner_scope: Literal["PERSON", "HOUSEHOLD"]
    person_id: str | None = None
    household_id: str | None = None
    date_from: date | None = None
    date_to: date | None = None
    mode: str = Field(default="balanced", max_length=64)


class SlotRequest(BaseModel):
    slot_key: str = Field(min_length=1, max_length=96)
    planned_date: date
    meal_type: str = Field(min_length=1, max_length=32)
    state: Literal["ASSIGNED", "EMPTY", "FREE", "CANCELLED"] | None = None
    recipe_version_id: str | None = None
    participants: list[dict[str, Any]] = Field(default_factory=list)
    portions: list[dict[str, Any]] = Field(default_factory=list)
    provenance: dict[str, Any] = Field(default_factory=dict)


class PlanGenerateRequest(BaseModel):
    slots: list[SlotRequest] = Field(default_factory=list)
    expected_revision_id: str | None = None


class PlanReplaceRequest(BaseModel):
    slot_key: str = Field(min_length=1, max_length=96)
    recipe_version_id: str
    participants: list[dict[str, Any]] = Field(default_factory=list)
    portions: list[dict[str, Any]] = Field(default_factory=list)
    expected_revision_id: str


class PlanEmptyRequest(BaseModel):
    expected_revision_id: str
    reason: str = Field(default="manual_clear", max_length=160)


def _context(
    db: Session = Depends(get_db),
    authorization: str | None = Header(default=None),
    session_token: str | None = Header(default=None, alias="X-Planam-Session"),
) -> AuthorizedContext:
    return authorized_context(db, authorization=authorization, x_planam_session=session_token)


def _key(value: str | None) -> str:
    if not value:
        raise error("validation_error", 422, details={"header": "Idempotency-Key is required"})
    return value


def _current_slots(db: Session, plan_id: str, revision_id: str) -> list[dict[str, Any]]:
    revision = db.scalar(select(PlanRevision).where(PlanRevision.plan_id == plan_id, PlanRevision.revision_id == revision_id))
    if revision is None:
        raise error("conflict", 409, details={"reason": "stale_revision"})
    plan = db.get(Plan, plan_id)
    return _revision_payload(db, plan, revision)["slots"]


@router.post("/plans")
def plan_create(payload: PlanCreateRequest, idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), context: AuthorizedContext = Depends(_context), db: Session = Depends(get_db)) -> dict:
    return create_plan(db, context, owner_scope=payload.owner_scope, person_id=payload.person_id, household_id=payload.household_id, idempotency_key=_key(idempotency_key), request=payload.model_dump(mode="json"))


@router.post("/plans/{plan_id}/generate")
def plan_generate(plan_id: str, payload: PlanGenerateRequest, idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), context: AuthorizedContext = Depends(_context), db: Session = Depends(get_db)) -> dict:
    plan = get_plan(db, context, plan_id, write=True)
    return create_revision(db, context, plan, source_kind="AI_GENERATED", idempotency_key=_key(idempotency_key), request=payload.model_dump(mode="json"), slots=[item.model_dump() for item in payload.slots], expected_revision_id=payload.expected_revision_id)


@router.post("/plans/{plan_id}/revisions/{revision_id}/replace")
def plan_replace(plan_id: str, revision_id: str, payload: PlanReplaceRequest, idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), context: AuthorizedContext = Depends(_context), db: Session = Depends(get_db)) -> dict:
    plan = get_plan(db, context, plan_id, write=True)
    current = _current_slots(db, plan_id, revision_id)
    if payload.expected_revision_id != revision_id:
        raise error("conflict", 409, details={"reason": "stale_revision"})
    if not any(item["slot_key"] == payload.slot_key for item in current):
        raise error("not_found", 404)
    slots = [{"slot_key": item["slot_key"], "planned_date": date.fromisoformat(item["date"]), "meal_type": item["meal_type"], "state": "ASSIGNED" if item["slot_key"] == payload.slot_key else item["state"], "recipe_version_id": payload.recipe_version_id if item["slot_key"] == payload.slot_key else item["recipe_version_id"], "participants": payload.participants if item["slot_key"] == payload.slot_key else item["participants"], "portions": payload.portions if item["slot_key"] == payload.slot_key else item["portions"]} for item in current]
    return create_revision(db, context, plan, source_kind="REPLACEMENT", idempotency_key=_key(idempotency_key), request=payload.model_dump(mode="json"), slots=slots, expected_revision_id=revision_id)


@router.post("/plans/{plan_id}/slots/{slot_id}/empty")
def plan_empty(plan_id: str, slot_id: str, payload: PlanEmptyRequest, idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), context: AuthorizedContext = Depends(_context), db: Session = Depends(get_db)) -> dict:
    plan = get_plan(db, context, plan_id, write=True)
    current = _current_slots(db, plan_id, payload.expected_revision_id)
    if not any(item["slot_id"] == slot_id or item["slot_key"] == slot_id for item in current):
        raise error("not_found", 404)
    slots = [{"slot_key": item["slot_key"], "planned_date": date.fromisoformat(item["date"]), "meal_type": item["meal_type"], "state": "EMPTY" if item["slot_id"] == slot_id or item["slot_key"] == slot_id else item["state"], "recipe_version_id": None if item["slot_id"] == slot_id or item["slot_key"] == slot_id else item["recipe_version_id"], "participants": item["participants"], "portions": item["portions"], "provenance": {"clear_reason": payload.reason} if item["slot_id"] == slot_id or item["slot_key"] == slot_id else {}} for item in current]
    return create_revision(db, context, plan, source_kind="MANUAL", idempotency_key=_key(idempotency_key), request=payload.model_dump(mode="json"), slots=slots, expected_revision_id=payload.expected_revision_id)
