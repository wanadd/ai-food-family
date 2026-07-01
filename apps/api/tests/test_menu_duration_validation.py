import pytest
from pydantic import ValidationError

from app.schemas.menu import MenuGenerateRequest


@pytest.mark.parametrize("days", [1, 3, 5, 7])
def test_menu_generate_request_allows_supported_plan_days(days: int) -> None:
    payload = MenuGenerateRequest(plan_days=days)
    assert payload.plan_days == days


@pytest.mark.parametrize("days", [0, 2, 4, 6, 8, 30])
def test_menu_generate_request_rejects_unsupported_plan_days(days: int) -> None:
    with pytest.raises(ValidationError):
        MenuGenerateRequest(plan_days=days)
