"""Tests for shopping list cleanup (units, rounding, pantry skip, dedupe)."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

API_ROOT = Path(__file__).resolve().parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.schemas.shopping_list import ShoppingListItem  # noqa: E402
from app.services.shopping_item_utils import (  # noqa: E402
    clean_float,
    normalize_shopping_category,
    normalize_shopping_quantity,
    normalize_shopping_unit,
    parse_shopping_amount,
    should_skip_menu_ingredient_for_shopping,
)
from app.services.shopping_list import build_items_from_ingredients  # noqa: E402
from app.services import shopping_list as shopping_list_service  # noqa: E402


def _ing(name, amount, category=None):
    return SimpleNamespace(name=name, amount=amount, category=category)


def _by_name(items):
    return {i.name.lower(): i for i in items}


# --------------------------- pure helpers ---------------------------

def test_normalize_shopping_unit():
    assert normalize_shopping_unit("пуч.") == "пучок"
    assert normalize_shopping_unit("зуб.") == "зубчик"
    assert normalize_shopping_unit("стак.") == "стакан"
    assert normalize_shopping_unit("упак.") == "упаковка"
    assert normalize_shopping_unit("пакет.") == "пакет"
    assert normalize_shopping_unit("ст. л.") == "ст.л."
    assert normalize_shopping_unit("ч. л.") == "ч.л."
    # already-clean units pass through
    for u in ("г", "кг", "мл", "л", "шт", "ст.л.", "ч.л.", "зубчик", "пучок"):
        assert normalize_shopping_unit(u) == u


def test_clean_float():
    assert clean_float(0.6000000000000001) == 0.6
    assert clean_float(1.7999999999999998) == 1.8
    assert clean_float(2.0) == 2.0
    assert isinstance(clean_float(3.0), float)


def test_fraction_amount_parsing():
    value, unit = parse_shopping_amount("1/2 ст.л.")
    assert value == 0.5
    assert unit == "ст.л."


def test_normalize_quantity_rounds_pieces_up():
    assert normalize_shopping_quantity("0.1", "шт", "x") == ("1", "шт")
    assert normalize_shopping_quantity("0.5", "шт", "x") == ("1", "шт")
    assert normalize_shopping_quantity("1.8", "шт", "x") == ("2", "шт")
    assert normalize_shopping_quantity("5.5", "шт", "x") == ("6", "шт")
    assert normalize_shopping_quantity("0.1", "пуч.", "x") == ("1", "пучок")
    assert normalize_shopping_quantity("0.4", "зуб.", "x") == ("1", "зубчик")


def test_normalize_quantity_keeps_measurements():
    assert normalize_shopping_quantity("125", "г", "x") == ("125", "г")
    assert normalize_shopping_quantity("0.6000000000000001", "кг", "x") == ("0.6", "кг")
    assert normalize_shopping_quantity("2.5", "ст.л.", "x") == ("2.5", "ст.л.")


def test_manual_item_id_helper_is_available_for_create_item():
    assert callable(shopping_list_service.new_manual_item_id)
    assert len(shopping_list_service.new_manual_item_id()) >= 8


def test_normalize_category_overrides():
    assert normalize_shopping_category("Яйцо куриное", "мясо_птица") == "яйца"
    assert normalize_shopping_category("Кальмары", None) == "рыба_морепродукты"
    assert normalize_shopping_category("Молоко", None) == "молочные"
    assert normalize_shopping_category("Грудка куриная", None) == "мясо_птица"


def test_skip_pantry_staples():
    assert should_skip_menu_ingredient_for_shopping("Соль", "7 шт") is True
    assert should_skip_menu_ingredient_for_shopping("Вода", "1 шт") is True
    assert should_skip_menu_ingredient_for_shopping("Перец черный", "0.2 ч.л.", "специи_соусы") is True
    assert should_skip_menu_ingredient_for_shopping("Масло растительное", "по вкусу") is True
    # real products kept
    assert should_skip_menu_ingredient_for_shopping("Майонез", "1 упаковка", "специи_соусы") is False
    assert should_skip_menu_ingredient_for_shopping("Кетчуп", "100 г", "специи_соусы") is False
    assert should_skip_menu_ingredient_for_shopping("Соевый соус", "2.5 ст.л.", "специи_соусы") is False
    assert should_skip_menu_ingredient_for_shopping("Грудка куриная", "125 г") is False


# --------------------------- build pipeline ---------------------------

def test_salt_and_water_excluded():
    items = build_items_from_ingredients([
        _ing("Соль", "7 шт"),
        _ing("Вода", "1 шт"),
        _ing("Грудка куриная", "125 г"),
    ])
    names = {i.name.lower() for i in items}
    assert "соль" not in names
    assert "вода" not in names
    assert "грудка куриная" in names


def test_chicken_breast_grams_not_pieces():
    items = build_items_from_ingredients([_ing("Грудка куриная", "125 г")])
    item = _by_name(items)["грудка куриная"]
    assert item.unit == "г"
    assert item.amount == "125 г"
    assert item.category == "мясо_птица"


def test_carrot_rounds_up():
    items = build_items_from_ingredients([_ing("Морковь", "1.8 шт")])
    assert _by_name(items)["морковь"].amount == "2 шт"


def test_cherry_tomatoes_round_up():
    items = build_items_from_ingredients([_ing("Помидоры черри", "5.5 шт")])
    assert _by_name(items)["помидоры черри"].amount == "6 шт"


def test_micro_greens_excluded():
    items = build_items_from_ingredients([_ing("Петрушка", "0.1 пуч.")])
    assert items == []


def test_greens_one_bunch_kept():
    items = build_items_from_ingredients([_ing("Зелень", "1 пуч.")])
    item = _by_name(items)["зелень"]
    assert item.unit == "пучок"
    assert item.amount == "1 пучок"


def test_identical_items_summed_not_overwritten():
    items = build_items_from_ingredients([
        _ing("Морковь", "1 шт"),
        _ing("Морковь", "1 шт"),
    ])
    assert len(items) == 1
    assert _by_name(items)["морковь"].amount == "2 шт"


def test_no_floating_garbage_in_amount():
    items = build_items_from_ingredients([_ing("Картофель", "0.6000000000000001 кг")])
    item = _by_name(items)["картофель"]
    assert "0.6000000000000001" not in item.amount
    assert item.amount in {"0,6 кг", "0.6 кг"}


def test_checked_state_preserved_on_resync():
    previous = build_items_from_ingredients([_ing("Морковь", "2 шт")])
    checked = previous[0].model_copy(update={"checked": True, "checked_by_user_id": 5})
    items = build_items_from_ingredients([_ing("Морковь", "2 шт")], previous=[checked])
    assert items[0].checked is True
    assert items[0].checked_by_user_id == 5


def test_manual_items_survive_menu_merge():
    # Mirror of sync_from_menu's merge: menu items + manual not already present.
    manual = ShoppingListItem(
        id="manual123456789a", name="Батарейки", category="быт_уборка",
        quantity="2", unit="шт", amount="2 шт", source="manual",
    )
    menu_items = build_items_from_ingredients([_ing("Морковь", "2 шт")], previous=[manual])
    menu_ids = {i.id for i in menu_items}
    merged = menu_items + [manual] if manual.id not in menu_ids else menu_items
    names = {i.name.lower() for i in merged}
    assert "батарейки" in names
    assert "морковь" in names
