"""Tests for shopping category deduplication tolerance."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

API_ROOT = Path(__file__).resolve().parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.database import Base  # noqa: E402
from app.models.family import Family  # noqa: E402
from app.models.shopping_category import ShoppingCategory  # noqa: E402
from app.models.user import User  # noqa: E402
from app.services.app_scope import AppScope  # noqa: E402
from app.services.shopping_category_service import (  # noqa: E402
    SYSTEM_CATEGORIES,
    ensure_system_categories,
    get_category_by_slug,
)


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(
        engine,
        tables=[
            User.__table__,
            Family.__table__,
            ShoppingCategory.__table__,
        ],
    )
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()


def test_ensure_system_categories_tolerates_duplicate_rows(db_session):
    scope = AppScope(mode="personal", user_id=42, family_id=None)
    for _ in range(2):
        db_session.add(
            ShoppingCategory(
                slug="продукты",
                name="Продукты",
                icon="🛒",
                is_food=True,
                is_system=True,
                user_id=42,
                family_id=None,
            )
        )
    db_session.commit()

    ensure_system_categories(db_session, scope)

    rows = (
        db_session.query(ShoppingCategory)
        .filter(
            ShoppingCategory.user_id == 42,
            ShoppingCategory.slug == "продукты",
            ShoppingCategory.is_system.is_(True),
        )
        .all()
    )
    assert len(rows) >= 1
    assert get_category_by_slug(db_session, scope, "продукты") is not None


def test_get_category_by_slug_picks_first_when_duplicates(db_session):
    scope = AppScope(mode="personal", user_id=7, family_id=None)
    db_session.add_all(
        [
            ShoppingCategory(
                slug="овощи",
                name="Овощи A",
                is_food=True,
                is_system=False,
                user_id=7,
            ),
            ShoppingCategory(
                slug="овощи",
                name="Овощи B",
                is_food=True,
                is_system=False,
                user_id=7,
            ),
        ]
    )
    db_session.commit()

    cat = get_category_by_slug(db_session, scope, "овощи")
    assert cat is not None
    assert cat.id == min(
        row.id
        for row in db_session.query(ShoppingCategory)
        .filter(ShoppingCategory.user_id == 7, ShoppingCategory.slug == "овощи")
        .all()
    )


def test_find_system_category_by_name_when_slug_differs(db_session):
    scope = AppScope(mode="personal", user_id=99, family_id=None)
    db_session.add(
        ShoppingCategory(
            slug="legacy_slug",
            name="Напитки",
            icon="🥤",
            is_food=True,
            is_system=True,
            user_id=99,
        )
    )
    db_session.commit()

    ensure_system_categories(db_session, scope)

    rows = (
        db_session.query(ShoppingCategory)
        .filter(
            ShoppingCategory.user_id == 99,
            ShoppingCategory.name == "Напитки",
            ShoppingCategory.is_system.is_(True),
        )
        .all()
    )
    assert len(rows) == 1


def test_ensure_system_categories_is_idempotent(db_session):
    scope = AppScope(mode="personal", user_id=55, family_id=None)
    ensure_system_categories(db_session, scope)
    count_after_first = (
        db_session.query(ShoppingCategory)
        .filter(ShoppingCategory.user_id == 55, ShoppingCategory.is_system.is_(True))
        .count()
    )
    ensure_system_categories(db_session, scope)
    count_after_second = (
        db_session.query(ShoppingCategory)
        .filter(ShoppingCategory.user_id == 55, ShoppingCategory.is_system.is_(True))
        .count()
    )
    assert count_after_first == count_after_second
    assert count_after_second == len(SYSTEM_CATEGORIES)
