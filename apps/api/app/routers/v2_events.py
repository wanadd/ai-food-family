from __future__ import annotations

from fastapi import APIRouter, Depends, Header
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.events.v2_schemas import (
    EventCreateRequest, EventUpdateRequest, FoodFactsRequest, InvitationCreateRequest,
    InvitationRespondRequest, LifecycleRequest, MenuRevisionRequest, ParticipantCreateRequest,
    ParticipantUpdateRequest, ShoppingGenerateRequest,
)
from app.events.v2_service import (
    _event, add_participant, create_event, create_invitation, create_menu_revision,
    event_payload, generate_shopping, inspect_invitation, menu_payload, respond_invitation,
    set_food_facts, transition_event, update_event, update_participant,
)
from app.events.v2_models import Event, EventParticipant
from app.v2.authorization import AuthorizedContext, authorized_context
from app.v2.errors import error

router = APIRouter(prefix="/api/v2", tags=["v2-events"])


def _context(
    db: Session = Depends(get_db),
    authorization: str | None = Header(default=None),
    session_token: str | None = Header(default=None, alias="X-Planam-Session"),
    household_id: str | None = Header(default=None, alias="X-Planam-Household-Id"),
    telegram_init_data: str | None = Header(default=None, alias="X-Telegram-Init-Data"),
) -> AuthorizedContext:
    return authorized_context(
        db,
        authorization=authorization,
        x_planam_session=session_token,
        x_household_id=household_id,
        x_telegram_init_data=telegram_init_data,
    )


def _key(value: str | None) -> str:
    if not value:
        raise error("validation_error", 422, details={"header": "Idempotency-Key is required"})
    return value


@router.get("/events")
def list_events(db: Session = Depends(get_db), context: AuthorizedContext = Depends(_context)) -> dict:
    actor = context.actor_person
    if actor is None:
        raise error("forbidden", 403)
    owned = select(Event.event_id).where(Event.organizer_person_id == actor.person_id)
    participant = select(EventParticipant.event_id).where(EventParticipant.person_id == actor.person_id)
    events = db.execute(select(Event).where(Event.event_id.in_(owned.union(participant))).order_by(Event.starts_at)).scalars().all()
    return {"items": [event_payload(db, event) for event in events]}


@router.post("/events")
def create_event_route(payload: EventCreateRequest, idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), db: Session = Depends(get_db), context: AuthorizedContext = Depends(_context)) -> dict:
    return create_event(db, context, title=payload.title, event_type=payload.event_type, starts_at=payload.starts_at, ends_at=payload.ends_at, collaboration_mode=payload.collaboration_mode, idempotency_key=_key(idempotency_key))


@router.get("/events/{event_id}")
def get_event(event_id: str, db: Session = Depends(get_db), context: AuthorizedContext = Depends(_context)) -> dict:
    return event_payload(db, _event(db, event_id, context))


@router.patch("/events/{event_id}")
def patch_event(event_id: str, payload: EventUpdateRequest, db: Session = Depends(get_db), context: AuthorizedContext = Depends(_context)) -> dict:
    return update_event(db, context, event_id, payload.model_dump(exclude_unset=True))


@router.post("/events/{event_id}/lifecycle")
def event_lifecycle(event_id: str, payload: LifecycleRequest, db: Session = Depends(get_db), context: AuthorizedContext = Depends(_context)) -> dict:
    return transition_event(db, context, event_id, payload.status, payload.expected_version)


@router.get("/events/{event_id}/participants")
def event_participants(event_id: str, db: Session = Depends(get_db), context: AuthorizedContext = Depends(_context)) -> dict:
    return {"items": event_payload(db, _event(db, event_id, context))["participants"]}


@router.post("/events/{event_id}/participants")
def add_event_participant(event_id: str, payload: ParticipantCreateRequest, idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), db: Session = Depends(get_db), context: AuthorizedContext = Depends(_context)) -> dict:
    return add_participant(db, context, event_id, payload.model_dump(), idempotency_key)


@router.patch("/events/{event_id}/participants/{participant_id}")
def patch_event_participant(event_id: str, participant_id: str, payload: ParticipantUpdateRequest, db: Session = Depends(get_db), context: AuthorizedContext = Depends(_context)) -> dict:
    return update_participant(db, context, event_id, participant_id, payload.model_dump(exclude_unset=True))


@router.post("/events/{event_id}/invitations")
def create_event_invitation(event_id: str, payload: InvitationCreateRequest, idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), db: Session = Depends(get_db), context: AuthorizedContext = Depends(_context)) -> dict:
    return create_invitation(db, context, event_id, payload.expires_at, _key(idempotency_key))


@router.post("/event-invitations/inspect")
def inspect_event_invitation(token: str, db: Session = Depends(get_db)) -> dict:
    return inspect_invitation(db, token)


@router.post("/event-invitations/respond")
def respond_event_invitation(token: str, payload: InvitationRespondRequest, idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), db: Session = Depends(get_db)) -> dict:
    return respond_invitation(db, token, [item.model_dump() for item in payload.participants], _key(idempotency_key))


@router.put("/events/{event_id}/participants/{participant_id}/food-facts")
def put_event_food_facts(event_id: str, participant_id: str, payload: FoodFactsRequest, idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), db: Session = Depends(get_db), context: AuthorizedContext = Depends(_context)) -> dict:
    return set_food_facts(db, context, event_id, participant_id, payload.knowledge_state, payload.restrictions, _key(idempotency_key))


@router.get("/events/{event_id}/menu")
def get_event_menu(event_id: str, db: Session = Depends(get_db), context: AuthorizedContext = Depends(_context)) -> dict:
    return menu_payload(db, _event(db, event_id, context))


@router.post("/events/{event_id}/menu/revisions")
def post_event_menu(event_id: str, payload: MenuRevisionRequest, idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), db: Session = Depends(get_db), context: AuthorizedContext = Depends(_context)) -> dict:
    return create_menu_revision(db, context, event_id, payload.expected_version, [item.model_dump() for item in payload.items], _key(idempotency_key))


@router.get("/events/{event_id}/shopping")
def get_event_shopping(event_id: str, db: Session = Depends(get_db), context: AuthorizedContext = Depends(_context)) -> dict:
    event = _event(db, event_id, context)
    from app.events.v2_models import EventShoppingDemand
    rows = db.execute(select(EventShoppingDemand).where(EventShoppingDemand.event_id == event.event_id)).scalars().all()
    return {"event_id": event.event_id, "shopping_list_id": None, "items": [{"demand_id": row.demand_id, "display_text": row.display_text, "quantity": row.quantity, "unit": row.unit, "uncertainty": row.uncertainty, "state": row.state} for row in rows]}


@router.post("/events/{event_id}/shopping/generate")
def post_event_shopping(event_id: str, payload: ShoppingGenerateRequest, idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), db: Session = Depends(get_db), context: AuthorizedContext = Depends(_context)) -> dict:
    return generate_shopping(db, context, event_id, [item.model_dump() for item in payload.items], payload.expected_version, _key(idempotency_key))
