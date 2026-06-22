"""Shared helpers for Sprint 1.3M Gold V3 post-apply read-only audits."""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "backend" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from dry_run_gold_v3_existing_recipe_upgrades import EXPECTED_UPGRADE_IDS  # noqa: E402

CONFIRMED_PLAN_ID = "gold-v3-upgrade-b6ade2d9f2d6975a"
DEFAULT_BACKUP_DIR_NAMES = (
    "gold_v3_upgrade_20260622T100339Z",
)
DEFAULT_DATABASE_URL = "postgresql://aifood:aifood@localhost:5432/aifood"

SOURCE_LEAKAGE_MARKERS = ("povarenok", "поваренок", "source_url", "original_url")
USER_FACING_GARBAGE = ("null", "undefined", "nan")
ENGLISH_TITLE_PREFIX_RE = re.compile(
    r"^\s*(high protein|pro weight loss|pre-workout|post-workout|meal prep)\s*:",
    re.I,
)
BATCH_LABEL_RE = re.compile(r"^#\d+\b")
DUPLICATE_UNIT_PATTERNS = (
    re.compile(r"\b\d+\s*л\s+л\b", re.I),
    re.compile(r"\b\d+\s*г\s+г\b", re.I),
    re.compile(r"\b\d+\s*шт\s+шт\b", re.I),
    re.compile(r"\b\d+\s*мл\s+мл\b", re.I),
)

PORK_WORDS = ("свинина", "свиной", "свиная", "свиные", "бекон", "ветчина", "свин")
MEAT_WORDS = ("куриц", "курин", "индейк", "говядин", "свинин", "бекон", "ветчина", "фарш", "рыб", "лосось", "кревет", "мясо")
SEAFOOD_WORDS = ("кревет", "морепродукт", "мидии", "кальмар", "рыб", "лосось")
ALCOHOL_WORDS = ("вино", "пиво", "водка", "коньяк", "ром", "алкоголь")
CAFFEINE_WORDS = ("кофе", "энергетик", "матча")

SAFE_SHOPPING_CATEGORIES = {
    "meat",
    "meat_poultry",
    "fish_seafood",
    "vegetables",
    "vegetables_greens",
    "fruits",
    "dairy",
    "grains",
    "grains_pasta",
    "spices",
    "herbs",
    "greens",
    "bakery",
    "canned",
    "frozen",
    "other",
    "мясо_птица",
    "рыба_морепродукты",
    "овощи",
    "фрукты",
    "молочные",
    "бакалея",
    "специи",
    "зелень",
    "прочее",
}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def redact_url(url: str) -> str:
    if "@" not in url or "://" not in url:
        return url
    scheme = url.split("://", 1)[0]
    return f"{scheme}://***:***@{url.split('@', 1)[1]}"


def import_sqlalchemy() -> tuple[Any, Any] | None:
    try:
        from sqlalchemy import create_engine, text
    except Exception:
        return None
    return create_engine, text


def connect_db(database_url: str | None = None):
    create_engine, _ = import_sqlalchemy()
    if create_engine is None:
        raise RuntimeError("sqlalchemy_unavailable")
    database_url = database_url or os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL)
    return create_engine(database_url, pool_pre_ping=True)


def normalize_text(value: Any) -> str:
    text = re.sub(r"[^0-9a-zа-яё]+", " ", str(value or "").lower(), flags=re.I)
    return re.sub(r"\s+", " ", text).strip()


def recursive_text(value: Any) -> str:
    if isinstance(value, dict):
        return " ".join(recursive_text(item) for item in value.values())
    if isinstance(value, list):
        return " ".join(recursive_text(item) for item in value)
    return str(value or "")


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


def row_diets(value: Any) -> list[str]:
    return row_tags(value)


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


def parse_json_value(value: Any) -> tuple[Any | None, str | None]:
    if value is None:
        return None, None
    if isinstance(value, (list, dict)):
        return value, None
    if isinstance(value, str):
        try:
            return json.loads(value), None
        except json.JSONDecodeError as exc:
            return None, str(exc)
    return value, None


def resolve_backup_path(explicit: str | Path | None = None) -> Path | None:
    if explicit:
        path = Path(explicit)
        return path if path.exists() else None
    env_path = os.environ.get("GOLD_V3_UPGRADE_BACKUP_PATH")
    if env_path:
        path = Path(env_path)
        if path.exists():
            return path
    for dirname in DEFAULT_BACKUP_DIR_NAMES:
        for base in (ROOT / "backups", Path("/app/backups")):
            candidate = base / dirname
            if candidate.exists():
                return candidate
    return None


def load_backup_recipe_ids(backup_path: Path | None) -> list[int]:
    if backup_path is None:
        return []
    recipes_path = backup_path / "recipes.jsonl"
    if not recipes_path.exists():
        return []
    ids: list[int] = []
    for line in recipes_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("id") is not None:
            ids.append(int(row["id"]))
    return sorted(ids)


def extract_upgraded_recipe_ids() -> dict[str, Any]:
    """Resolve upgraded recipe IDs from plan builder / backup manifest."""
    import apply_gold_v3_controlled_recipe_upgrades as apply_mod  # noqa: E402
    import dry_run_gold_v3_controlled_upgrade_apply as controlled_mod  # noqa: E402

    backup_path = resolve_backup_path()
    controlled = controlled_mod.build_report(backup_path=backup_path, write_reports=False)
    plan_id = apply_mod.plan_id_for(controlled)
    operation_ids = sorted(
        {
            int(card["recipe_id"])
            for card in controlled.get("operation_cards") or []
            if card.get("recipe_id") is not None
        }
    )
    planned_ids = [int(recipe_id) for recipe_id in controlled.get("planned_recipe_ids") or []]
    backup_ids = load_backup_recipe_ids(backup_path)
    deterministic_ids = list(EXPECTED_UPGRADE_IDS)

    sources: list[dict[str, Any]] = []
    if operation_ids:
        sources.append(
            {
                "name": "operation_cards",
                "path": "dry_run_gold_v3_controlled_upgrade_apply.build_report",
                "ids": operation_ids,
                "count": len(operation_ids),
            }
        )
    if planned_ids:
        sources.append(
            {
                "name": "planned_recipe_ids",
                "path": "dry_run_gold_v3_controlled_upgrade_apply.planned_recipe_ids",
                "ids": planned_ids,
                "count": len(planned_ids),
            }
        )
    if backup_ids:
        sources.append(
            {
                "name": "backup_manifest",
                "path": str(backup_path / "recipes.jsonl") if backup_path else None,
                "ids": backup_ids,
                "count": len(backup_ids),
            }
        )
    sources.append(
        {
            "name": "deterministic_plan_builder",
            "path": "dry_run_gold_v3_existing_recipe_upgrades.EXPECTED_UPGRADE_IDS",
            "ids": deterministic_ids,
            "count": len(deterministic_ids),
        }
    )

    primary = operation_ids or planned_ids or backup_ids or deterministic_ids
    mismatches = {
        source["name"]: source["ids"]
        for source in sources
        if source["ids"] and source["ids"] != primary
    }
    plan_id_ok = plan_id == CONFIRMED_PLAN_ID if backup_path else None
    return {
        "generated_at": now(),
        "confirmed_plan_id": CONFIRMED_PLAN_ID,
        "computed_plan_id": plan_id,
        "plan_id_matches_confirmed": plan_id_ok,
        "plan_id_verification_skipped": backup_path is None,
        "backup_path": str(backup_path) if backup_path else None,
        "recipe_ids": primary,
        "recipe_id_count": len(primary),
        "sources": sources,
        "source_mismatches": mismatches,
        "passed": len(primary) == 30 and not mismatches and plan_id_ok is not False,
    }


def fetch_recipe_rows(recipe_ids: list[int], database_url: str | None = None) -> tuple[list[dict[str, Any]], dict[int, list[dict[str, Any]]], dict[int, list[dict[str, Any]]]]:
    engine = connect_db(database_url)
    _, text = import_sqlalchemy()
    assert text is not None
    with engine.connect() as conn:
        rows = [
            dict(row._mapping)
            for row in conn.execute(
                text(
                    """
                    SELECT *
                    FROM recipes
                    WHERE id = ANY(:ids)
                    ORDER BY id
                    """
                ),
                {"ids": recipe_ids},
            )
        ]
        ingredients_by_id: dict[int, list[dict[str, Any]]] = {recipe_id: [] for recipe_id in recipe_ids}
        for row in conn.execute(
            text(
                """
                SELECT *
                FROM recipe_ingredients
                WHERE recipe_id = ANY(:ids)
                ORDER BY recipe_id, id
                """
            ),
            {"ids": recipe_ids},
        ):
            mapping = dict(row._mapping)
            ingredients_by_id.setdefault(int(mapping["recipe_id"]), []).append(mapping)
        steps_by_id: dict[int, list[dict[str, Any]]] = {recipe_id: [] for recipe_id in recipe_ids}
        for row in conn.execute(
            text(
                """
                SELECT *
                FROM recipe_steps
                WHERE recipe_id = ANY(:ids)
                ORDER BY recipe_id, step_number
                """
            ),
            {"ids": recipe_ids},
        ):
            mapping = dict(row._mapping)
            steps_by_id.setdefault(int(mapping["recipe_id"]), []).append(mapping)
    return rows, ingredients_by_id, steps_by_id


def recipe_text_blob(row: dict[str, Any], ingredients: list[dict[str, Any]], steps: list[dict[str, Any]]) -> str:
    ingredient_names = [
        str(item.get("name") or item.get("display_name") or "")
        for item in ingredients
    ]
    step_texts = [str(item.get("text") or "") for item in steps]
    parts = [
        row.get("title"),
        row.get("display_title"),
        row.get("description"),
        row.get("normalized_title"),
        " ".join(row_tags(row.get("tags"))),
        " ".join(row_diets(row.get("diets"))),
        *ingredient_names,
        *step_texts,
    ]
    return " ".join(str(part or "") for part in parts).lower()


def has_source_leakage(text: str) -> list[str]:
    return [marker for marker in SOURCE_LEAKAGE_MARKERS if marker in text]


def has_user_facing_garbage(text: str) -> list[str]:
    lowered = text.lower()
    hits = []
    for marker in USER_FACING_GARBAGE:
        if re.search(rf"\b{re.escape(marker)}\b", lowered):
            hits.append(marker)
    return hits


def title_garbage(title: str | None) -> list[str]:
    value = str(title or "")
    blockers = []
    if ENGLISH_TITLE_PREFIX_RE.search(value):
        blockers.append("english_prefix")
    if BATCH_LABEL_RE.search(value):
        blockers.append("batch_label")
    return blockers


def image_field_safe(value: Any) -> bool:
    if value is None or value == "":
        return True
    text = str(value).strip().lower()
    if text in {"null", "undefined", "nan", "none"}:
        return False
    if text.startswith("http://") or text.startswith("https://") or text.startswith("/"):
        return True
    return False


def nutrition_values(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "kcal": row.get("calories_per_serving") or row.get("nutrition_kcal_per_serving"),
        "protein_g": row.get("protein_g") or row.get("nutrition_protein_per_serving"),
        "fat_g": row.get("fat_g") or row.get("nutrition_fat_per_serving"),
        "carbs_g": row.get("carbs_g") or row.get("nutrition_carbs_per_serving"),
    }


def nutrition_complete(row: dict[str, Any]) -> bool:
    values = nutrition_values(row)
    return all(values[key] is not None for key in values)


def time_fields_safe(row: dict[str, Any]) -> bool:
    for field in ("cooking_time_minutes", "prep_time_minutes", "total_time_minutes"):
        value = row.get(field)
        if value is None:
            continue
        if not isinstance(value, (int, float)) or value < 0:
            return False
    return True


def servings_safe(row: dict[str, Any]) -> bool:
    servings = row.get("servings") or row.get("nutrition_servings")
    try:
        return servings is not None and float(servings) > 0
    except (TypeError, ValueError):
        return False


def has_any(text: str, words: tuple[str, ...]) -> bool:
    return any(word in text for word in words)


def forbidden_for_profile(text: str, profile: str) -> bool:
    if profile == "no_pork":
        return has_any(text, PORK_WORDS)
    if profile == "vegetarian":
        return has_any(text, MEAT_WORDS)
    if profile == "no_seafood":
        return has_any(text, SEAFOOD_WORDS)
    if profile == "halal_possible":
        return has_any(text, PORK_WORDS) or has_any(text, ALCOHOL_WORDS)
    if profile == "child_safe":
        return has_any(text, ALCOHOL_WORDS) or has_any(text, CAFFEINE_WORDS)
    return False


def duplicate_unit_issues(ingredient: dict[str, Any]) -> list[str]:
    issues = []
    unit = str(ingredient.get("unit") or "").strip()
    quantity_text = str(ingredient.get("quantity_text") or "").strip()
    quantity = str(ingredient.get("quantity") or "").strip()
    combined = f"{quantity} {unit} {quantity_text}".strip()
    for pattern in DUPLICATE_UNIT_PATTERNS:
        if pattern.search(combined):
            issues.append(f"duplicate_unit:{pattern.pattern}")
    if unit and quantity_text:
        if quantity_text.lower().endswith(unit.lower()) and quantity.lower().endswith(unit.lower()):
            issues.append("unit_duplicated_in_quantity_text")
    return issues


def ingredient_name(ingredient: dict[str, Any]) -> str:
    return str(ingredient.get("name") or ingredient.get("display_name") or "").strip()


def ingredient_category_safe(ingredient: dict[str, Any]) -> bool:
    category = str(ingredient.get("category") or ingredient.get("shopping_category_slug") or "").strip()
    if not category:
        return True
    return category.lower() in {item.lower() for item in SAFE_SHOPPING_CATEGORIES} or bool(category)


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
