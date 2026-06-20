"""Tests for the read-only ingredient quality audit helpers."""

from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[3] / "backend" / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from audit_recipe_ingredients import (  # noqa: E402
    IngredientRow,
    analyze,
    canonical_unit,
    head_noun,
    is_generic,
    is_valid_quantity,
    normalize_key,
)


def test_normalize_key_collapses_spelling_and_order():
    key = normalize_key("Перец чёрный")
    assert normalize_key("перец черный") == key
    assert normalize_key("Чёрный перец") == key
    assert normalize_key("  чёрный   перец  ") == key


def test_normalize_key_distinguishes_modifiers():
    assert normalize_key("перец черный") != normalize_key("перец молотый")


def test_is_generic():
    assert is_generic("Овощи")
    assert is_generic("зелень")
    assert is_generic("СПЕЦИИ")
    assert not is_generic("Баклажан")
    assert not is_generic("Перец черный")


def test_is_valid_quantity():
    assert is_valid_quantity("3")
    assert is_valid_quantity("1.5")
    assert is_valid_quantity("1,5")
    assert is_valid_quantity("1/2")
    assert is_valid_quantity("1-2")
    assert not is_valid_quantity("")
    assert not is_valid_quantity("0")
    assert not is_valid_quantity("по вкусу")
    assert not is_valid_quantity("немного")
    assert not is_valid_quantity("1 пакетик")


def test_canonical_unit():
    assert canonical_unit("г") == ("г", True)
    assert canonical_unit("шт") == ("шт", True)
    assert canonical_unit("гр") == ("г", False)
    assert canonical_unit("грамм") == ("г", False)
    assert canonical_unit("ложка") == ("ст.л.", False)
    assert canonical_unit("пакетик") == ("упаковка", False)


def test_head_noun_detects_ambiguous_family():
    assert head_noun("Перец черный") == "перец"
    assert head_noun("перец болгарский") == "перец"
    assert head_noun("Масло сливочное") == "масло"


def test_analyze_detects_variants_and_issues():
    rows = [
        IngredientRow(1, "Перец чёрный", "по вкусу", "гр", "other"),
        IngredientRow(1, "перец черный", "1", "г", "specii_sousy"),
        IngredientRow(1, "Перец болгарский", "2", "шт", "ovoshchi_zelen"),
        IngredientRow(2, "Овощи", "0", "шт", "other"),
        IngredientRow(2, "Баклажан", "3", "шт", "ovoshchi_zelen"),
    ]
    result = analyze(rows, recipe_count=2)

    assert result.ingredient_count == 5
    # "Перец чёрный" + "перец черный" collapse to one variant group.
    assert any(len(v) >= 2 for v in result.variant_groups.values())
    # перец family flagged as ambiguous (черный/болгарский under "перец").
    assert "перец" in result.ambiguous_families
    # "Овощи" flagged as generic.
    assert "овощи" in result.generic_names
    # bad quantities: "по вкусу" and "0".
    assert len(result.bad_quantities) == 2
    # dirty unit "гр" detected with canonical suggestion "г".
    assert "гр" in result.dirty_units
    assert result.unit_suggestions.get("гр") == "г"
    # readiness keys present and bounded.
    for key in (
        "normalization_pct",
        "canonical_products_pct",
        "shopping_grouping_pct",
        "nutrition_pct",
        "photo_prompt_pct",
    ):
        assert 0.0 <= result.readiness[key] <= 100.0
