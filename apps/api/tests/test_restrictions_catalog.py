from app.nutrition.restrictions_catalog import (
    get_unknown_restrictions,
    list_restrictions_for_ui,
    normalize_restriction_key,
    normalize_restrictions,
)


def test_normalize_no_pork_russian_alias():
    assert normalize_restriction_key("без свинины") == "no_pork"


def test_normalize_halal_english():
    assert normalize_restriction_key("halal") == "halal"


def test_normalize_halal_russian():
    assert normalize_restriction_key("халяль") == "halal"


def test_normalize_gluten_free_russian():
    assert normalize_restriction_key("без глютена") == "gluten_free"


def test_normalize_restrictions_dedupes():
    result = normalize_restrictions(["halal", "халяль", "HALAL", "vegan"])
    assert result == ["halal", "vegan"]


def test_unknown_restriction_does_not_crash():
    assert normalize_restriction_key("totally_unknown_xyz") is None
    assert get_unknown_restrictions(["без свинины", "weird_custom"]) == ["weird_custom"]
    assert normalize_restrictions(["weird_custom", "no_pork"]) == ["no_pork"]


def test_list_restrictions_for_ui_has_russian_labels():
    ui = list_restrictions_for_ui()
    by_key = {item["key"]: item for item in ui}
    assert by_key["no_pork"]["label_ru"] == "Без свинины"
    assert by_key["vegetarian"]["label_ru"] == "Вегетарианское"
    assert all(item["label_ru"] for item in ui)
