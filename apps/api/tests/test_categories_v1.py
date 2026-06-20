"""Tests for PlanAm V1 category taxonomy."""

from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

API_ROOT = Path(__file__).resolve().parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.services.categories_v1 import (  # noqa: E402
    DEPRECATED_SYSTEM_SLUGS,
    FORBIDDEN_CATEGORY_SLUG,
    SYSTEM_CATEGORIES_V1,
    normalize_category_slug,
)


def test_v1_has_fifteen_categories():
    assert len(SYSTEM_CATEGORIES_V1) == 15


def test_forbidden_slugs_not_in_system_categories():
    slugs = {row[0] for row in SYSTEM_CATEGORIES_V1}
    assert FORBIDDEN_CATEGORY_SLUG not in slugs
    assert "заморозка" not in slugs
    assert "сладости" not in slugs


def test_migration_slug_map():
    assert normalize_category_slug("продукты") == "другое"
    assert normalize_category_slug("заморозка") == "бакалея"
    assert normalize_category_slug("сладости") == "бакалея"
    assert normalize_category_slug("животные") == "для_питомцев"
    assert normalize_category_slug("фрукты") == "фрукты_ягоды"
    assert normalize_category_slug("овощи") == "овощи_зелень"


def test_deprecated_system_slugs():
    assert FORBIDDEN_CATEGORY_SLUG in DEPRECATED_SYSTEM_SLUGS
    assert "заморозка" in DEPRECATED_SYSTEM_SLUGS
