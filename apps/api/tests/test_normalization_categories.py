"""Tests for the unified category normalization surface."""

from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

API_ROOT = Path(__file__).resolve().parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.services.normalization import categories  # noqa: E402


def test_legacy_slug_maps_to_canonical():
    assert categories.normalize_category("овощи") == "овощи_зелень"
    assert categories.normalize_category("meat") == "мясо_птица"


def test_forbidden_slug_becomes_default():
    assert categories.normalize_category("продукты") == categories.DEFAULT_CATEGORY_SLUG


def test_infer_category_from_name():
    assert categories.infer_category("Куриная грудка", None) == "мясо_птица"
    assert categories.infer_category("Яйцо куриное", None) == "яйца"


def test_is_valid_category():
    assert categories.is_valid_category("молочные") is True
    assert categories.is_valid_category("продукты") is False
    assert categories.is_valid_category(None) is False


def test_is_deprecated_category():
    assert categories.is_deprecated_category("продукты") is True
    assert categories.is_deprecated_category("заморозка") is True
    assert categories.is_deprecated_category("молочные") is False


def test_shopping_category_override_eggs():
    # eggs must escape a wrong meat hint
    assert categories.normalize_shopping_category("Яйцо куриное", "мясо_птица") == "яйца"
