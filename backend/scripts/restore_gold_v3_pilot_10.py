"""Restore or dry-run the prod Gold V3 pilot recipes 256-265.

Dry-run is the default. Apply requires --apply and only touches recipes,
recipe_ingredients, and recipe_steps for IDs 256..265.
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
SEED_PATH = ROOT / "data" / "recipe_v2" / "gold_v3_pilot_10_seed.json"
REPORTS = ROOT / "reports"
DRY_RUN_REPORT = REPORTS / "SPRINT_1_3B_GOLD_V3_PILOT_RESTORE_DRY_RUN.md"
APPLY_REPORT = REPORTS / "SPRINT_1_3B_GOLD_V3_PILOT_RESTORE_APPLY.md"
PILOT_IDS = list(range(256, 266))
REQUIRED_TAGS = {"gold_v3", "recipe_schema_v3", "status:gold"}
DEFAULT_DATABASE_URL = "postgresql://aifood:aifood@localhost:5432/aifood"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def fail(message: str) -> None:
    raise SystemExit(message)


def load_seed() -> list[dict[str, Any]]:
    if not SEED_PATH.exists():
        fail(f"Seed file not found: {SEED_PATH}")
    data = json.loads(SEED_PATH.read_text(encoding="utf-8"))
    recipes = data.get("recipes") if isinstance(data, dict) else data
    if not isinstance(recipes, list):
        fail("Seed must be a list or an object with a recipes list.")
    return recipes


def validate_seed(recipes: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    ids = [recipe.get("id") for recipe in recipes]
    if len(recipes) != 10:
        errors.append(f"Expected exactly 10 recipes, got {len(recipes)}.")
    if sorted(ids) != PILOT_IDS:
        errors.append(f"Expected IDs {PILOT_IDS}, got {sorted(ids)}.")
    for recipe in recipes:
        recipe_id = recipe.get("id")
        tags = set(recipe.get("tags") or [])
        missing_tags = sorted(REQUIRED_TAGS - tags)
        if missing_tags:
            errors.append(f"Recipe {recipe_id}: missing tags {missing_tags}.")
        if recipe.get("source_type") != "seed":
            errors.append(f"Recipe {recipe_id}: source_type must be seed.")
        expected_urls = {
            "hero_image_url": f"/recipe-images/{recipe_id}/hero.webp",
            "image_url": f"/recipe-images/{recipe_id}/card_800.webp",
            "thumbnail_url": f"/recipe-images/{recipe_id}/thumb_400.webp",
        }
        for field, expected in expected_urls.items():
            if recipe.get(field) != expected:
                errors.append(f"Recipe {recipe_id}: {field} must be {expected}.")
        if not recipe.get("title"):
            errors.append(f"Recipe {recipe_id}: title is required.")
        if not (recipe.get("ingredient_rows") or recipe.get("ingredients")):
            errors.append(f"Recipe {recipe_id}: at least one ingredient is required.")
        if not (recipe.get("step_rows") or recipe.get("steps")):
            errors.append(f"Recipe {recipe_id}: at least one step is required.")
    return errors


def import_sqlalchemy() -> tuple[Any, Any, Any] | None:
    try:
        from sqlalchemy import create_engine, inspect, text
    except Exception:
        return None
    return create_engine, inspect, text


def redacted_url(url: str) -> str:
    if "@" not in url or "://" not in url:
        return url
    scheme = url.split("://", 1)[0]
    return f"{scheme}://***:***@{url.split('@', 1)[1]}"


def table_columns(inspector: Any, table: str) -> set[str]:
    try:
        return {column["name"] for column in inspector.get_columns(table)}
    except Exception:
        return set()


def normalize_scalar(value: Any) -> Any:
    if value == "":
        return None
    return value


def recipe_payload(recipe: dict[str, Any], columns: set[str]) -> dict[str, Any]:
    allowed = {
        "id",
        "title",
        "original_title",
        "normalized_title",
        "display_title",
        "description",
        "meal_type",
        "category",
        "cuisine",
        "difficulty",
        "cooking_time_minutes",
        "prep_time_minutes",
        "servings",
        "calories_per_serving",
        "protein_g",
        "fat_g",
        "carbs_g",
        "fiber_g",
        "sugar_g",
        "source_type",
        "source_url",
        "image_url",
        "hero_image_url",
        "thumbnail_url",
        "is_drink",
        "is_alcoholic",
        "alcohol_percent",
        "caffeine_mg",
        "suitable_for_children",
        "suitable_for_sport",
        "suitable_for_event",
        "is_active",
        "diets",
        "tags",
        "ingredients",
        "steps",
        "nutrition_kcal_total",
        "nutrition_protein_total",
        "nutrition_fat_total",
        "nutrition_carbs_total",
        "nutrition_kcal_per_serving",
        "nutrition_protein_per_serving",
        "nutrition_fat_per_serving",
        "nutrition_carbs_per_serving",
        "nutrition_servings",
        "nutrition_serving_size_text",
        "nutrition_confidence",
        "nutrition_coverage_json",
        "nutrition_source",
        "nutrition_needs_review",
        "nutrition_review_reason",
        "recipe_yield_amount",
        "recipe_yield_unit",
        "serving_size_amount",
        "serving_size_unit",
        "estimated_servings",
        "yield_type",
    }
    payload = {
        key: normalize_scalar(recipe.get(key))
        for key in sorted(allowed & columns)
        if key in recipe
    }
    payload["id"] = recipe["id"]
    return payload


def ingredient_payload(row: dict[str, Any], columns: set[str]) -> dict[str, Any]:
    allowed = {
        "recipe_id",
        "name",
        "quantity",
        "unit",
        "category",
        "is_optional",
        "notes",
        "quantity_mode",
        "quantity_text",
        "is_to_taste",
        "nutrition_precision",
        "shopping_priority",
        "needs_review",
        "needs_review_reason",
        "photo_visibility",
        "manual_review_status",
    }
    return {
        key: normalize_scalar(row.get(key))
        for key in sorted(allowed & columns)
        if key in row
    }


def step_payload(row: dict[str, Any], columns: set[str]) -> dict[str, Any]:
    allowed = {"recipe_id", "step_number", "text"}
    return {
        key: normalize_scalar(row.get(key))
        for key in sorted(allowed & columns)
        if key in row
    }


def execute_insert(conn: Any, text: Any, table: str, payload: dict[str, Any]) -> None:
    columns = sorted(payload)
    names = ", ".join(columns)
    values = ", ".join(f":{column}" for column in columns)
    conn.execute(text(f"INSERT INTO {table} ({names}) VALUES ({values})"), payload)


def execute_recipe_upsert(conn: Any, text: Any, payload: dict[str, Any]) -> None:
    columns = sorted(payload)
    names = ", ".join(columns)
    values = ", ".join(f":{column}" for column in columns)
    updates = ", ".join(f"{column} = EXCLUDED.{column}" for column in columns if column != "id")
    conn.execute(
        text(
            f"""
            INSERT INTO recipes ({names})
            VALUES ({values})
            ON CONFLICT (id) DO UPDATE SET {updates}
            """
        ),
        payload,
    )


def set_sequence_above_max(conn: Any, text: Any) -> None:
    conn.execute(
        text(
            """
            SELECT setval(
                pg_get_serial_sequence('recipes', 'id'),
                COALESCE((SELECT MAX(id) FROM recipes), 1),
                true
            )
            """
        )
    )


def db_plan(recipes: list[dict[str, Any]], force: bool) -> dict[str, Any]:
    database_url = os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL)
    imported = import_sqlalchemy()
    if imported is None:
        return {
            "db_available": False,
            "error": "sqlalchemy is not importable in this environment",
            "database_url": redacted_url(database_url),
        }
    create_engine, inspect, text = imported
    try:
        engine = create_engine(database_url, pool_pre_ping=True)
        with engine.connect() as conn:
            inspector = inspect(conn)
            recipe_columns = table_columns(inspector, "recipes")
            ingredient_columns = table_columns(inspector, "recipe_ingredients")
            step_columns = table_columns(inspector, "recipe_steps")
            existing = [
                dict(row._mapping)
                for row in conn.execute(
                    text(
                        """
                        SELECT id, title, source_type, tags
                        FROM recipes
                        WHERE id = ANY(:ids)
                        ORDER BY id
                        """
                    ),
                    {"ids": PILOT_IDS},
                )
            ]
            blockers = []
            for row in existing:
                tags_text = json.dumps(row.get("tags") or [], ensure_ascii=False)
                if "gold_v3" not in tags_text:
                    blockers.append(row)
            if blockers and not force:
                blocker_ids = [row["id"] for row in blockers]
                return {
                    "db_available": True,
                    "database_url": redacted_url(database_url),
                    "blocked": True,
                    "blocker_ids": blocker_ids,
                    "existing": existing,
                    "error": "Existing pilot ID rows are not tagged gold_v3. Re-run apply with --force-gold-v3-pilot only after manual review.",
                }
            return {
                "db_available": True,
                "database_url": redacted_url(database_url),
                "blocked": False,
                "existing": existing,
                "missing_ids": [recipe_id for recipe_id in PILOT_IDS if recipe_id not in {row["id"] for row in existing}],
                "recipe_columns": sorted(recipe_columns),
                "ingredient_columns": sorted(ingredient_columns),
                "step_columns": sorted(step_columns),
            }
    except Exception as exc:
        return {
            "db_available": False,
            "database_url": redacted_url(database_url),
            "error": repr(exc),
        }


def apply_restore(recipes: list[dict[str, Any]], force: bool) -> dict[str, Any]:
    database_url = os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL)
    imported = import_sqlalchemy()
    if imported is None:
        fail("sqlalchemy is required for --apply.")
    create_engine, inspect, text = imported
    engine = create_engine(database_url, pool_pre_ping=True)
    with engine.begin() as conn:
        inspector = inspect(conn)
        recipe_columns = table_columns(inspector, "recipes")
        ingredient_columns = table_columns(inspector, "recipe_ingredients")
        step_columns = table_columns(inspector, "recipe_steps")
        plan = db_plan(recipes, force)
        if plan.get("blocked"):
            fail(plan["error"])
        for recipe in recipes:
            execute_recipe_upsert(conn, text, recipe_payload(recipe, recipe_columns))
        conn.execute(text("DELETE FROM recipe_ingredients WHERE recipe_id = ANY(:ids)"), {"ids": PILOT_IDS})
        conn.execute(text("DELETE FROM recipe_steps WHERE recipe_id = ANY(:ids)"), {"ids": PILOT_IDS})
        ingredient_count = 0
        step_count = 0
        for recipe in recipes:
            for ingredient in recipe.get("ingredient_rows") or recipe["ingredients"]:
                payload = ingredient_payload(ingredient, ingredient_columns)
                payload["recipe_id"] = recipe["id"]
                execute_insert(conn, text, "recipe_ingredients", payload)
                ingredient_count += 1
            for step in recipe.get("step_rows") or recipe["steps"]:
                payload = step_payload(step, step_columns)
                payload["recipe_id"] = recipe["id"]
                execute_insert(conn, text, "recipe_steps", payload)
                step_count += 1
        set_sequence_above_max(conn, text)
    return {
        "db_available": True,
        "database_url": redacted_url(database_url),
        "applied": True,
        "recipes_upserted": len(recipes),
        "ingredients_reinserted": ingredient_count,
        "steps_reinserted": step_count,
    }


def render_report(mode: str, seed_errors: list[str], plan: dict[str, Any], recipes: list[dict[str, Any]]) -> str:
    lines = [
        f"# Sprint 1.3B Gold V3 Pilot Restore {mode.title()}",
        "",
        f"Generated: `{now()}`",
        f"Mode: `{mode}`",
        f"Seed: `{SEED_PATH}`",
        f"Seed valid: `{not seed_errors}`",
        f"DB available: `{plan.get('db_available')}`",
        f"DB URL: `{plan.get('database_url')}`",
        "",
        "## Seed",
        "",
        f"- count: `{len(recipes)}`",
        f"- ids: `{[recipe.get('id') for recipe in recipes]}`",
        f"- titles: `{[recipe.get('title') for recipe in recipes]}`",
        "",
        "## DB Plan",
        "",
        f"- blocked: `{plan.get('blocked', False)}`",
        f"- existing: `{[row.get('id') for row in plan.get('existing', [])]}`",
        f"- missing: `{plan.get('missing_ids')}`",
        f"- applied: `{plan.get('applied', False)}`",
        f"- recipes upserted: `{plan.get('recipes_upserted')}`",
        f"- ingredients reinserted: `{plan.get('ingredients_reinserted')}`",
        f"- steps reinserted: `{plan.get('steps_reinserted')}`",
        "",
    ]
    if seed_errors:
        lines.extend(["## Seed Errors", ""])
        lines.extend(f"- {error}" for error in seed_errors)
        lines.append("")
    if plan.get("error"):
        lines.extend(["## DB Error", "", f"`{plan['error']}`", ""])
    lines.append("Only recipe IDs 256-265 are in scope.")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Validate and plan only. This is also the default.")
    parser.add_argument("--apply", action="store_true", help="Apply the idempotent restore.")
    parser.add_argument("--force-gold-v3-pilot", action="store_true", help="Allow replacing existing non-gold rows for IDs 256-265.")
    args = parser.parse_args()
    if args.dry_run and args.apply:
        fail("Use either --dry-run or --apply, not both.")

    REPORTS.mkdir(exist_ok=True)
    recipes = load_seed()
    seed_errors = validate_seed(recipes)
    mode = "apply" if args.apply else "dry-run"
    if seed_errors:
        report = render_report(mode, seed_errors, {}, recipes)
        (APPLY_REPORT if args.apply else DRY_RUN_REPORT).write_text(report, encoding="utf-8")
        fail("Seed validation failed; report written.")

    if args.apply:
        plan = apply_restore(recipes, args.force_gold_v3_pilot)
    else:
        plan = db_plan(recipes, args.force_gold_v3_pilot)
    report = render_report(mode, seed_errors, plan, recipes)
    (APPLY_REPORT if args.apply else DRY_RUN_REPORT).write_text(report, encoding="utf-8")
    print(f"Wrote {APPLY_REPORT if args.apply else DRY_RUN_REPORT}")
    if plan.get("blocked"):
        return 2
    if args.apply and not plan.get("applied"):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
