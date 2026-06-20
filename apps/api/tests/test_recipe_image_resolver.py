"""Tests for title-based recipe id resolution (image pilot hotfix).

Guards against the bug where the pilot JSON ``recipe_id`` (a batch index 1..10)
was used as a DB primary key, assigning images to archived manual recipes.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from sqlalchemy import Boolean, Integer, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

SCRIPTS_DIR = Path(__file__).resolve().parents[3] / "backend" / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from recipe_id_resolver import (  # noqa: E402
    RecipeResolutionError,
    resolve_v1_recipe_id_by_title,
)


class _Base(DeclarativeBase):
    pass


class _Recipe(_Base):
    """Minimal recipes mapping (no JSONB) for dialect-agnostic tests."""

    __tablename__ = "recipes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200))
    source_type: Mapped[str] = mapped_column(String(16), default="manual")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


def _make_session():
    engine = create_engine("sqlite:///:memory:")
    _Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def _seed(session, rows):
    for rid, title, source_type, is_active in rows:
        session.add(
            _Recipe(id=rid, title=title, source_type=source_type, is_active=is_active)
        )
    session.commit()


def test_resolves_to_v1_import_id_not_batch_index():
    session = _make_session()
    # id 1 is an archived manual recipe sharing the title; the resolver must
    # ignore it and return the active v1_import recipe (id 76).
    _seed(
        session,
        [
            (1, "Куриные котлеты с картофельным пюре в духовке", "manual", False),
            (76, "Куриные котлеты с картофельным пюре в духовке", "v1_import", True),
        ],
    )
    rid = resolve_v1_recipe_id_by_title(
        session, _Recipe, "Куриные котлеты с картофельным пюре в духовке"
    )
    assert rid == 76


def test_case_insensitive_match():
    session = _make_session()
    _seed(session, [(80, "Chicken Soup", "v1_import", True)])
    assert resolve_v1_recipe_id_by_title(session, _Recipe, "chicken soup") == 80
    assert resolve_v1_recipe_id_by_title(session, _Recipe, "  CHICKEN SOUP  ") == 80


def test_ignores_inactive_v1_import():
    session = _make_session()
    _seed(
        session,
        [
            (5, "Рыба «Красное и белое»", "v1_import", False),
            (77, "Рыба «Красное и белое»", "v1_import", True),
        ],
    )
    assert (
        resolve_v1_recipe_id_by_title(session, _Recipe, "Рыба «Красное и белое»") == 77
    )


def test_missing_title_raises():
    session = _make_session()
    _seed(session, [(76, "Other dish", "v1_import", True)])
    with pytest.raises(RecipeResolutionError):
        resolve_v1_recipe_id_by_title(session, _Recipe, "Nonexistent dish")


def test_ambiguous_title_raises():
    session = _make_session()
    _seed(
        session,
        [
            (76, "Duplicate dish", "v1_import", True),
            (90, "Duplicate dish", "v1_import", True),
        ],
    )
    with pytest.raises(RecipeResolutionError):
        resolve_v1_recipe_id_by_title(session, _Recipe, "Duplicate dish")


def test_empty_title_raises():
    session = _make_session()
    with pytest.raises(RecipeResolutionError):
        resolve_v1_recipe_id_by_title(session, _Recipe, "")
