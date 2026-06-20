"""Tests for canonical products + ingredient normalization (dry-run/commit)."""

from __future__ import annotations

import json
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
import resync_recipe_ingredients_jsonb as resync  # noqa: E402


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
    canon, changed = cp.normalize_unit("...4 ст.л.")
    assert canon == "ст.л." and changed is True


def test_normalize_quantity_to_taste_and_numbers():
    assert cp.normalize_quantity("по вкусу") == ("", True)
    assert cp.normalize_quantity("немного") == ("", True)
    assert cp.normalize_quantity("") == ("", True)
    assert cp.normalize_quantity("0") == ("", True)
    assert cp.normalize_quantity("1,5") == ("1.5", False)
    assert cp.normalize_quantity("3") == ("3", False)


def test_photo_visibility():
    assert cp.is_photo_visible("Картофель", "овощи_зелень", False, False) is True
    assert cp.is_photo_visible("Соль", "специи_соусы", False, False) is False
    assert cp.is_photo_visible("Овощи", "овощи_зелень", False, True) is False  # generic
    assert cp.is_photo_visible("Помидор", "овощи_зелень", True, False) is False  # to_taste


# --------------------------- normalizer DB flow ---------------------------

def _make_engine():
    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as conn:
        conn.execute(
            text(
                "CREATE TABLE recipes (id INTEGER PRIMARY KEY, title VARCHAR(200), "
                "is_active BOOLEAN, source_type VARCHAR(16), ingredients TEXT)"
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
                "INSERT INTO recipes (id, title, is_active, source_type, ingredients) VALUES "
                "(1, 'Тест рецепт', 1, 'v1_import', '[{\"name\": \"Перец черный\", \"amount\": \"по вкусу гр\"}]'),"
                "(2, 'Manual', 0, 'manual', '[]')"
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


def test_dry_run_does_not_write_db():
    engine = _make_engine()
    before = build_proposals(engine, "v1_import")
    # dry-run = just building proposals, never calling apply_commit
    summarize(before)
    with engine.connect() as conn:
        rows = list(conn.execute(text("SELECT category, unit FROM recipe_ingredients WHERE id=1")))
    assert rows[0] == ("other", "гр")  # untouched


def test_build_proposals_only_active_v1_import():
    engine = _make_engine()
    proposals = build_proposals(engine, "v1_import")
    assert {p.row_id for p in proposals} == {1, 2, 3}


def test_proposals_propose_category_unit_and_flag_to_taste():
    engine = _make_engine()
    proposals = build_proposals(engine, "v1_import")
    by_id = {p.row_id: p for p in proposals}

    assert by_id[1].new_category == "специи_соусы"
    assert by_id[1].new_unit == "г"
    assert by_id[1].to_taste is True
    assert by_id[1].new_quantity == "по вкусу"  # not auto-changed

    assert by_id[2].new_category == "овощи_зелень"

    assert by_id[3].new_category == "другое"
    assert by_id[3].needs_review is True


def test_safe_commit_applies_category_unit_numeric_quantity():
    engine = _make_engine()
    proposals = build_proposals(engine, "v1_import")
    result = apply_commit(engine, proposals)
    assert result.rows_changed >= 1
    with engine.connect() as conn:
        rows = dict(
            (r[0], (r[1], r[2], r[3]))
            for r in conn.execute(
                text("SELECT id, category, unit, quantity FROM recipe_ingredients")
            )
        )
    # category + unit normalized; to_taste quantity preserved
    assert rows[1] == ("специи_соусы", "г", "по вкусу")
    assert rows[2][0] == "овощи_зелень"


def test_commit_never_changes_name():
    engine = _make_engine()
    before_names = None
    with engine.connect() as conn:
        before_names = sorted(r[0] for r in conn.execute(text("SELECT name FROM recipe_ingredients")))
    apply_commit(engine, build_proposals(engine, "v1_import"))
    with engine.connect() as conn:
        after_names = sorted(r[0] for r in conn.execute(text("SELECT name FROM recipe_ingredients")))
    assert before_names == after_names


def test_commit_does_not_touch_manual_recipes():
    engine = _make_engine()
    apply_commit(engine, build_proposals(engine, "v1_import"))
    with engine.connect() as conn:
        row = list(conn.execute(text("SELECT category, unit FROM recipe_ingredients WHERE id=4")))
    assert row[0] == ("specii", "г")  # manual row untouched


def test_commit_is_idempotent():
    engine = _make_engine()
    first = apply_commit(engine, build_proposals(engine, "v1_import"))
    assert first.rows_changed >= 1

    second = apply_commit(engine, build_proposals(engine, "v1_import"))
    assert second.rows_changed == 0

    summary = summarize(build_proposals(engine, "v1_import"))
    assert summary.category_changes == 0
    assert summary.unit_changes == 0


# --------------------------- JSONB resync ---------------------------

def test_resync_dry_run_does_not_write_db():
    engine = _make_engine()
    diffs = resync.build_diffs(engine, "v1_import", None)
    assert any(d.changed for d in diffs)
    with engine.connect() as conn:
        row = list(conn.execute(text("SELECT ingredients FROM recipes WHERE id=1")))
    # JSONB still the original stale value (dry-run never writes)
    assert json.loads(row[0][0]) == [{"name": "Перец черный", "amount": "по вкусу гр"}]


def test_resync_commit_updates_only_jsonb_and_is_idempotent():
    engine = _make_engine()
    # normalize rows first so amounts reflect canonical units
    apply_commit(engine, build_proposals(engine, "v1_import"))

    diffs = resync.build_diffs(engine, "v1_import", None)
    changed = resync.apply_commit(engine, diffs)
    assert changed >= 1

    with engine.connect() as conn:
        ing = json.loads(
            list(conn.execute(text("SELECT ingredients FROM recipes WHERE id=1")))[0][0]
        )
    # rebuilt from rows via honest formatter: name preserved; to_taste drops unit
    names = [i["name"] for i in ing]
    assert names == ["Перец черный", "Картофель", "Загадка"]
    assert ing[0]["amount"] == "по вкусу"  # not "по вкусу г"

    # idempotent: second resync changes nothing
    diffs2 = resync.build_diffs(engine, "v1_import", None)
    assert resync.apply_commit(engine, diffs2) == 0


def test_resync_skips_manual_and_rowless_recipes():
    engine = _make_engine()
    diffs = resync.build_diffs(engine, "v1_import", None)
    # only recipe 1 (active v1_import with rows); manual recipe 2 excluded
    assert {d.recipe_id for d in diffs} == {1}
