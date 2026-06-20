"""Tests for Home 2026 next-action rule engine."""

from app.schemas.menu_overview import HomeNextAction
from app.services.home_next_action import compute_home_next_action


class _Profile:
    nutrition_goal: str | None = None


def test_next_action_priority_nutrition_first(monkeypatch):
    monkeypatch.setattr(
        "app.services.home_next_action.get_or_create_profile",
        lambda db, user: _Profile(),
    )
    monkeypatch.setattr(
        "app.services.home_next_action.is_profile_complete",
        lambda profile: False,
    )
    monkeypatch.setattr(
        "app.services.home_next_action._shopping_unchecked",
        lambda db, user, scope: 0,
    )
    monkeypatch.setattr(
        "app.services.home_next_action._pantry_expiring_preview",
        lambda db, scope: None,
    )

    action, unchecked, pantry = compute_home_next_action(
        None,
        None,
        None,
        has_menu=False,
        today_meal_count=0,
    )
    assert action.id == "complete_nutrition"
    assert unchecked == 0
    assert pantry is None


def test_next_action_shopping_when_menu_exists(monkeypatch):
    monkeypatch.setattr(
        "app.services.home_next_action.get_or_create_profile",
        lambda db, user: type("_", (), {"nutrition_goal": "healthy"})(),
    )
    monkeypatch.setattr(
        "app.services.home_next_action.is_profile_complete",
        lambda profile: True,
    )
    monkeypatch.setattr(
        "app.services.home_next_action._shopping_unchecked",
        lambda db, user, scope: 3,
    )
    monkeypatch.setattr(
        "app.services.home_next_action._pantry_expiring_preview",
        lambda db, scope: None,
    )
    monkeypatch.setattr(
        "app.services.home_next_action._needs_meal_outcome",
        lambda db, scope, count: False,
    )

    action, unchecked, _ = compute_home_next_action(
        None,
        None,
        None,
        has_menu=True,
        today_meal_count=2,
    )
    assert action.id == "shopping"
    assert "3" in action.cta_label
    assert unchecked == 3
