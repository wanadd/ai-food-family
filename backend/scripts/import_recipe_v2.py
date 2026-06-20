#!/usr/bin/env python3
"""Import Recipe V2 gold recipes (dry-run by default).

Usage:
    python backend/scripts/import_recipe_v2.py --file data/recipe_v2/gold_recipes_30.jsonl
    python backend/scripts/import_recipe_v2.py --file data/recipe_v2/gold_recipes_30.jsonl --apply
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
API_ROOT = ROOT / "apps" / "api"
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.recipes.recipe_v2_validation import validate_recipe_v2  # noqa: E402

REPORT_PATH = ROOT / "reports" / "recipe_rebuild_v2_gold_30_import_report.md"


def load_recipes(path: Path) -> list[dict]:
    if path.suffix == ".jsonl":
        rows: list[dict] = []
        with path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    rows.append(json.loads(line))
        return rows
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return data
    raise ValueError("Expected JSON array or JSONL")


def normalize_title(title: str) -> str:
    return " ".join(title.lower().split())


def map_to_db_recipe(normalized: dict) -> dict:
    meal_type = normalized["meal_types"][0]
    tags = list(normalized.get("tags") or [])
    tags.extend(["recipe_schema_v2", f"status:{normalized.get('status', 'gold')}"])
    return {
        "title": normalized["title"],
        "description": normalized.get("description") or "",
        "meal_type": meal_type,
        "category": normalized.get("category") or "main",
        "difficulty": normalized.get("difficulty") or "easy",
        "prep_time_minutes": normalized.get("prep_time_minutes") or 0,
        "cooking_time_minutes": normalized.get("cook_time_minutes") or 0,
        "servings": normalized.get("servings") or 1,
        "calories_per_serving": (normalized.get("nutrition_summary") or {}).get("calories"),
        "protein_g": (normalized.get("nutrition_summary") or {}).get("protein_g"),
        "fat_g": (normalized.get("nutrition_summary") or {}).get("fat_g"),
        "carbs_g": (normalized.get("nutrition_summary") or {}).get("carbs_g"),
        "fiber_g": (normalized.get("nutrition_summary") or {}).get("fiber_g"),
        "sugar_g": (normalized.get("nutrition_summary") or {}).get("sugar_g"),
        "nutrition_confidence": (normalized.get("nutrition_summary") or {}).get("confidence"),
        "source_type": "seed",
        "image_url": normalized.get("image_url"),
        "diets": normalized.get("diet_tags") or [],
        "tags": tags,
        "ingredients": [
            {
                "name": i["display_name"],
                "amount": f"{i['amount']} {i['unit']}",
                "quantity": str(i["amount"]),
                "unit": i["unit"],
                "category": i.get("shopping_category_slug"),
                "canonical_slug": i.get("canonical_slug"),
                "pantry_category_slug": i.get("pantry_category_slug"),
                "is_optional": i.get("is_optional", False),
            }
            for i in normalized.get("ingredients") or []
        ],
        "steps": [
            s.get("instruction") if isinstance(s, dict) else str(s)
            for s in normalized.get("steps") or []
        ],
    }


def write_report(lines: list[str]) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Import Recipe V2 (dry-run default)")
    parser.add_argument("--file", type=Path, required=True)
    parser.add_argument("--apply", action="store_true", help="Write to DB (default: dry-run)")
    parser.add_argument("--database-url", default=os.getenv("DATABASE_URL"))
    args = parser.parse_args()

    recipes = load_recipes(args.file)
    mode = "apply" if args.apply else "dry-run"
    created = updated = skipped = invalid = 0
    details: list[str] = []

    SessionLocal = Recipe = persist = None
    if args.apply:
        if not args.database_url:
            print("DATABASE_URL required for --apply", file=sys.stderr)
            return 2
        from app.database import SessionLocal as SL
        from app.models.recipe import Recipe as RM
        from app.services.recipe_storage import persist_recipe_structure

        SessionLocal, Recipe, persist = SL, RM, persist_recipe_structure

    db = SessionLocal() if SessionLocal else None
    try:
        for raw in recipes:
            validation = validate_recipe_v2(raw)
            title = raw.get("title") or "(untitled)"
            if not validation["valid"]:
                invalid += 1
                details.append(f"- INVALID `{title}`: {validation['errors']}")
                continue

            norm = validation["normalized_recipe"]
            nt = normalize_title(norm["title"])
            existing = None
            if db is not None:
                for row in db.query(Recipe).filter(Recipe.normalized_title.isnot(None)).all():
                    if normalize_title(row.normalized_title or row.title) == nt:
                        existing = row
                        break
                if existing is None:
                    for row in db.query(Recipe).all():
                        if normalize_title(row.title) == nt:
                            existing = row
                            break

            payload = map_to_db_recipe(norm)
            if existing:
                if args.apply:
                    for key, val in payload.items():
                        setattr(existing, key, val)
                    existing.normalized_title = nt
                    persist(db, existing, ingredients=payload["ingredients"], steps=payload["steps"], tags=payload.get("tags"), allergens=norm.get("allergens") or [], restrictions=norm.get("excludes") or norm.get("religious_tags") or [])
                    db.flush()
                    updated += 1
                    details.append(f"- UPDATED `{title}` (id={existing.id})")
                else:
                    skipped += 1
                    details.append(f"- SKIP duplicate `{title}` (would update id={existing.id})")
            else:
                if args.apply:
                    row = Recipe(**payload, normalized_title=nt)
                    db.add(row)
                    db.flush()
                    persist(db, row, ingredients=payload["ingredients"], steps=payload["steps"], tags=payload.get("tags"), allergens=norm.get("allergens") or [], restrictions=norm.get("excludes") or norm.get("religious_tags") or [])
                    created += 1
                    details.append(f"- CREATED `{title}` (id={row.id})")
                else:
                    created += 1
                    details.append(f"- WOULD CREATE `{title}`")

        if db is not None and args.apply:
            db.commit()
    except Exception as exc:
        if db is not None:
            db.rollback()
        details.append(f"- ERROR: {exc}")
        write_report(
            [
                "# Gold 30 Import Report",
                "",
                f"- Mode: **{mode}**",
                f"- Time: {datetime.now(timezone.utc).isoformat()}",
                f"- Error: `{exc}`",
                "",
                "## Details",
                "",
                *details,
            ]
        )
        raise
    finally:
        if db is not None:
            db.close()

    lines = [
        "# Gold 30 Import Report",
        "",
        f"- Mode: **{mode}**",
        f"- File: `{args.file}`",
        f"- Time: {datetime.now(timezone.utc).isoformat()}",
        f"- Created/would-create: **{created}**",
        f"- Updated: **{updated}**",
        f"- Skipped duplicates: **{skipped}**",
        f"- Invalid: **{invalid}**",
        "",
        "## Details",
        "",
        *details,
        "",
        "## Notes",
        "",
        "- Default mode is dry-run; production apply only on VPS after backup.",
        "- Sets tags `recipe_schema_v2` and `status:gold`.",
    ]
    write_report(lines)
    print(f"Import {mode}: created={created}, updated={updated}, skipped={skipped}, invalid={invalid}")
    print(f"Report: {REPORT_PATH}")
    return 1 if invalid else 0


if __name__ == "__main__":
    raise SystemExit(main())
