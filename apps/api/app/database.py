from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    pass


def init_db() -> None:
    from app.models.bot_session import TelegramBotSession  # noqa: F401
    from app.models.family_invite import FamilyInvite  # noqa: F401
    from app.models.shopping_category import ShoppingCategory  # noqa: F401
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

    from app.database_migrations import run_schema_migrations

    run_schema_migrations(engine)

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
