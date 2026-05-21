from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    pass


def init_db() -> None:
    from app.models import (  # noqa: F401
        family,
        menu_selection,
        notification_settings,
        pantry,
        recipe,
        shopping_list,
        user,
        user_preferences,
        user_profile,
    )

    Base.metadata.create_all(bind=engine)

    from app.services.recipes import seed_recipes_if_empty

    db = SessionLocal()
    try:
        seed_recipes_if_empty(db)
    finally:
        db.close()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
