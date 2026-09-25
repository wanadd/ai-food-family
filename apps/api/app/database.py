from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings
from app.cutover import application_boundary  # noqa: F401 - installs the mutation boundary

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
        meal_consumption_log,
        meal_consumption_reminder_event,
        cooking_batch,
        external_food_log,
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

    from app.database_migrations import (
        SCHEMA_ADVISORY_LOCK_ID,
        _ensure_database_schema_on_connection,
    )

    # Legacy tables: SQLAlchemy create_all. Recipe Engine tables: SQL migrations only.
    from app.services.recipes import seed_recipes_if_empty
    from app.services.subscription import (
        ensure_all_users_have_billing,
        seed_subscription_plans,
    )

    # Keep schema DDL and all first-boot seed reads/writes under one transaction
    # scoped lock. Releasing the lock before seeding lets another worker run DDL
    # while this worker is reading the catalog, which can deadlock in PostgreSQL.
    with engine.begin() as connection:
        connection.execute(
            text("SELECT pg_advisory_xact_lock(:lock_id)"),
            {"lock_id": SCHEMA_ADVISORY_LOCK_ID},
        )
        _ensure_database_schema_on_connection(connection, Base)
        db = Session(
            bind=connection,
            join_transaction_mode="create_savepoint",
        )
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
