"""Tests for shopping category deduplication tolerance."""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

API_ROOT = Path(__file__).resolve().parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))


def _load_module(name: str, relative_path: str):
    path = API_ROOT / relative_path
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_load_module("app.config", "app/config.py")
_load_module("app.database", "app/database.py")
_load_module("app.models.shopping_category", "app/models/shopping_category.py")
_load_module("app.services.app_scope", "app/services/app_scope.py")
_load_module("app.services.shopping_categories", "app/services/shopping_categories.py")
category_service = _load_module(
    "app.services.shopping_category_service",
    "app/services/shopping_category_service.py",
)

ShoppingCategory = sys.modules["app.models.shopping_category"].ShoppingCategory
AppScope = sys.modules["app.services.app_scope"].AppScope
ensure_system_categories = category_service.ensure_system_categories
get_category_by_slug = category_service.get_category_by_slug

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite:///:memory:")
    ShoppingCategory.__table__.create(engine)
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
    assert count_after_second == len(category_service.SYSTEM_CATEGORIES)
