"""Read-only Recipe Gold V3 database state audit.

This script only issues SELECT statements and writes local reports. It is safe
to run when the database is unavailable: the generated report records the error
instead of mutating or repairing anything.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
REPORTS = ROOT / "reports"
DB_JSON = REPORTS / "SPRINT_1_3A_RECIPE_GOLD_V3_DB_STATE.json"
DB_MD = REPORTS / "SPRINT_1_3A_RECIPE_GOLD_V3_DB_STATE.md"
CREATED_IDS_PATH = REPORTS / "recipe_gold_v3_stage_r_created_ids.json"

DEFAULT_DATABASE_URL = "postgresql://aifood:aifood@localhost:5432/aifood"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def json_default(value: Any) -> str:
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2, default=json_default) + "\n",
        encoding="utf-8",
    )


def load_created_ids() -> list[int]:
    if not CREATED_IDS_PATH.exists():
        return []
    try:
        payload = json.loads(CREATED_IDS_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    raw_items = payload.get("created", payload if isinstance(payload, list) else [])
    ids: list[int] = []
    for item in raw_items:
        value = item.get("id") if isinstance(item, dict) else item
        try:
            ids.append(int(value))
        except (TypeError, ValueError):
            continue
    return ids


def import_sqlalchemy() -> tuple[Any, Any, Any] | None:
    try:
        from sqlalchemy import create_engine, inspect, text
    except Exception:
        return None
    return create_engine, inspect, text


def scalar(conn: Any, text: Any, sql: str, params: dict[str, Any] | None = None) -> int:
    value = conn.execute(text(sql), params or {}).scalar()
    return int(value or 0)


def rows(conn: Any, text: Any, sql: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    result = conn.execute(text(sql), params or {})
    return [dict(row._mapping) for row in result]


def table_exists(inspector: Any, name: str) -> bool:
    try:
        return name in inspector.get_table_names()
    except Exception:
        return False


def columns_for(inspector: Any, table: str) -> set[str]:
    try:
        return {column["name"] for column in inspector.get_columns(table)}
    except Exception:
        return set()


def gold_where(recipe_columns: set[str]) -> str:
    parts = []
    if "tags" in recipe_columns:
        parts.append("COALESCE(tags::text, '') ILIKE '%gold_v3%'")
        parts.append("COALESCE(tags::text, '') ILIKE '%schema:recipe_gold_v3%'")
    if "source_type" in recipe_columns:
        parts.append("source_type IN ('import', 'generated_original')")
    if "schema_version" in recipe_columns:
        parts.append("schema_version = 'recipe_gold_v3'")
    return "(" + " OR ".join(parts or ["FALSE"]) + ")"


def recipe_select_sql(recipe_columns: set[str], has_ingredients_table: bool, has_steps_table: bool) -> str:
    def col(name: str, fallback: str = "NULL") -> str:
        return name if name in recipe_columns else fallback

    ingredient_rows = (
        "(SELECT COUNT(*) FROM recipe_ingredients ri WHERE ri.recipe_id = r.id)"
        if has_ingredients_table
        else "0"
    )
    step_rows = (
        "(SELECT COUNT(*) FROM recipe_steps rs WHERE rs.recipe_id = r.id)"
        if has_steps_table
        else "0"
    )
    ingredients_json = (
        "CASE WHEN jsonb_typeof(r.ingredients) = 'array' THEN jsonb_array_length(r.ingredients) ELSE 0 END"
        if "ingredients" in recipe_columns
        else "0"
    )
    steps_json = (
        "CASE WHEN jsonb_typeof(r.steps) = 'array' THEN jsonb_array_length(r.steps) ELSE 0 END"
        if "steps" in recipe_columns
        else "0"
    )
    schema_value = (
        "schema_version"
        if "schema_version" in recipe_columns
        else "CASE WHEN COALESCE(tags::text, '') ILIKE '%schema:recipe_gold_v3%' THEN 'recipe_gold_v3' ELSE NULL END"
    )
    return f"""
        SELECT
            r.id,
            {col('title')} AS title,
            {col('meal_type')} AS meal_type,
            {col('source_type')} AS source_type,
            {schema_value} AS schema_version,
            {col('is_active', 'TRUE')} AS is_active,
            {col('tags')} AS tags,
            {col('hero_image_url')} AS hero_image_url,
            {col('image_url')} AS image_url,
            {col('thumbnail_url')} AS thumbnail_url,
            {col('calories_per_serving')} AS calories_per_serving,
            {col('protein_g')} AS protein_g,
            {col('fat_g')} AS fat_g,
            {col('carbs_g')} AS carbs_g,
            {col('fiber_g')} AS fiber_g,
            {col('sugar_g')} AS sugar_g,
            {col('nutrition_kcal_per_serving')} AS nutrition_kcal_per_serving,
            {col('nutrition_protein_per_serving')} AS nutrition_protein_per_serving,
            {col('nutrition_fat_per_serving')} AS nutrition_fat_per_serving,
            {col('nutrition_carbs_per_serving')} AS nutrition_carbs_per_serving,
            {ingredient_rows} AS ingredient_rows_count,
            {step_rows} AS step_rows_count,
            {ingredients_json} AS ingredients_json_count,
            {steps_json} AS steps_json_count
        FROM recipes r
        WHERE {gold_where(recipe_columns)}
        ORDER BY r.id
    """


def enrich_recipe(row: dict[str, Any]) -> dict[str, Any]:
    ingredients_count = max(int(row.get("ingredient_rows_count") or 0), int(row.get("ingredients_json_count") or 0))
    steps_count = max(int(row.get("step_rows_count") or 0), int(row.get("steps_json_count") or 0))
    has_core_nutrition = all(
        row.get(name) is not None
        for name in ("calories_per_serving", "protein_g", "fat_g", "carbs_g")
    )
    has_extended_nutrition = has_core_nutrition and all(
        row.get(name) is not None for name in ("fiber_g", "sugar_g")
    )
    has_summary_nutrition = all(
        row.get(name) is not None
        for name in (
            "nutrition_kcal_per_serving",
            "nutrition_protein_per_serving",
            "nutrition_fat_per_serving",
            "nutrition_carbs_per_serving",
        )
    )
    image_ready = bool(row.get("hero_image_url") or row.get("image_url") or row.get("thumbnail_url"))
    shopping_ready = ingredients_count > 0
    ui_ready = bool(row.get("title")) and ingredients_count > 0 and steps_count > 0
    menu_ready = ui_ready and bool(row.get("meal_type")) and bool(row.get("is_active"))
    row.update(
        {
            "ingredients_count": ingredients_count,
            "steps_count": steps_count,
            "nutrition_core_complete": has_core_nutrition,
            "nutrition_extended_complete": has_extended_nutrition,
            "nutrition_summary_complete": has_summary_nutrition,
            "ui_ready": ui_ready,
            "menu_ready": menu_ready,
            "shopping_ready": shopping_ready,
            "image_ready": image_ready,
        }
    )
    return row


def unavailable_report(database_url: str, error: str) -> dict[str, Any]:
    return {
        "generated_at": now(),
        "db_available": False,
        "database_url_source": "DATABASE_URL" if os.environ.get("DATABASE_URL") else "default_local",
        "database_url_redacted": redact_url(database_url),
        "error": error,
        "read_only": True,
        "created_ids": load_created_ids(),
        "gold_v3_recipes": [],
        "summary": {},
    }


def redact_url(url: str) -> str:
    if "@" not in url or "://" not in url:
        return url
    prefix, suffix = url.split("@", 1)
    scheme = prefix.split("://", 1)[0]
    return f"{scheme}://***:***@{suffix}"


def build_report() -> dict[str, Any]:
    database_url = os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL)
    imported = import_sqlalchemy()
    if imported is None:
        return unavailable_report(database_url, "sqlalchemy is not importable in this environment")

    create_engine, inspect, text = imported
    created_ids = load_created_ids()
    try:
        engine = create_engine(database_url, pool_pre_ping=True)
        with engine.connect() as conn:
            inspector = inspect(conn)
            if not table_exists(inspector, "recipes"):
                return unavailable_report(database_url, "recipes table does not exist")
            recipe_columns = columns_for(inspector, "recipes")
            has_ingredients_table = table_exists(inspector, "recipe_ingredients")
            has_steps_table = table_exists(inspector, "recipe_steps")
            where = gold_where(recipe_columns)
            summary: dict[str, Any] = {
                "recipes_total": scalar(conn, text, "SELECT COUNT(*) FROM recipes"),
                "schema_version_column_exists": "schema_version" in recipe_columns,
                "gold_v3_candidates": scalar(conn, text, f"SELECT COUNT(*) FROM recipes WHERE {where}"),
                "gold_v3_tagged": scalar(
                    conn,
                    text,
                    "SELECT COUNT(*) FROM recipes WHERE COALESCE(tags::text, '') ILIKE '%gold_v3%'"
                    if "tags" in recipe_columns
                    else "SELECT 0",
                ),
                "schema_recipe_gold_v3_tagged": scalar(
                    conn,
                    text,
                    "SELECT COUNT(*) FROM recipes WHERE COALESCE(tags::text, '') ILIKE '%schema:recipe_gold_v3%'"
                    if "tags" in recipe_columns
                    else "SELECT 0",
                ),
                "source_type_import": scalar(
                    conn,
                    text,
                    "SELECT COUNT(*) FROM recipes WHERE source_type = 'import'"
                    if "source_type" in recipe_columns
                    else "SELECT 0",
                ),
                "source_type_generated_original": scalar(
                    conn,
                    text,
                    "SELECT COUNT(*) FROM recipes WHERE source_type = 'generated_original'"
                    if "source_type" in recipe_columns
                    else "SELECT 0",
                ),
                "with_hero_image_url": scalar(
                    conn,
                    text,
                    f"SELECT COUNT(*) FROM recipes WHERE {where} AND hero_image_url IS NOT NULL AND hero_image_url <> ''"
                    if "hero_image_url" in recipe_columns
                    else "SELECT 0",
                ),
                "with_image_url": scalar(
                    conn,
                    text,
                    f"SELECT COUNT(*) FROM recipes WHERE {where} AND image_url IS NOT NULL AND image_url <> ''"
                    if "image_url" in recipe_columns
                    else "SELECT 0",
                ),
                "with_thumbnail_url": scalar(
                    conn,
                    text,
                    f"SELECT COUNT(*) FROM recipes WHERE {where} AND thumbnail_url IS NOT NULL AND thumbnail_url <> ''"
                    if "thumbnail_url" in recipe_columns
                    else "SELECT 0",
                ),
                "with_recipe_ingredients_rows": scalar(
                    conn,
                    text,
                    f"""
                    SELECT COUNT(DISTINCT r.id)
                    FROM recipes r
                    JOIN recipe_ingredients ri ON ri.recipe_id = r.id
                    WHERE {where}
                    """,
                )
                if has_ingredients_table
                else 0,
                "with_recipe_steps_rows": scalar(
                    conn,
                    text,
                    f"""
                    SELECT COUNT(DISTINCT r.id)
                    FROM recipes r
                    JOIN recipe_steps rs ON rs.recipe_id = r.id
                    WHERE {where}
                    """,
                )
                if has_steps_table
                else 0,
                "with_json_steps": scalar(
                    conn,
                    text,
                    f"""
                    SELECT COUNT(*)
                    FROM recipes
                    WHERE {where}
                    AND jsonb_typeof(steps) = 'array'
                    AND jsonb_array_length(steps) > 0
                    """,
                )
                if "steps" in recipe_columns
                else 0,
                "nutrition_core_complete": scalar(
                    conn,
                    text,
                    f"""
                    SELECT COUNT(*)
                    FROM recipes
                    WHERE {where}
                    AND calories_per_serving IS NOT NULL
                    AND protein_g IS NOT NULL
                    AND fat_g IS NOT NULL
                    AND carbs_g IS NOT NULL
                    """,
                )
                if {"calories_per_serving", "protein_g", "fat_g", "carbs_g"}.issubset(recipe_columns)
                else 0,
                "nutrition_extended_complete": scalar(
                    conn,
                    text,
                    f"""
                    SELECT COUNT(*)
                    FROM recipes
                    WHERE {where}
                    AND calories_per_serving IS NOT NULL
                    AND protein_g IS NOT NULL
                    AND fat_g IS NOT NULL
                    AND carbs_g IS NOT NULL
                    AND fiber_g IS NOT NULL
                    AND sugar_g IS NOT NULL
                    """,
                )
                if {
                    "calories_per_serving",
                    "protein_g",
                    "fat_g",
                    "carbs_g",
                    "fiber_g",
                    "sugar_g",
                }.issubset(recipe_columns)
                else 0,
            }
            recipe_rows = [
                enrich_recipe(row)
                for row in rows(
                    conn,
                    text,
                    recipe_select_sql(recipe_columns, has_ingredients_table, has_steps_table),
                )
            ]
            created_existing: list[int] = []
            created_missing: list[int] = []
            if created_ids:
                existing = {
                    int(row["id"])
                    for row in rows(
                        conn,
                        text,
                        "SELECT id FROM recipes WHERE id = ANY(:ids)",
                        {"ids": created_ids},
                    )
                }
                created_existing = [recipe_id for recipe_id in created_ids if recipe_id in existing]
                created_missing = [recipe_id for recipe_id in created_ids if recipe_id not in existing]
            summary.update(
                {
                    "gold_v3_ui_ready": sum(1 for row in recipe_rows if row["ui_ready"]),
                    "gold_v3_menu_ready": sum(1 for row in recipe_rows if row["menu_ready"]),
                    "gold_v3_shopping_ready": sum(1 for row in recipe_rows if row["shopping_ready"]),
                    "gold_v3_image_ready": sum(1 for row in recipe_rows if row["image_ready"]),
                    "created_ids_total": len(created_ids),
                    "created_ids_existing": len(created_existing),
                    "created_ids_missing": len(created_missing),
                }
            )
            return {
                "generated_at": now(),
                "db_available": True,
                "database_url_source": "DATABASE_URL" if os.environ.get("DATABASE_URL") else "default_local",
                "database_url_redacted": redact_url(database_url),
                "read_only": True,
                "tables": {
                    "recipes": True,
                    "recipe_ingredients": has_ingredients_table,
                    "recipe_steps": has_steps_table,
                },
                "recipe_columns": sorted(recipe_columns),
                "summary": summary,
                "created_ids": created_ids,
                "created_ids_existing": created_existing,
                "created_ids_missing": created_missing,
                "gold_v3_recipes": recipe_rows,
            }
    except Exception as exc:
        return unavailable_report(database_url, repr(exc))


def render_markdown(data: dict[str, Any]) -> str:
    summary = data.get("summary", {})
    lines = [
        "# Sprint 1.3A Recipe Gold V3 DB State",
        "",
        f"Generated: `{data['generated_at']}`",
        f"Read-only: `{data.get('read_only')}`",
        f"DB available: `{data.get('db_available')}`",
        f"Database URL: `{data.get('database_url_redacted')}`",
        "",
    ]
    if not data.get("db_available"):
        lines.extend(
            [
                "## Error",
                "",
                f"`{data.get('error')}`",
                "",
                "No DB mutation was attempted.",
                "",
            ]
        )
        return "\n".join(lines)

    lines.extend(
        [
            "## Summary",
            "",
            f"- recipes total: `{summary.get('recipes_total')}`",
            f"- Gold V3 candidates: `{summary.get('gold_v3_candidates')}`",
            f"- gold_v3 tag: `{summary.get('gold_v3_tagged')}`",
            f"- schema:recipe_gold_v3 tag: `{summary.get('schema_recipe_gold_v3_tagged')}`",
            f"- schema_version column exists: `{summary.get('schema_version_column_exists')}`",
            f"- source_type import: `{summary.get('source_type_import')}`",
            f"- source_type generated_original: `{summary.get('source_type_generated_original')}`",
            f"- created IDs existing/missing: `{summary.get('created_ids_existing')}` / `{summary.get('created_ids_missing')}`",
            f"- UI ready: `{summary.get('gold_v3_ui_ready')}`",
            f"- menu ready: `{summary.get('gold_v3_menu_ready')}`",
            f"- shopping ready: `{summary.get('gold_v3_shopping_ready')}`",
            f"- image ready: `{summary.get('gold_v3_image_ready')}`",
            f"- with hero_image_url: `{summary.get('with_hero_image_url')}`",
            f"- with image_url: `{summary.get('with_image_url')}`",
            f"- with thumbnail_url: `{summary.get('with_thumbnail_url')}`",
            f"- with recipe_ingredients rows: `{summary.get('with_recipe_ingredients_rows')}`",
            f"- with recipe_steps rows: `{summary.get('with_recipe_steps_rows')}`",
            f"- with JSON steps: `{summary.get('with_json_steps')}`",
            f"- nutrition core complete: `{summary.get('nutrition_core_complete')}`",
            f"- nutrition extended complete: `{summary.get('nutrition_extended_complete')}`",
            "",
            "## Gold V3 Recipes",
            "",
            "| id | title | meal_type | source_type | schema | ingredients | steps | ui | menu | shopping | image |",
            "| --- | --- | --- | --- | --- | ---: | ---: | --- | --- | --- | --- |",
        ]
    )
    for recipe in data.get("gold_v3_recipes", []):
        title = str(recipe.get("title") or "").replace("|", "\\|")
        lines.append(
            "| {id} | {title} | {meal_type} | {source_type} | {schema} | {ingredients} | {steps} | {ui} | {menu} | {shopping} | {image} |".format(
                id=recipe.get("id"),
                title=title,
                meal_type=recipe.get("meal_type"),
                source_type=recipe.get("source_type"),
                schema=recipe.get("schema_version"),
                ingredients=recipe.get("ingredients_count"),
                steps=recipe.get("steps_count"),
                ui=recipe.get("ui_ready"),
                menu=recipe.get("menu_ready"),
                shopping=recipe.get("shopping_ready"),
                image=recipe.get("image_ready"),
            )
        )
    lines.extend(["", "No INSERT/UPDATE/DELETE statements are used by this audit."])
    return "\n".join(lines) + "\n"


def main() -> int:
    REPORTS.mkdir(exist_ok=True)
    data = build_report()
    write_json(DB_JSON, data)
    DB_MD.write_text(render_markdown(data), encoding="utf-8")
    print(f"Wrote {DB_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
