"""Tests for nutrition / shopping grouping / photo readiness pipeline."""

from __future__ import annotations

import sys
from pathlib import Path

from sqlalchemy import create_engine, text

SCRIPTS_DIR = Path(__file__).resolve().parents[3] / "backend" / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import calculate_nutrition as cn  # noqa: E402
import evaluate_photo_prompt_readiness as photo  # noqa: E402
import generate_shopping_list_groups as shop  # noqa: E402
import migrate_to_taste_ingredients as mig  # noqa: E402
import nutrition_data as nd  # noqa: E402
import nutrition_shopping_photo_pipeline as pipe  # noqa: E402


# --------------------------- nutrition_data (pure) ---------------------------

def test_grams_for_exact_mass():
    assert nd.grams_for("Курица", "100", "г") == (100.0, "exact")
    assert nd.grams_for("Мука", "1", "кг") == (1000.0, "exact")


def test_grams_for_volume_and_density():
    grams, hint = nd.grams_for("Вода", "200", "мл")
    assert grams == 200.0 and hint == "exact"
    grams_oil, _ = nd.grams_for("Масло растительное", "100", "мл")
    assert grams_oil == 92.0  # density 0.92


def test_grams_for_spoons_estimated():
    grams, hint = nd.grams_for("Сахар", "1", "ст.л.")
    assert grams == 15.0 and hint == "estimated"


def test_grams_for_piece_needs_weight():
    grams, hint = nd.grams_for("Яйцо куриное", "2", "шт")
    assert grams == 110.0 and hint == "estimated"
    # unknown piece weight -> not invented
    grams2, hint2 = nd.grams_for("Бульон", "1", "шт")
    assert grams2 is None and hint2 == "low_confidence"


def test_compute_row_nutrition_precision_branches():
    exact = nd.compute_row_nutrition("Курица", "100", "г", category="мясо_птица", generic=False, is_to_taste=False)
    assert exact.precision == "exact" and exact.kcal == 190.0

    estimated = nd.compute_row_nutrition("Яйцо куриное", "1", "шт", category="яйца", generic=False, is_to_taste=False)
    assert estimated.precision == "estimated" and estimated.grams == 55.0

    to_taste = nd.compute_row_nutrition("Соль", "по вкусу", "шт", category="специи_соусы", generic=False, is_to_taste=True)
    assert to_taste.precision == "low_confidence" and to_taste.grams is None

    unavailable = nd.compute_row_nutrition("Незнакомка", "1", "шт", category="другое", generic=False, is_to_taste=False)
    assert unavailable.precision == "unavailable" and unavailable.grams is None


# --------------------------- DB fixtures ---------------------------

def _make_engine(url: str = "sqlite:///:memory:"):
    engine = create_engine(url)
    with engine.begin() as conn:
        conn.execute(
            text(
                "CREATE TABLE recipes (id INTEGER PRIMARY KEY, title VARCHAR(200), "
                "servings INTEGER, is_active BOOLEAN, source_type VARCHAR(16))"
            )
        )
        conn.execute(
            text(
                "CREATE TABLE recipe_ingredients (id INTEGER PRIMARY KEY, recipe_id INTEGER, "
                "name VARCHAR(120), quantity VARCHAR(32), unit VARCHAR(32), "
                "category VARCHAR(32), is_optional BOOLEAN, notes VARCHAR(200))"
            )
        )
        conn.execute(
            text(
                "INSERT INTO recipes (id, title, servings, is_active, source_type) VALUES "
                "(1, 'Куриное блюдо', 2, 1, 'v1_import'), (2, 'Manual', 4, 0, 'manual')"
            )
        )
        conn.execute(
            text(
                "INSERT INTO recipe_ingredients (id, recipe_id, name, quantity, unit, category, is_optional, notes) VALUES "
                "(1, 1, 'Курица', '200', 'г', 'мясо_птица', 0, NULL),"
                "(2, 1, 'Картофель', '300', 'г', 'овощи_зелень', 0, NULL),"
                "(3, 1, 'Соль', 'по вкусу', 'шт', 'специи_соусы', 0, NULL),"
                "(4, 1, 'Вода', '200', 'мл', 'напитки', 0, NULL),"
                "(5, 2, 'Соль', 'по вкусу', 'шт', 'специи_соусы', 0, NULL)"
            )
        )
    mig.ensure_quality_columns(engine)
    # populate quality columns first (so pipeline has a baseline to refine from)
    mig.apply_commit(engine, mig.build_proposals(engine, "v1_import"))
    return engine


# --------------------------- nutrition aggregate ---------------------------

def test_load_rows_only_active_v1():
    engine = _make_engine()
    rows = cn.load_rows(engine, "v1_import")
    assert {r.id for r in rows} == {1, 2, 3, 4}  # manual row 5 excluded


def test_aggregate_by_recipe():
    engine = _make_engine()
    rows = cn.load_rows(engine, "v1_import")
    recipes = cn.aggregate_by_recipe(rows)
    assert len(recipes) == 1
    r = recipes[0]
    assert r.kcal > 0
    # salt (to_taste) does not block; water + chicken + potato all quantifiable
    assert r.estimable is True
    assert r.rows_with_grams == 3  # chicken, potato, water (salt has no grams)


# --------------------------- shopping grouping ---------------------------

def test_shopping_summary_counts():
    engine = _make_engine()
    rows = cn.load_rows(engine, "v1_import")
    s = shop.build_summary(rows)
    assert s["hidden"] >= 1  # water hidden
    assert s["to_taste"] >= 1  # salt
    groups = shop.build_recipe_groups(rows)
    assert 1 in groups
    cats = groups[1]["categories"]
    assert "напитки" in cats and cats["напитки"]["hidden"]  # water hidden bucket


# --------------------------- photo readiness ---------------------------

def test_photo_readiness():
    engine = _make_engine()
    rows = cn.load_rows(engine, "v1_import")
    rep = photo.evaluate(rows)
    assert rep["recipes"] == 1
    # chicken + potato visible -> ready
    assert rep["recipe_list"][0]["ready"] is True


# --------------------------- pipeline commit ---------------------------

def test_pipeline_dry_run_does_not_write(tmp_path, monkeypatch):
    engine = _make_engine()
    rows = cn.load_rows(engine, "v1_import")
    before = [(r.id, r.nutrition_precision, r.shopping_priority) for r in rows]
    updates = pipe.proposed_updates(rows)
    # building proposals must not write
    rows_after = cn.load_rows(engine, "v1_import")
    after = [(r.id, r.nutrition_precision, r.shopping_priority) for r in rows_after]
    assert before == after
    assert isinstance(updates, list)


def test_pipeline_commit_idempotent():
    engine = _make_engine()
    rows = cn.load_rows(engine, "v1_import")
    first = pipe.apply_commit(engine, pipe.proposed_updates(rows))
    # re-run computes against fresh DB state -> 0 changes
    rows2 = cn.load_rows(engine, "v1_import")
    second = pipe.apply_commit(engine, pipe.proposed_updates(rows2))
    assert second == 0
    assert first >= 0


def test_pipeline_refines_nutrition_precision():
    engine = _make_engine()
    rows = cn.load_rows(engine, "v1_import")
    pipe.apply_commit(engine, pipe.proposed_updates(rows))
    with engine.connect() as conn:
        chicken = list(
            conn.execute(text("SELECT nutrition_precision FROM recipe_ingredients WHERE id=1"))
        )[0]
    assert chicken[0] == "exact"  # 200 г + facts available


def test_pipeline_does_not_touch_manual():
    engine = _make_engine()
    rows = cn.load_rows(engine, "v1_import")
    pipe.apply_commit(engine, pipe.proposed_updates(rows))
    with engine.connect() as conn:
        manual = list(
            conn.execute(text("SELECT nutrition_precision FROM recipe_ingredients WHERE id=5"))
        )
    # manual row never loaded/updated -> stays whatever migrate left (NULL)
    assert manual[0][0] is None
