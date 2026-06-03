"""P0-5: Recipe write access — admin or user-owned draft only."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

API_ROOT = Path(__file__).resolve().parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.schemas.recipe import RecipeCreateRequest, RecipeUpdateRequest  # noqa: E402
from app.services.recipes import access  # noqa: E402


def _user(user_id: int = 7, telegram_id: int = 100) -> MagicMock:
    user = MagicMock()
    user.id = user_id
    user.telegram_id = telegram_id
    return user


def _recipe(
    *,
    source_type: str = "manual",
    source_url: str | None = None,
    recipe_id: int = 1,
) -> MagicMock:
    recipe = MagicMock()
    recipe.id = recipe_id
    recipe.source_type = source_type
    recipe.source_url = source_url
    return recipe


def test_non_admin_cannot_create_catalog_recipe():
    user = _user()
    payload = RecipeCreateRequest(
        title="Test",
        meal_type="lunch",
        ingredients=[{"name": "a", "amount": "1"}],
        steps=["step"],
        source_type="manual",
    )
    with patch.object(access, "is_admin_user", return_value=False):
        with pytest.raises(HTTPException) as exc:
            access.assert_can_create_recipe(user, payload)
    assert exc.value.status_code == 403


def test_non_admin_can_create_draft_payload():
    user = _user()
    payload = RecipeCreateRequest(
        title="Draft",
        meal_type="lunch",
        ingredients=[{"name": "a", "amount": "1"}],
        steps=["step"],
        source_type="draft",
    )
    with patch.object(access, "is_admin_user", return_value=False):
        access.assert_can_create_recipe(user, payload)


def test_non_admin_cannot_patch_foreign_recipe():
    user = _user(user_id=7)
    recipe = _recipe(source_type="manual")
    payload = RecipeUpdateRequest(title="Hacked")
    with patch.object(access, "is_admin_user", return_value=False):
        with pytest.raises(HTTPException) as exc:
            access.assert_can_update_recipe(user, recipe, payload)
    assert exc.value.status_code == 403


def test_non_admin_can_patch_own_draft():
    user = _user(user_id=7)
    recipe = _recipe(
        source_type="draft",
        source_url=f"{access.DRAFT_OWNER_PREFIX}7",
    )
    payload = RecipeUpdateRequest(title="Updated")
    with patch.object(access, "is_admin_user", return_value=False):
        access.assert_can_update_recipe(user, recipe, payload)


def test_non_admin_cannot_publish_draft():
    user = _user(user_id=7)
    recipe = _recipe(
        source_type="draft",
        source_url=f"{access.DRAFT_OWNER_PREFIX}7",
    )
    payload = RecipeUpdateRequest(is_active=True)
    with patch.object(access, "is_admin_user", return_value=False):
        with pytest.raises(HTTPException) as exc:
            access.assert_can_update_recipe(user, recipe, payload)
    assert exc.value.status_code == 403
