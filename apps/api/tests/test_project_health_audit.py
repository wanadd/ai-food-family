"""Tests for the read-only project health audit script."""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

API_ROOT = Path(__file__).resolve().parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

ROOT = API_ROOT.parents[1]
SCRIPT = ROOT / "backend" / "scripts" / "audit_project_health.py"


def _load_audit_module():
    spec = importlib.util.spec_from_file_location("audit_project_health", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


AUDIT = _load_audit_module()


def test_normalization_layer_importable():
    # The audit should be able to import the unified normalization helpers.
    assert AUDIT.HAVE_NORM is True


def test_suspicious_amount_detection():
    assert AUDIT._is_suspicious_amount("по вкусу шт") is True
    assert AUDIT._is_suspicious_amount("800 г шт") is True
    assert AUDIT._is_suspicious_amount("5 шт") is False
    assert AUDIT._is_suspicious_amount("") is False


def test_valid_time_helper():
    assert AUDIT._is_valid_time("09:00") is True
    assert AUDIT._is_valid_time("99:99") is False


def test_canonical_category_helper():
    assert AUDIT._is_canonical_category("молочные") is True
    assert AUDIT._is_canonical_category("продукты") is False


def test_dirty_list_helper():
    assert AUDIT._has_dirty_list(["a", "a"]) is True
    assert AUDIT._has_dirty_list(["a", ""]) is True
    assert AUDIT._has_dirty_list(["a", "b"]) is False
    assert AUDIT._has_dirty_list([]) is False


def test_iter_menu_ingredients():
    menu = {
        "days": [
            {"meals": [{"ingredients": [{"name": "x", "amount": "2 шт"}]}]},
        ],
        "meals": [{"ingredients": [{"name": "y", "display_amount": "по вкусу"}]}],
    }
    amounts = list(AUDIT._iter_menu_ingredients(menu))
    assert "2 шт" in amounts
    assert "по вкусу" in amounts


def test_static_checks_find_deprecated_routes_and_legacy_services():
    static = AUDIT.run_static_checks()
    # Deprecated route folders exist in this repo (menu, recipes, ...).
    assert "menu" in static["deprecated_route_dirs_present"]
    assert any(
        f.endswith("menu_ai_legacy.py")
        for f in static["legacy_service_files_present"]
    )


def test_build_metrics_shapes_keys():
    metrics = AUDIT.build_metrics(
        {"db_connected": False}, AUDIT.run_static_checks()
    )
    for key in (
        "suspicious_food_count",
        "suspicious_profile_count",
        "suspicious_notification_count",
        "suspicious_subscription_count",
        "deprecated_routes_count",
        "legacy_services_count",
    ):
        assert key in metrics
    assert metrics["deprecated_routes_count"] >= 1
    assert metrics["legacy_services_count"] >= 1
