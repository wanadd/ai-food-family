from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.models import CoreHousehold, CorePerson
from app.database import Base
from app.events import v2_models  # noqa: F401
from app.events.v2_models import Event
from app.events.v2_service import (
    create_event, create_invitation, event_payload, respond_invitation,
    set_food_facts, transition_event,
)
from app.v2.authorization import AuthorizedContext
from app.v2.errors import V2Error
from app.v2.uuid7 import uuid7_str


@pytest.fixture()
def db() -> Session:
    engine = create_engine("sqlite:///:memory:")
    names = ["core_persons", "core_households"] + [
        "events_v2", "event_invitations_v2", "event_participants_v2", "event_participant_food_facts_v2",
        "event_menu_revisions_v2", "event_menu_items_v2", "event_menu_item_participants_v2", "event_shopping_demands_v2",
    ]
    Base.metadata.create_all(engine, tables=[Base.metadata.tables[name] for name in names])
    with Session(engine) as session:
        yield session


def _context(db: Session, name: str = "Organizer") -> AuthorizedContext:
    person = CorePerson(person_id=uuid7_str(), display_name=name, birth_date_precision="unknown")
    db.add(person)
    db.flush()
    return AuthorizedContext(account=None, session=None, person=person, household_id=None, actor_person=person)  # type: ignore[arg-type]


def _event(db: Session, context: AuthorizedContext, key: str = "event-1") -> dict:
    return create_event(db, context, title="Dinner", event_type="dinner", starts_at=datetime.now(timezone.utc), ends_at=None, collaboration_mode="RESTRICTIONS_COLLECTION", idempotency_key=key)


def test_multiple_events_are_independent_and_idempotent(db: Session):
    context = _context(db)
    first = _event(db, context, "one")
    second = _event(db, context, "two")

    assert first["event_id"] != second["event_id"]
    assert _event(db, context, "one")["event_id"] == first["event_id"]
    assert first["headcount"] == {"expected": 1, "confirmed": 1}


def test_invitation_can_add_multiple_temporary_guests_without_core_identity(db: Session):
    context = _context(db)
    event = _event(db, context)
    invitation = create_invitation(db, context, event["event_id"], None, "invite-1")
    response = respond_invitation(db, invitation["token"], [
        {"display_name": "Guest A", "age_group": "ADULT", "knowledge_state": "UNKNOWN", "restrictions": [{"fact_key": "allergen.egg"}]},
        {"display_name": "Child B", "age_group": "CHILD", "knowledge_state": "KNOWN_NONE", "restrictions": [{"fact_key": "allergen.milk"}]},
    ], "response-1")
    db.commit()

    assert len(response["participants"]) == 2
    assert all(item["person_id"] is None for item in response["participants"])
    refreshed = event_payload(db, db.get(Event, event["event_id"]))
    assert refreshed["headcount"]["confirmed"] == 3
    states = {item["food_profile"]["knowledge_state"] for item in refreshed["participants"]}
    assert "UNKNOWN" in states and "KNOWN_NONE" in states


def test_unknown_is_not_known_none_and_stale_version_is_rejected(db: Session):
    context = _context(db)
    event = _event(db, context)
    participant = event["participants"][0]
    set_food_facts(db, context, event["event_id"], participant["participant_id"], "UNKNOWN", [{"fact_key": "allergen.egg"}], "facts-1")
    db.commit()
    current = event_payload(db, db.get(Event, event["event_id"]))
    assert current["food_profile_completeness"]["state"] == "INCOMPLETE"
    with pytest.raises(V2Error) as exc:
        transition_event(db, context, event["event_id"], "OPEN", expected_version=999)
    assert exc.value.status_code == 409
