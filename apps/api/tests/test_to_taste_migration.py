"""Tests for the to_taste / ingredient quality migration and readiness report."""

from __future__ import annotations

import sys
from pathlib import Path

from sqlalchemy import create_engine, text

SCRIPTS_DIR = Path(__file__).resolve().parents[3] / "backend" / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import canonical_products as cp  # noqa: E402
import migrate_to_taste_ingredients as mig  # noqa: E402
import report_recipe_readiness as rr  # noqa: E402


# --------------------------- pure rule functions ---------------------------

def test_photo_visibility_hidden_for_seasonings_and_oils():
    assert cp.get_photo_visibility("Соль", "специи_соусы") == "hidden"
    assert cp.get_photo_visibility("Перец черный", "специи_соусы") == "hidden"
    assert cp.get_photo_visibility("Масло растительное", "бакалея") == "hidden"


def test_photo_visibility_visible_for_concrete_products():
    assert cp.get_photo_visibility("Курица", "мясо_птица") == "visible"
    assert cp.get_photo_visibility("Семга", "рыба_морепродукты") == "visible"
    assert cp.get_photo_visibility("Картофель", "овощи_зелень") == "visible"
    assert cp.get_photo_visibility("Овощи", "овощи_зелень", generic=True) == "unsafe"


def test_nutrition_precision_exact_estimated_low():
    assert cp.get_nutrition_precision("Курица", "100", "г", category="мясо_птица") == "exact"
    assert cp.get_nutrition_precision("Яйцо куриное", "1", "шт", category="яйца") == "estimated"
    assert (
        cp.get_nutrition_precision("Соль", "по вкусу", "шт", category="специи_соусы", is_to_taste=True)
        == "low_confidence"
    )


def test_shopping_priority_rules():
    assert cp.get_shopping_priority("Соль", "специи_соусы", is_to_taste=True) == "low"
    assert cp.get_shopping_priority("Перец черный", "специи_соусы") == "low"
    assert cp.get_shopping_priority("Вода", "напитки") == "hidden"
    assert cp.get_shopping_priority("Картофель", "овощи_зелень") == "normal"
    assert cp.get_shopping_priority("Овощи", "овощи_зелень", generic=True) == "optional"


def test_classify_quantity_mode():
    assert cp.classify_quantity_mode("по вкусу") == ("to_taste", True)
    assert cp.classify_quantity_mode("100") == ("exact", False)
    assert cp.classify_quantity_mode("1-2") == ("range", False)


# --------------------------- DB migration flow ---------------------------

def _make_engine(with_quality_cols: bool = False, url: str = "sqlite:///:memory:"):
    engine = create_engine(url)
    quality = ""
    with engine.begin() as conn:
        conn.execute(
            text(
                "CREATE TABLE recipes (id INTEGER PRIMARY KEY, title VARCHAR(200), "
                "is_active BOOLEAN, source_type VARCHAR(16))"
            )
        )
        conn.execute(
            text(
                "CREATE TABLE recipe_ingredients (id INTEGER PRIMARY KEY, recipe_id INTEGER, "
                "name VARCHAR(120), quantity VARCHAR(32), unit VARCHAR(32), "
                "category VARCHAR(32), is_optional BOOLEAN, notes VARCHAR(200)" + quality + ")"
            )
        )
        conn.execute(
            text(
                "INSERT INTO recipes (id, title, is_active, source_type) VALUES "
                "(1, 'Тест', 1, 'v1_import'), (2, 'Manual', 0, 'manual')"
            )
        )
        conn.execute(
            text(
                "INSERT INTO recipe_ingredients (id, recipe_id, name, quantity, unit, category, is_optional, notes) VALUES "
                "(1, 1, 'Соль', 'по вкусу', 'шт', 'специи_соусы', 0, NULL),"
                "(2, 1, 'Курица', '100', 'г', 'мясо_птица', 0, NULL),"
                "(3, 1, 'Вода', '200', 'мл', 'напитки', 0, NULL),"
                "(4, 1, 'Овощи', '1', 'шт', 'овощи_зелень', 0, NULL),"
                "(5, 2, 'Соль', 'по вкусу', 'шт', 'специи_соусы', 0, NULL)"
            )
        )
    if with_quality_cols:
        mig.ensure_quality_columns(engine)
    return engine


def test_ensure_quality_columns_idempotent():
    engine = _make_engine()
    first = mig.ensure_quality_columns(engine)
    assert "is_to_taste" in first
    second = mig.ensure_quality_columns(engine)
    assert second == []  # sqlite: nothing added the second time


def test_dry_run_does_not_write_db():
    engine = _make_engine(with_quality_cols=True)
    mig.build_proposals(engine, "v1_import")  # building proposals never writes
    with engine.connect() as conn:
        row = list(conn.execute(text("SELECT is_to_taste, quantity FROM recipe_ingredients WHERE id=1")))
    assert mig._norm_bool(row[0][0]) is False  # untouched
    assert row[0][1] == "по вкусу"


def test_commit_sets_to_taste_and_preserves_quantity():
    engine = _make_engine(with_quality_cols=True)
    mig.apply_commit(engine, mig.build_proposals(engine, "v1_import"))
    with engine.connect() as conn:
        m = list(
            conn.execute(
                text(
                    "SELECT quantity, quantity_text, is_to_taste, quantity_mode, "
                    "nutrition_precision, shopping_priority, photo_visibility "
                    "FROM recipe_ingredients WHERE id=1"
                )
            )
        )[0]
    quantity, quantity_text, is_to_taste, mode, nutr, shop, photo = m
    assert quantity == "по вкусу"  # NOT erased
    assert quantity_text == "по вкусу"
    assert mig._norm_bool(is_to_taste) is True
    assert mode == "to_taste"
    assert nutr == "low_confidence"  # unit шт + to_taste -> not exact
    assert shop == "low"
    assert photo == "hidden"


def test_commit_water_hidden_and_generic_needs_review():
    engine = _make_engine(with_quality_cols=True)
    mig.apply_commit(engine, mig.build_proposals(engine, "v1_import"))
    with engine.connect() as conn:
        water = list(conn.execute(text("SELECT shopping_priority FROM recipe_ingredients WHERE id=3")))[0]
        veg = list(
            conn.execute(text("SELECT needs_review, photo_visibility FROM recipe_ingredients WHERE id=4"))
        )[0]
    assert water[0] == "hidden"
    assert mig._norm_bool(veg[0]) is True  # generic -> needs_review
    assert veg[1] == "unsafe"


def test_commit_does_not_touch_manual_recipes_and_is_idempotent():
    engine = _make_engine(with_quality_cols=True)
    first = mig.apply_commit(engine, mig.build_proposals(engine, "v1_import"))
    assert first >= 1
    second = mig.apply_commit(engine, mig.build_proposals(engine, "v1_import"))
    assert second == 0  # idempotent

    with engine.connect() as conn:
        manual = list(conn.execute(text("SELECT is_to_taste FROM recipe_ingredients WHERE id=5")))[0]
    assert mig._norm_bool(manual[0]) is False  # manual recipe untouched


def test_manual_review_status_preserved_on_rerun():
    engine = _make_engine(with_quality_cols=True)
    mig.apply_commit(engine, mig.build_proposals(engine, "v1_import"))
    # a human approves the generic row
    with engine.begin() as conn:
        conn.execute(text("UPDATE recipe_ingredients SET manual_review_status='approved' WHERE id=4"))
    # re-run must NOT clobber the human decision
    mig.apply_commit(engine, mig.build_proposals(engine, "v1_import"))
    with engine.connect() as conn:
        status = list(conn.execute(text("SELECT manual_review_status FROM recipe_ingredients WHERE id=4")))[0]
    assert status[0] == "approved"


# --------------------------- readiness report ---------------------------

def test_readiness_report_writes_files(tmp_path, monkeypatch):
    db_url = f"sqlite:///{(tmp_path / 'readiness.db').as_posix()}"
    engine = _make_engine(with_quality_cols=True, url=db_url)
    mig.apply_commit(engine, mig.build_proposals(engine, "v1_import"))

    out_md = tmp_path / "readiness.md"
    out_json = tmp_path / "readiness.json"
    monkeypatch.setattr(rr, "OUT_MD", out_md)
    monkeypatch.setattr(rr, "OUT_JSON", out_json)
    monkeypatch.setattr(sys, "argv", ["report", "--database-url", db_url])

    assert rr.main() == 0
    assert out_md.exists() and out_json.exists()
    assert "Shopping list readiness" in out_md.read_text(encoding="utf-8")


def test_build_report_counts():
    rows = [
        {"recipe_id": 1, "photo_visibility": "visible", "nutrition_precision": "exact",
         "shopping_priority": "normal", "is_to_taste": False, "needs_review_reason": None},
        {"recipe_id": 1, "photo_visibility": "hidden", "nutrition_precision": "low_confidence",
         "shopping_priority": "low", "is_to_taste": True, "needs_review_reason": None},
    ]
    rep = rr.build_report(rows)
    assert rep["total_ingredients"] == 2
    assert rep["shopping_list_readiness"]["normal"] == 1
    assert rep["nutrition_readiness"]["exact"] == 1
    assert rep["photo_prompt_readiness"]["hidden"] == 1
