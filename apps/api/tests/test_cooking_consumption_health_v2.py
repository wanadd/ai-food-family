from pathlib import Path

from app.cooking.v2_contracts import CookingBatchV2, cooking_completion_creates_consumption
from app.cooking_health.v2_service import _normalize_items
from app.routers.v2_cooking_health import router
from app.v2.errors import V2Error


def test_cooking_completion_never_creates_consumption():
    assert cooking_completion_creates_consumption(CookingBatchV2(cooking_batch_id="batch")) is False


def test_unknown_portion_is_not_zero_or_full():
    items = _normalize_items({"external_description": "restaurant meal"})
    assert items[0]["quantity"] is None


def test_invalid_portion_is_rejected():
    try:
        _normalize_items({"items": [{"display_text": "meal", "quantity": 0}]})
    except V2Error as exc:
        assert exc.code == "validation_error"
    else:
        raise AssertionError("zero portion must be rejected")


def test_w6_migration_has_exact_canonical_tables():
    migration = Path(__file__).parents[1] / "alembic" / "versions" / "20260927_0017_wave_6_cooking_consumption_health.py"
    source = migration.read_text(encoding="utf-8")
    for table in ("cooking_sessions", "prepared_foods", "cooking_events", "consumption_events", "consumption_items", "health_projections", "health_deviations"):
        assert f'"{table}"' in source


def test_w6_router_has_exactly_four_public_routes():
    routes = {(next(iter(route.methods)), route.path) for route in router.routes}
    assert routes == {
        ("POST", "/api/v2/households/{household_id}/cooking-sessions"),
        ("POST", "/api/v2/cooking-sessions/{session_id}/complete"),
        ("POST", "/api/v2/people/{person_id}/meal-checkins"),
        ("GET", "/api/v2/people/{person_id}/health/deviations"),
    }
