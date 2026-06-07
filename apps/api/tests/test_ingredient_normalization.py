"""Tests for canonical products + ingredient normalization (dry-run/commit)."""

from __future__ import annotations

import sys
from pathlib import Path

from sqlalchemy import create_engine, text

SCRIPTS_DIR = Path(__file__).resolve().parents[3] / "backend" / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import canonical_products as cp  # noqa: E402
from normalize_recipe_ingredients import (  # noqa: E402
    apply_commit,
    build_proposals,
    summarize,
)


# --------------------------- canonical_products ---------------------------

def test_pepper_family_splits_into_correct_categories():
    assert cp.resolve_product("Перец черный").category == "специи_соусы"
    assert cp.resolve_product("Перец душистый").category == "специи_соусы"
    assert cp.resolve_product("Перец болгарский").category == "овощи_зелень"
    assert cp.resolve_product("Перец сладкий красный").category == "овощи_зелень"


def test_generic_name_flagged():
    овощи = cp.resolve_product("Овощи")
    assert овощи.category == "овощи_зелень"
    assert овощи.generic is True
    assert овощи.nutrition_ready is False


def test_specific_name_nutrition_ready():
    p = cp.resolve_product("Картофель")
    assert p.category == "овощи_зелень"
    assert p.generic is False
    assert p.nutrition_ready is True


def test_normalize_unit_aliases_and_junk():
    assert cp.normalize_unit("гр") == ("г", True)
    assert cp.normalize_unit("грамм") == ("г", True)
    assert cp.normalize_unit("ложка") == ("ст.л.", True)
    assert cp.normalize_unit("пакетик") == ("упаковка", True)
    assert cp.normalize_unit("г") == ("г", False)
    # junk where quantity bled into unit
    canon, changed = cp.normalize_unit("...4 ст.л.")
    assert canon == "ст.л." and changed is True


def test_normalize_quantity_to_taste_and_numbers():
    assert cp.normalize_quantity("по вкусу") == ("", True)
    assert cp.normalize_quantity("немного") == ("", True)
    assert cp.normalize_quantity("") == ("", True)
    assert cp.normalize_quantity("0") == ("", True)
    assert cp.normalize_quantity("1,5") == ("1.5", False)
    assert cp.normalize_quantity("3") == ("3", False)


# --------------------------- normalizer DB flow ---------------------------

def _make_engine():
    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as conn:
        conn.execute(
            text(
                "CREATE TABLE recipes (id INTEGER PRIMARY KEY, is_active BOOLEAN, "
                "source_type VARCHAR(16))"
            )
        )
        conn.execute(
            text(
                "CREATE TABLE recipe_ingredients (id INTEGER PRIMARY KEY, "
                "recipe_id INTEGER, name VARCHAR(120), quantity VARCHAR(32), "
                "unit VARCHAR(32), category VARCHAR(32))"
            )
        )
        conn.execute(
            text(
                "INSERT INTO recipes (id, is_active, source_type) VALUES "
                "(1, 1, 'v1_import'), (2, 0, 'manual')"
            )
        )
        conn.execute(
            text(
                "INSERT INTO recipe_ingredients (id, recipe_id, name, quantity, unit, category) VALUES "
                "(1, 1, 'Перец черный', 'по вкусу', 'гр', 'other'),"
                "(2, 1, 'Картофель', '3', 'шт', 'other'),"
                "(3, 1, 'Загадка', '1', 'ложка', 'other'),"
                "(4, 2, 'Перец черный', '1', 'г', 'specii')"
            )
        )
    return engine


def test_build_proposals_only_active_v1_import():
    engine = _make_engine()
    proposals = build_proposals(engine, "v1_import")
    # row 4 belongs to inactive manual recipe -> excluded
    assert {p.row_id for p in proposals} == {1, 2, 3}


def test_proposals_propose_category_unit_and_flag_to_taste():
    engine = _make_engine()
    proposals = build_proposals(engine, "v1_import")
    by_id = {p.row_id: p for p in proposals}

    # Перец черный -> специи_соусы, unit гр->г, quantity to_taste (kept as-is for commit)
    assert by_id[1].new_category == "специи_соусы"
    assert by_id[1].new_unit == "г"
    assert by_id[1].to_taste is True
    assert by_id[1].new_quantity == "по вкусу"  # not auto-changed

    # Картофель already clean numeric
    assert by_id[2].new_category == "овощи_зелень"

    # Unknown name -> другое + needs_review
    assert by_id[3].new_category == "другое"
    assert by_id[3].needs_review is True


def test_commit_is_idempotent():
    engine = _make_engine()
    proposals = build_proposals(engine, "v1_import")
    changed_first = apply_commit(engine, proposals)
    assert changed_first >= 1

    proposals_again = build_proposals(engine, "v1_import")
    changed_second = apply_commit(engine, proposals_again)
    assert changed_second == 0  # nothing left to change

    summary = summarize(build_proposals(engine, "v1_import"))
    assert summary.category_changes == 0
    assert summary.unit_changes == 0
