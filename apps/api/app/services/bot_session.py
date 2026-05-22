from sqlalchemy.orm import Session

from app.models.bot_session import TelegramBotSession

STATE_AWAITING_INVITE_CONTACT = "awaiting_invite_contact"


def get_session(db: Session, telegram_id: int) -> TelegramBotSession | None:
    return db.get(TelegramBotSession, telegram_id)


def get_or_create_session(db: Session, telegram_id: int) -> TelegramBotSession:
    session = get_session(db, telegram_id)
    if session is None:
        session = TelegramBotSession(telegram_id=telegram_id)
        db.add(session)
        db.commit()
        db.refresh(session)
    return session


def set_session_state(
    db: Session,
    telegram_id: int,
    state: str,
    *,
    invite_token: str | None = None,
) -> TelegramBotSession:
    session = get_or_create_session(db, telegram_id)
    session.state = state
    if invite_token is not None:
        session.invite_token = invite_token
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
        db.commit()
