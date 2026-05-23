from copy import deepcopy
from typing import Any

from sqlalchemy.orm import Session

from app.models.bot_session import TelegramBotSession

STATE_AWAITING_INVITE_CONTACT = "awaiting_invite_contact"
STATE_AWAITING_LEGAL = "awaiting_legal"
STATE_AWAITING_PHONE = "awaiting_phone"
STATE_LEFTOVER_DISH = "leftover_dish"
STATE_LEFTOVER_PORTIONS = "leftover_portions"
STATE_PENDING_CONFIRM = "pending_confirm"


def get_session(db: Session, telegram_id: int) -> TelegramBotSession | None:
    return db.get(TelegramBotSession, telegram_id)


def get_or_create_session(db: Session, telegram_id: int) -> TelegramBotSession:
    session = get_session(db, telegram_id)
    if session is None:
        session = TelegramBotSession(telegram_id=telegram_id, payload_json={})
        db.add(session)
        db.commit()
        db.refresh(session)
    return session


def get_payload(session: TelegramBotSession | None) -> dict[str, Any]:
    if session is None:
        return {}
    data = session.payload_json
    return deepcopy(data) if isinstance(data, dict) else {}


def set_payload(db: Session, telegram_id: int, payload: dict[str, Any]) -> TelegramBotSession:
    session = get_or_create_session(db, telegram_id)
    session.payload_json = payload
    db.commit()
    db.refresh(session)
    return session


def patch_payload(
    db: Session, telegram_id: int, **updates: Any
) -> dict[str, Any]:
    session = get_or_create_session(db, telegram_id)
    data = get_payload(session)
    data.update(updates)
    session.payload_json = data
    db.commit()
    db.refresh(session)
    return data


def set_session_state(
    db: Session,
    telegram_id: int,
    state: str,
    *,
    invite_token: str | None = None,
    payload: dict[str, Any] | None = None,
) -> TelegramBotSession:
    session = get_or_create_session(db, telegram_id)
    session.state = state
    if invite_token is not None:
        session.invite_token = invite_token
    if payload is not None:
        session.payload_json = payload
    db.commit()
    db.refresh(session)
    return session


def clear_invite_token(db: Session, telegram_id: int) -> None:
    session = get_session(db, telegram_id)
    if session:
        session.invite_token = None
        db.commit()


def clear_session_state(db: Session, telegram_id: int) -> None:
    session = get_session(db, telegram_id)
    if session:
        session.state = ""
        session.invite_token = None
        session.payload_json = {}
        db.commit()
