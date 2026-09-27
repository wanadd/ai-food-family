from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal

from fastapi import APIRouter, Depends, Header, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.v2.authorization import AuthorizedContext, authorized_context
from app.v2.errors import error
from app.cooking_health.v2_service import complete_cooking, list_health_deviations, record_consumption, start_cooking

router = APIRouter(prefix="/api/v2", tags=["v2-cooking-consumption-health"])


class CookingStartRequest(BaseModel):
    recipe_version_id: str | None = None
    plan_slot_id: str | None = None
    provenance: dict[str, Any] = Field(default_factory=dict)


class CookingCompleteRequest(BaseModel):
    display_name: str | None = Field(default=None, max_length=240)
    yield_quantity: float | None = None
    yield_unit: str | None = Field(default=None, max_length=32)
    yield_servings: float | None = None


class ConsumptionItemRequest(BaseModel):
    food_identity_key: str | None = None
    product_instance_key: str | None = None
    display_text: str | None = Field(default=None, max_length=240)
    quantity: float | None = None
    unit: str | None = Field(default=None, max_length=32)
    nutrition: dict[str, Any] = Field(default_factory=dict)
    nutrition_provenance: dict[str, Any] = Field(default_factory=dict)


class MealCheckinRequest(BaseModel):
    source_kind: Literal["PLANNED_RECIPE", "COOKED_FOOD", "EXTERNAL_MEAL", "MANUAL", "AI_PROPOSAL"] = "MANUAL"
    household_id: str | None = None
    plan_slot_id: str | None = None
    recipe_version_id: str | None = None
    cooking_session_id: str | None = None
    external_description: str | None = Field(default=None, max_length=500)
    portion: float | None = None
    portion_unit: str | None = Field(default=None, max_length=32)
    nutrition: dict[str, Any] = Field(default_factory=dict)
    nutrition_provenance: dict[str, Any] = Field(default_factory=dict)
    items: list[ConsumptionItemRequest] = Field(default_factory=list)
    occurred_at: datetime | None = None
    confirmed: bool = False
    correction_of_event_id: str | None = None


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


@router.post("/households/{household_id}/cooking-sessions")
def cooking_start(household_id: str, payload: CookingStartRequest, idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), context: AuthorizedContext = Depends(_context), db: Session = Depends(get_db)) -> dict[str, Any]:
    return start_cooking(db, context, household_id, idempotency_key=_key(idempotency_key), request=payload.model_dump(mode="json"))


@router.post("/cooking-sessions/{session_id}/complete")
def cooking_complete(session_id: str, payload: CookingCompleteRequest, idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), context: AuthorizedContext = Depends(_context), db: Session = Depends(get_db)) -> dict[str, Any]:
    return complete_cooking(db, context, session_id, idempotency_key=_key(idempotency_key), request=payload.model_dump(mode="json"))


@router.post("/people/{person_id}/meal-checkins")
def meal_checkin(person_id: str, payload: MealCheckinRequest, idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), context: AuthorizedContext = Depends(_context), db: Session = Depends(get_db)) -> dict[str, Any]:
    request = payload.model_dump(mode="json")
    if not request["items"] and request.get("external_description") is None and request.get("portion") is None:
        raise error("validation_error", 422, details={"items": "explicit consumed food is required"})
    request["items"] = [item.model_dump(mode="json") for item in payload.items]
    return record_consumption(db, context, person_id, idempotency_key=_key(idempotency_key), request=request)


@router.get("/people/{person_id}/health/deviations")
def health_deviations(person_id: str, date_from: date | None = Query(default=None), date_to: date | None = Query(default=None), context: AuthorizedContext = Depends(_context), db: Session = Depends(get_db)) -> dict[str, Any]:
    return list_health_deviations(db, context, person_id, date_from=date_from, date_to=date_to)
