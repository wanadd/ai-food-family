"""Read-only Gold V3 pilot API contract audit for recipes 256-265."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
REPORTS = ROOT / "reports"
REPORT_JSON = REPORTS / "SPRINT_1_3C_GOLD_V3_API_CONTRACT.json"
REPORT_MD = REPORTS / "SPRINT_1_3C_GOLD_V3_API_CONTRACT.md"
PILOT_IDS = list(range(256, 266))
REQUIRED_TAGS = {"gold_v3", "recipe_schema_v3", "status:gold"}
LEAKAGE_MARKERS = ("povarenok", "поваренок", "source_url", "original_url")
DEFAULT_DATABASE_URL = "postgresql://aifood:aifood@localhost:5432/aifood"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")


def import_sqlalchemy() -> tuple[Any, Any] | None:
    try:
        from sqlalchemy import create_engine, text
    except Exception:
        return None
    return create_engine, text


def redact_url(url: str) -> str:
    if "@" not in url or "://" not in url:
        return url
    scheme = url.split("://", 1)[0]
    return f"{scheme}://***:***@{url.split('@', 1)[1]}"


def row_tags(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return []
        if isinstance(parsed, list):
            return [str(item) for item in parsed]
    return []


def count_json_array(value: Any) -> int:
    if isinstance(value, list):
        return len(value)
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return 0
        return len(parsed) if isinstance(parsed, list) else 0
    return 0


def text_blob(row: dict[str, Any], ingredient_names: list[str], steps: list[str]) -> str:
    parts = [
        row.get("title"),
        row.get("display_title"),
        row.get("description"),
        row.get("normalized_title"),
        *ingredient_names,
        *steps,
    ]
    return " ".join(str(part or "") for part in parts).lower()


def api_visible_payload(row: dict[str, Any], ingredient_names: list[str], steps: list[str]) -> dict[str, Any]:
    """Approximate public recipe payload fields; intentionally excludes DB-only source_url."""
    return {
        "id": row.get("id"),
        "title": row.get("display_title") or row.get("title"),
        "display_title": row.get("display_title"),
        "description": row.get("description") or "",
        "meal_type": row.get("meal_type"),
        "hero_image_url": row.get("hero_image_url"),
        "image_url": row.get("image_url"),
        "thumbnail_url": row.get("thumbnail_url"),
        "ingredients": ingredient_names,
        "steps": steps,
        "source_type": row.get("source_type") or "manual",
        "is_gold_v3": True,
        "recipe_schema": "gold_v3",
        "image_ready": bool(row.get("hero_image_url") or row.get("image_url") or row.get("thumbnail_url")),
    }


def build_report() -> dict[str, Any]:
    database_url = os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL)
    imported = import_sqlalchemy()
    if imported is None:
        return {
            "generated_at": now(),
            "ok": False,
            "db_available": False,
            "error": "sqlalchemy is not importable",
            "database_url": redact_url(database_url),
            "recipes": [],
        }
    create_engine, text = imported
    errors: list[str] = []
    recipes: list[dict[str, Any]] = []
    try:
        engine = create_engine(database_url, pool_pre_ping=True)
        with engine.connect() as conn:
            rows = [
                dict(row._mapping)
                for row in conn.execute(
                    text(
                        """
                        SELECT id, title, display_title, normalized_title, description, meal_type,
                               source_type, tags, source_url, hero_image_url, image_url, thumbnail_url,
                               calories_per_serving, protein_g, fat_g, carbs_g,
                               nutrition_kcal_per_serving, nutrition_protein_per_serving,
                               nutrition_fat_per_serving, nutrition_carbs_per_serving,
                               ingredients, steps
                        FROM recipes
                        WHERE id = ANY(:ids)
                        ORDER BY id
                        """
                    ),
                    {"ids": PILOT_IDS},
                )
            ]
            ingredients_by_id: dict[int, list[str]] = {recipe_id: [] for recipe_id in PILOT_IDS}
            for row in conn.execute(
                text(
                    """
                    SELECT recipe_id, name
                    FROM recipe_ingredients
                    WHERE recipe_id = ANY(:ids)
                    ORDER BY recipe_id, id
                    """
                ),
                {"ids": PILOT_IDS},
            ):
                ingredients_by_id.setdefault(int(row.recipe_id), []).append(str(row.name))
            steps_by_id: dict[int, list[str]] = {recipe_id: [] for recipe_id in PILOT_IDS}
            for row in conn.execute(
                text(
                    """
                    SELECT recipe_id, text
                    FROM recipe_steps
                    WHERE recipe_id = ANY(:ids)
                    ORDER BY recipe_id, step_number
                    """
                ),
                {"ids": PILOT_IDS},
            ):
                steps_by_id.setdefault(int(row.recipe_id), []).append(str(row.text))
    except Exception as exc:
        return {
            "generated_at": now(),
            "ok": False,
            "db_available": False,
            "error": repr(exc),
            "database_url": redact_url(database_url),
            "recipes": [],
        }

    found_ids = {int(row["id"]) for row in rows}
    missing_ids = [recipe_id for recipe_id in PILOT_IDS if recipe_id not in found_ids]
    if missing_ids:
        errors.append(f"Missing pilot IDs: {missing_ids}")
    if len(rows) != 10:
        errors.append(f"Expected 10 rows, got {len(rows)}")

    for row in rows:
        recipe_id = int(row["id"])
        tags = row_tags(row.get("tags"))
        ingredient_names = ingredients_by_id.get(recipe_id) or []
        step_texts = steps_by_id.get(recipe_id) or []
        ingredient_count = len(ingredient_names) or count_json_array(row.get("ingredients"))
        step_count = len(step_texts) or count_json_array(row.get("steps"))
        core_nutrition = all(
            row.get(field) is not None
            for field in ("calories_per_serving", "protein_g", "fat_g", "carbs_g")
        ) or all(
            row.get(field) is not None
            for field in (
                "nutrition_kcal_per_serving",
                "nutrition_protein_per_serving",
                "nutrition_fat_per_serving",
                "nutrition_carbs_per_serving",
            )
        )
        leakage = [
            marker
            for marker in LEAKAGE_MARKERS
            if marker in text_blob(row, ingredient_names, step_texts)
        ]
        item_errors: list[str] = []
        if row.get("source_type") != "seed":
            item_errors.append("source_type is not seed")
        missing_tags = sorted(REQUIRED_TAGS - set(tags))
        if missing_tags:
            item_errors.append(f"missing tags {missing_tags}")
        if not row.get("title") or not row.get("display_title"):
            item_errors.append("title/display_title is empty")
        if not row.get("meal_type"):
            item_errors.append("meal_type is empty")
        if not (row.get("hero_image_url") and row.get("image_url") and row.get("thumbnail_url")):
            item_errors.append("image URL fields incomplete")
        if ingredient_count <= 0:
            item_errors.append("ingredient count is 0")
        if step_count <= 0:
            item_errors.append("steps count is 0")
        if not core_nutrition:
            item_errors.append("nutrition core incomplete")
        if leakage:
            item_errors.append(f"user-facing leakage markers: {leakage}")
        api_payload_text = json.dumps(api_visible_payload(row, ingredient_names, step_texts), ensure_ascii=False).lower()
        if "source_url" in api_payload_text or "original_url" in api_payload_text:
            item_errors.append("source URL leakage in API-visible payload")
        if item_errors:
            errors.append(f"{recipe_id}: {'; '.join(item_errors)}")
        recipes.append(
            {
                "id": recipe_id,
                "title": row.get("title"),
                "display_title": row.get("display_title"),
                "meal_type": row.get("meal_type"),
                "source_type": row.get("source_type"),
                "tags": tags,
                "ingredient_count": ingredient_count,
                "step_count": step_count,
                "image_ready": bool(row.get("hero_image_url") and row.get("image_url") and row.get("thumbnail_url")),
                "nutrition_core_complete": core_nutrition,
                "source_url_db_present": bool(row.get("source_url")),
                "source_url_api_visible": "source_url" in api_payload_text,
                "leakage": leakage,
                "ok": not item_errors,
            }
        )
    return {
        "generated_at": now(),
        "ok": not errors,
        "db_available": True,
        "database_url": redact_url(database_url),
        "expected_ids": PILOT_IDS,
        "found_ids": sorted(found_ids),
        "missing_ids": missing_ids,
        "errors": errors,
        "recipes": recipes,
    }


def render(data: dict[str, Any]) -> str:
    lines = [
        "# Sprint 1.3C Gold V3 API Contract",
        "",
        f"Generated: `{data['generated_at']}`",
        f"OK: `{data.get('ok')}`",
        f"DB available: `{data.get('db_available')}`",
        f"DB URL: `{data.get('database_url')}`",
        f"Missing IDs: `{data.get('missing_ids')}`",
        "",
        "| id | title | source_type | ingredients | steps | image | nutrition | ok |",
        "| --- | --- | --- | ---: | ---: | --- | --- | --- |",
    ]
    for recipe in data.get("recipes", []):
        title = str(recipe.get("title") or "").replace("|", "\\|")
        lines.append(
            f"| {recipe['id']} | {title} | {recipe['source_type']} | {recipe['ingredient_count']} | "
            f"{recipe['step_count']} | {recipe['image_ready']} | {recipe['nutrition_core_complete']} | {recipe['ok']} |"
        )
    if data.get("errors"):
        lines.extend(["", "## Errors", ""])
        lines.extend(f"- {error}" for error in data["errors"])
    return "\n".join(lines) + "\n"


def main() -> int:
    REPORTS.mkdir(exist_ok=True)
    data = build_report()
    write_json(REPORT_JSON, data)
    REPORT_MD.write_text(render(data), encoding="utf-8")
    print(f"Wrote {REPORT_MD}")
    return 0 if data.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
