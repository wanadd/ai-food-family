"""Tests for subscription plan/status normalization."""

from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

API_ROOT = Path(__file__).resolve().parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.services.normalization import subscription as sub  # noqa: E402


def test_known_plan_codes_match_catalog():
    from app.services.subscription_catalog import PLAN_SEEDS

    catalog_codes = {seed["code"] for seed in PLAN_SEEDS}
    assert catalog_codes.issubset(sub.KNOWN_PLAN_CODES)


def test_normalize_plan_code_aliases_and_default():
    assert sub.normalize_plan_code("Premium") == "pro"
    assert sub.normalize_plan_code("basic") == "personal"
    assert sub.normalize_plan_code("") == "start"
    assert sub.normalize_plan_code("personal") == "personal"


def test_is_valid_plan_code():
    assert sub.is_valid_plan_code("pro") is True
    assert sub.is_valid_plan_code("Premium") is True  # alias resolves
    assert sub.is_valid_plan_code("nonsense") is False


def test_normalize_status_aliases():
    assert sub.normalize_status("trialing") == "trial"
    assert sub.normalize_status("canceled") == "cancelled"
    assert sub.normalize_status("") == "active"


def test_is_valid_status():
    assert sub.is_valid_status("active") is True
    assert sub.is_valid_status("trialing") is True
    assert sub.is_valid_status("garbage") is False
