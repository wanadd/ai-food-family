"""Tests for subscription capability gates (Phase 4C)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

API_ROOT = Path(__file__).resolve().parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.services import subscription_capabilities as caps  # noqa: E402


def test_start_trial_profile_limit():
    assert caps.profile_limit_for_tariff("start_trial") == 1


def test_family_pro_has_sport_mode():
    assert caps.has_capability("family_pro", "health_sport_mode") is True


def test_start_trial_no_ai_leftovers():
    assert caps.has_capability("start_trial", "ai_leftovers_suggestions") is False


def test_family_profiles_limit():
    assert caps.profile_limit_for_tariff("family") == 5
