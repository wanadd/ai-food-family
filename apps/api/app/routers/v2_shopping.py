from __future__ import annotations
from typing import Any
from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.database import get_db
from app.v2.authorization import AuthorizedContext, authorized_context
from app.shopping.v2_service import accept_receipt, add_manual_item, adjust_pantry, create_receipt, derive_from_revision, list_pantry, list_shopping, purchase, remove_item

router = APIRouter(prefix="/api/v2", tags=["v2-shopping"])


def _context(db: Session = Depends(get_db), authorization: str | None = Header(default=None), session_token: str | None = Header(default=None, alias="X-Planam-Session")) -> AuthorizedContext:
    return authorized_context(db, authorization=authorization, x_planam_session=session_token)


def _key(value: str | None) -> str:
    if not value:
        from app.v2.errors import error
        raise error("validation_error", 422, details={"header": "Idempotency-Key is required"})
    return value


class ManualShoppingRequest(BaseModel):
    display_text: str = Field(min_length=1, max_length=240)
    quantity: float | None = Field(default=None, gt=0)
    unit: str | None = Field(default=None, max_length=32)
    category: str | None = Field(default=None, max_length=64)


class PurchaseRequest(BaseModel):
    add_to_pantry: bool = False


class PantryAdjustRequest(BaseModel):
    display_text: str = Field(min_length=1, max_length=240)
    quantity_delta: float | None = None
    unit: str | None = Field(default=None, max_length=32)


class ReceiptLineRequest(BaseModel):
    raw_text: str = Field(min_length=1, max_length=500)
    confidence: str = "UNKNOWN"
    quantity: float | None = Field(default=None, gt=0)
    unit: str | None = None


class ReceiptCreateRequest(BaseModel):
    media_asset_id: str | None = None
    provider_metadata: dict[str, Any] = {}
    lines: list[ReceiptLineRequest] = []


class ReceiptAcceptRequest(BaseModel):
    line_ids: list[str] = Field(min_length=1)


@router.get("/households/{household_id}/shopping")
def shopping_read(household_id: str, context: AuthorizedContext = Depends(_context), db: Session = Depends(get_db)) -> dict:
    return list_shopping(db, context, household_id)


@router.get("/persons/{person_id}/shopping")
def person_shopping_read(person_id: str, context: AuthorizedContext = Depends(_context), db: Session = Depends(get_db)) -> dict:
    return list_shopping(db, context, person_id=person_id)


@router.post("/households/{household_id}/shopping/items")
def shopping_add(household_id: str, payload: ManualShoppingRequest, idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), context: AuthorizedContext = Depends(_context), db: Session = Depends(get_db)) -> dict:
    return add_manual_item(db, context, household_id, idempotency_key=_key(idempotency_key), request=payload.model_dump())


@router.post("/persons/{person_id}/shopping/items")
def person_shopping_add(person_id: str, payload: ManualShoppingRequest, idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), context: AuthorizedContext = Depends(_context), db: Session = Depends(get_db)) -> dict:
    return add_manual_item(db, context, person_id=person_id, idempotency_key=_key(idempotency_key), request=payload.model_dump())


@router.post("/households/{household_id}/shopping/from-plan/{revision_id}")
def household_shopping_from_plan(household_id: str, revision_id: str, idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), context: AuthorizedContext = Depends(_context), db: Session = Depends(get_db)) -> dict:
    return derive_from_revision(db, context, household_id, revision_id, idempotency_key=_key(idempotency_key))


@router.post("/persons/{person_id}/shopping/from-plan/{revision_id}")
def person_shopping_from_plan(person_id: str, revision_id: str, idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), context: AuthorizedContext = Depends(_context), db: Session = Depends(get_db)) -> dict:
    return derive_from_revision(db, context, None, revision_id, person_id=person_id, idempotency_key=_key(idempotency_key))


@router.post("/shopping/items/{item_id}/purchase")
def shopping_purchase(item_id: str, payload: PurchaseRequest, household_id: str | None = Header(default=None, alias="X-Planam-Household-Id"), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), context: AuthorizedContext = Depends(_context), db: Session = Depends(get_db)) -> dict:
    return purchase(db, context, household_id, item_id, idempotency_key=_key(idempotency_key), add_to_pantry=payload.add_to_pantry)


@router.delete("/shopping/items/{item_id}")
def shopping_remove(item_id: str, idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), context: AuthorizedContext = Depends(_context), db: Session = Depends(get_db)) -> dict:
    return remove_item(db, context, item_id, idempotency_key=_key(idempotency_key))


@router.get("/households/{household_id}/pantry")
def pantry_read(household_id: str, context: AuthorizedContext = Depends(_context), db: Session = Depends(get_db)) -> dict:
    return list_pantry(db, context, household_id)


@router.get("/persons/{person_id}/pantry")
def person_pantry_read(person_id: str, context: AuthorizedContext = Depends(_context), db: Session = Depends(get_db)) -> dict:
    return list_pantry(db, context, person_id=person_id)


@router.post("/households/{household_id}/pantry/adjust")
def pantry_adjust(household_id: str, payload: PantryAdjustRequest, idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), context: AuthorizedContext = Depends(_context), db: Session = Depends(get_db)) -> dict:
    return adjust_pantry(db, context, household_id, idempotency_key=_key(idempotency_key), request=payload.model_dump())


@router.post("/persons/{person_id}/pantry/adjust")
def person_pantry_adjust(person_id: str, payload: PantryAdjustRequest, idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), context: AuthorizedContext = Depends(_context), db: Session = Depends(get_db)) -> dict:
    return adjust_pantry(db, context, person_id=person_id, idempotency_key=_key(idempotency_key), request=payload.model_dump())


@router.post("/households/{household_id}/receipts")
def receipt_create(household_id: str, payload: ReceiptCreateRequest, idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), context: AuthorizedContext = Depends(_context), db: Session = Depends(get_db)) -> dict:
    return create_receipt(db, context, household_id, idempotency_key=_key(idempotency_key), request=payload.model_dump())


@router.post("/persons/{person_id}/receipts")
def person_receipt_create(person_id: str, payload: ReceiptCreateRequest, idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), context: AuthorizedContext = Depends(_context), db: Session = Depends(get_db)) -> dict:
    return create_receipt(db, context, person_id=person_id, idempotency_key=_key(idempotency_key), request=payload.model_dump())


@router.post("/receipts/{receipt_id}/proposals/{proposal_id}/accept")
def receipt_accept(receipt_id: str, proposal_id: str, payload: ReceiptAcceptRequest, household_id: str | None = Header(default=None, alias="X-Planam-Household-Id"), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), context: AuthorizedContext = Depends(_context), db: Session = Depends(get_db)) -> dict:
    return accept_receipt(db, context, household_id, receipt_id, proposal_id, idempotency_key=_key(idempotency_key), line_ids=payload.line_ids)
