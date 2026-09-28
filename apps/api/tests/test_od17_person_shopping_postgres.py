from __future__ import annotations

import os
import uuid

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from app.core.models import CoreAccount, CoreHousehold, CoreMembership, CorePerson
from app.shopping.v2_models import PantryInventory, ShoppingItem
from app.shopping.v2_service import (
    accept_receipt, add_manual_item, create_receipt, list_pantry, list_shopping,
    purchase,
)
from app.v2.authorization import AuthorizedContext
from app.v2.errors import V2Error


@pytest.fixture
def db():
    url = os.getenv("OD17_TEST_DATABASE_URL")
    if not url:
        pytest.skip("OD17_TEST_DATABASE_URL is required")
    engine = create_engine(url)
    if engine.dialect.name != "postgresql" or engine.url.host not in {"localhost", "127.0.0.1"}:
        engine.dispose()
        pytest.fail("OD-17 functional tests require local PostgreSQL")
    with engine.connect() as connection:
        outer = connection.begin()
        session = Session(bind=connection, join_transaction_mode="create_savepoint")
        try:
            yield session
        finally:
            session.close()
            outer.rollback()
    engine.dispose()


def _person(db: Session) -> tuple[str, AuthorizedContext]:
    person = CorePerson(person_id=str(uuid.uuid4()), display_name="fixture")
    db.add(person)
    db.flush()
    account = CoreAccount(account_id=str(uuid.uuid4()), primary_person_id=person.person_id, status="active")
    return person.person_id, AuthorizedContext(account=account, session=None, person=person, household_id=None, actor_person=person)


def test_person_only_shopping_purchase_pantry_and_receipt(db: Session):
    person_id, context = _person(db)
    shopping = add_manual_item(db, context, person_id=person_id, idempotency_key="person-item", request={
        "display_text": "Test food", "quantity": 2, "unit": "g", "category": None,
    })
    assert shopping["owner_scope"] == "PERSON"
    assert shopping["household_id"] is None
    assert list_shopping(db, context, person_id=person_id)["items"][0]["state"] == "NEEDED"
    item_id = shopping["items"][0]["shopping_item_id"]
    bought = purchase(db, context, None, item_id, idempotency_key="person-purchase", add_to_pantry=True)
    assert bought["items"][0]["state"] == "PURCHASED"
    assert purchase(db, context, None, item_id, idempotency_key="person-purchase", add_to_pantry=True)["items"][0]["state"] == "PURCHASED"
    pantry = list_pantry(db, context, person_id=person_id)
    assert pantry["household_id"] is None
    assert [(item["display_text"], item["quantity"]) for item in pantry["items"]] == [("Test food", 2)]
    receipt = create_receipt(db, context, person_id=person_id, idempotency_key="person-receipt", request={
        "lines": [{"raw_text": "Other food", "confidence": "HIGH", "quantity": 1, "unit": "g"}],
    })
    from app.shopping.v2_models import ReceiptLine
    line_id = db.scalar(select(ReceiptLine.receipt_line_id).where(ReceiptLine.receipt_proposal_id == receipt["receipt_proposal_id"]))
    result = accept_receipt(db, context, None, receipt["receipt_document_id"], receipt["receipt_proposal_id"],
                            idempotency_key="person-receipt-confirm", line_ids=[line_id])
    assert result["state"] == "VERIFIED"
    assert db.scalar(select(func.count()).select_from(PantryInventory).where(PantryInventory.person_id == person_id)) == 2


def test_person_cross_scope_denied_before_mutation(db: Session):
    owner_id, owner = _person(db)
    stranger_id, stranger = _person(db)
    shopping = add_manual_item(db, owner, person_id=owner_id, idempotency_key="owned-item", request={
        "display_text": "Private item", "quantity": None, "unit": None, "category": None,
    })
    item_id = shopping["items"][0]["shopping_item_id"]
    before = db.scalar(select(func.count()).select_from(ShoppingItem))
    with pytest.raises(V2Error) as denied:
        list_shopping(db, stranger, person_id=owner_id)
    assert denied.value.status_code == 403
    with pytest.raises(V2Error) as denied:
        purchase(db, stranger, None, item_id, idempotency_key="foreign-purchase")
    assert denied.value.status_code == 403
    assert db.scalar(select(func.count()).select_from(ShoppingItem)) == before
    assert list_shopping(db, owner, person_id=owner_id)["items"][0]["state"] == "NEEDED"
    assert stranger_id != owner_id


def test_household_shopping_still_works(db: Session):
    person_id, context = _person(db)
    household = CoreHousehold(household_id=str(uuid.uuid4()), name="fixture")
    db.add(household)
    db.add(CoreMembership(membership_id=str(uuid.uuid4()), person_id=person_id, household_id=household.household_id))
    db.flush()
    shopping = add_manual_item(db, context, household.household_id, idempotency_key="household-item", request={
        "display_text": "Shared item", "quantity": 1, "unit": "piece", "category": None,
    })
    assert shopping["owner_scope"] == "HOUSEHOLD"
    assert shopping["person_id"] is None
    assert shopping["household_id"] == household.household_id
