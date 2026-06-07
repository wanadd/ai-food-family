"""Tests for recipe-level nutrition summary calculator + persist script + mapper."""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

from sqlalchemy import create_engine, text

SCRIPTS_DIR = Path(__file__).resolve().parents[3] / "backend" / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import calculate_recipe_nutrition_summary as script  # noqa: E402
import recipe_nutrition_calculator as calc  # noqa: E402

from app.services.recipes.mapper import nutrition_summary  # noqa: E402


# --------------------------- calculator (pure) ---------------------------

def _calc(ings, *, servings=2, meal_type="dinner", category="main"):
    return calc.calculate_recipe_nutrition(
        recipe_id=1,
        title="Тест",
        servings=servings,
        meal_type=meal_type,
        category=category,
        ingredients=ings,
    )


def test_exact_chicken_100g():
    s = _calc([{"name": "Курица", "quantity": "100", "unit": "г", "category": "мясо_птица"}])
    assert s.total["kcal"] == 190.0
    assert s.confidence == "exact"
    assert s.per_serving["kcal"] == 95.0  # 190 / 2 servings


def test_estimated_one_egg():
    s = _calc([{"name": "Яйцо куриное", "quantity": "1", "unit": "шт", "category": "яйца"}])
    assert s.coverage["estimated_ingredients"] == 1
    assert s.confidence in {"estimated", "exact"}
    assert s.total["kcal"] > 0


def test_to_taste_not_counted_as_exact():
    s = _calc(
        [
            {"name": "Курица", "quantity": "100", "unit": "г", "category": "мясо_птица"},
            {"name": "Соль", "quantity": "по вкусу", "unit": "шт",
             "category": "специи_соусы", "is_to_taste": True},
        ]
    )
    # salt excluded from countable; chicken alone -> exact, salt contributes 0
    assert s.coverage["to_taste_ingredients"] == 1
    assert s.coverage["used_ingredients"] == 1
    assert s.total["kcal"] == 190.0


def test_unavailable_product_lowers_confidence():
    s = _calc(
        [
            {"name": "Незнакомый продукт", "quantity": "100", "unit": "г", "category": "другое"},
            {"name": "Ещё незнакомка", "quantity": "50", "unit": "г", "category": "другое"},
        ]
    )
    assert s.confidence == "unavailable"
    assert s.total is None and s.per_serving is None
    assert s.needs_review is True
    assert s.review_reason == "insufficient_data"


def test_generic_lowers_confidence():
    s = _calc(
        [
            {"name": "Курица", "quantity": "100", "unit": "г", "category": "мясо_птица"},
            {"name": "Овощи", "quantity": "200", "unit": "г", "category": "овощи_зелень"},
            {"name": "Мясо", "quantity": "200", "unit": "г", "category": "мясо_птица"},
        ]
    )
    # 2 of 3 are generic (no grams) -> coverage 1/3 -> low confidence / unavailable
    assert s.confidence in {"low_confidence", "unavailable"}


def test_servings_fallback_when_missing():
    s = _calc(
        [{"name": "Курица", "quantity": "100", "unit": "г", "category": "мясо_птица"}],
        servings=0,
        meal_type="snack",
        category="",
    )
    assert s.servings == 1.0  # snack fallback


# --------------------------- DB fixture ---------------------------

def _make_engine(url: str = "sqlite:///:memory:"):
    engine = create_engine(url)
    extra = " ".join(f", {c} FLOAT" for c in (
        "nutrition_kcal_total", "nutrition_protein_total", "nutrition_fat_total",
        "nutrition_carbs_total", "nutrition_kcal_per_serving", "nutrition_protein_per_serving",
        "nutrition_fat_per_serving", "nutrition_carbs_per_serving", "nutrition_servings",
    ))
    with engine.begin() as conn:
        conn.execute(
            text(
                "CREATE TABLE recipes (id INTEGER PRIMARY KEY, title VARCHAR(200), "
                "servings INTEGER, meal_type VARCHAR(32), category VARCHAR(32), "
                "is_active BOOLEAN, source_type VARCHAR(16), ingredients TEXT" + extra
                + ", nutrition_serving_size_text TEXT, nutrition_confidence VARCHAR(24), "
                "nutrition_coverage_json TEXT, nutrition_calculated_at TIMESTAMP, "
                "nutrition_source VARCHAR(64), nutrition_needs_review BOOLEAN, "
                "nutrition_review_reason VARCHAR(64))"
            )
        )
        conn.execute(
            text(
                "CREATE TABLE recipe_ingredients (id INTEGER PRIMARY KEY, recipe_id INTEGER, "
                "name VARCHAR(120), quantity VARCHAR(32), unit VARCHAR(32), "
                "category VARCHAR(32), is_to_taste BOOLEAN, needs_review BOOLEAN)"
            )
        )
        conn.execute(
            text(
                "INSERT INTO recipes (id, title, servings, meal_type, category, is_active, source_type, ingredients) VALUES "
                "(1, 'Куриное блюдо', 2, 'dinner', 'main', 1, 'v1_import', '[]'),"
                "(2, 'Manual', 4, 'lunch', 'main', 0, 'manual', '[]')"
            )
        )
        conn.execute(
            text(
                "INSERT INTO recipe_ingredients (id, recipe_id, name, quantity, unit, category, is_to_taste, needs_review) VALUES "
                "(1, 1, 'Курица', '200', 'г', 'мясо_птица', 0, 0),"
                "(2, 1, 'Картофель', '300', 'г', 'овощи_зелень', 0, 0),"
                "(3, 1, 'Соль', 'по вкусу', 'шт', 'специи_соусы', 1, 0),"
                "(4, 2, 'Курица', '100', 'г', 'мясо_птица', 0, 0)"
            )
        )
    return engine


def test_dry_run_does_not_write_db():
    engine = _make_engine()
    summaries = script.compute_all(engine, "v1_import", None)
    assert len(summaries) == 1  # only active v1_import recipe
    with engine.connect() as conn:
        val = list(conn.execute(text("SELECT nutrition_confidence FROM recipes WHERE id=1")))[0]
    assert val[0] is None  # compute_all never writes


def test_commit_writes_only_nutrition_fields():
    engine = _make_engine()
    summaries = script.compute_all(engine, "v1_import", None)
    changed = script.apply_commit(engine, summaries)
    assert changed == 1
    with engine.connect() as conn:
        row = list(
            conn.execute(
                text(
                    "SELECT title, ingredients, nutrition_confidence, nutrition_kcal_total, "
                    "nutrition_kcal_per_serving, nutrition_source FROM recipes WHERE id=1"
                )
            )
        )[0]
    title, ingredients, confidence, kcal_total, kcal_ps, source = row
    assert title == "Куриное блюдо"  # untouched
    assert ingredients == "[]"  # JSONB untouched
    assert confidence == "exact"
    assert kcal_total and kcal_total > 0
    assert kcal_ps and kcal_ps > 0
    assert source == "planam_v1_nutrition_facts"


def test_commit_idempotent():
    engine = _make_engine()
    summaries = script.compute_all(engine, "v1_import", None)
    first = script.apply_commit(engine, summaries)
    assert first == 1
    summaries2 = script.compute_all(engine, "v1_import", None)
    second = script.apply_commit(engine, summaries2)
    assert second == 0  # nothing changed


def test_commit_does_not_touch_manual_recipes():
    engine = _make_engine()
    script.apply_commit(engine, script.compute_all(engine, "v1_import", None))
    with engine.connect() as conn:
        manual = list(conn.execute(text("SELECT nutrition_confidence FROM recipes WHERE id=2")))[0]
    assert manual[0] is None


# --------------------------- mapper / API serialization ---------------------------

def test_mapper_returns_none_when_not_calculated():
    recipe = SimpleNamespace(nutrition_confidence=None, nutrition_calculated_at=None)
    assert nutrition_summary(recipe) is None


def test_mapper_builds_summary_when_present():
    recipe = SimpleNamespace(
        nutrition_confidence="estimated",
        nutrition_calculated_at=None,
        nutrition_kcal_total=1200.0,
        nutrition_protein_total=50.0,
        nutrition_fat_total=60.0,
        nutrition_carbs_total=120.0,
        nutrition_kcal_per_serving=300.0,
        nutrition_protein_per_serving=12.5,
        nutrition_fat_per_serving=15.0,
        nutrition_carbs_per_serving=30.0,
        nutrition_servings=4.0,
        nutrition_serving_size_text="1 порция",
        nutrition_needs_review=False,
        nutrition_review_reason=None,
    )
    summary = nutrition_summary(recipe)
    assert summary is not None
    assert summary.confidence == "estimated"
    assert summary.kcal_per_serving == 300.0
    assert summary.servings == 4.0


def test_mapper_missing_columns_safe():
    # Older DB row without nutrition columns at all -> getattr default None.
    recipe = SimpleNamespace()
    assert nutrition_summary(recipe) is None
