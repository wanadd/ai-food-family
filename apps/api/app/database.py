from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    pass


def init_db() -> None:
    from app.models.admin import (  # noqa: F401
        AdminAction,
        AdminErrorLog,
        AdminLoginAttempt,
        AdminSession,
    )
    from app.models.bot_session import TelegramBotSession  # noqa: F401
    from app.models.family_invite import FamilyInvite  # noqa: F401
    from app.models.shopping_category import ShoppingCategory  # noqa: F401
    from app.models import (  # noqa: F401
        family,
        meal_checkin,
        meal_eating_schedule,
        meal_leftover,
        menu_selection,
        notification_settings,
        pantry,
        event_plan,
        recipe,
        shopping_list,
        user,
        user_preferences,
        user_profile,
    )
    from app.models import subscription as subscription_models  # noqa: F401
    from app.models import care as care_models  # noqa: F401
    from app.models import progress as progress_models  # noqa: F401

    from app.database_migrations import ensure_database_schema

    # Legacy tables: SQLAlchemy create_all. Recipe Engine tables: SQL migrations only.
    ensure_database_schema(engine, Base)

    from app.services.recipes import seed_recipes_if_empty
    from app.services.subscription import (
        ensure_all_users_have_billing,
        seed_subscription_plans,
    )

    db = SessionLocal()
    try:
        seed_subscription_plans(db)
        seed_recipes_if_empty(db)
        ensure_all_users_have_billing(db)
    finally:
        db.close()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
