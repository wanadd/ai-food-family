#!/usr/bin/env python3
"""Read-only audit of current recipe DB before Recipe Rebuild V2.

STRICTLY READ-ONLY: SELECT queries only. Never UPDATE/DELETE/INSERT.

Run:
    python backend/scripts/audit_recipe_rebuild_v2.py
    python backend/scripts/audit_recipe_rebuild_v2.py --database-url postgresql://...
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, text

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATABASE_URL = "postgresql://aifood:aifood@localhost:5432/aifood"
MD_REPORT = ROOT / "reports" / "recipe_rebuild_v2_current_db_audit.md"
JSON_REPORT = ROOT / "reports" / "recipe_rebuild_v2_current_db_audit.json"

SUSPICIOUS_UNITS = {"", "null", "undefined", "л л", "г г", "гр гр", "шт.", "None"}
BULK_PCS_KEYWORDS = (
    "мук",
    "сахар",
    "греч",
    "рис",
    "овсян",
    "круп",
    "молок",
    "масл",
    "мёд",
    "мед ",
    "вод",
    "мяс",
    "филе",
    "говядин",
    "свинин",
)
OTHER_CATEGORIES = frozenset({"other", "другое", "main", ""})
RESTRICTED_PATTERNS: dict[str, re.Pattern[str]] = {
    "pork": re.compile(r"\b(свинин|бекон|ветчин|сало)\b", re.I),
    "alcohol": re.compile(r"\b(водк|виски|вино|пиво|настойк|лик[её]р|алкогол)\b", re.I),
    "gelatin": re.compile(r"\b(желатин)\b", re.I),
    "beef": re.compile(r"\b(говядин|телят)\b", re.I),
    "seafood": re.compile(r"\b(кревет|лосос|треск|рыб|кальмар|мидии|морепродукт)\b", re.I),
    "spicy": re.compile(r"\b(остр|чили|перец жгуч|кайен)\b", re.I),
    "sugar": re.compile(r"\b(сахар|сироп|конфет)\b", re.I),
}
ALLERGEN_HINTS = re.compile(r"\b(орех|арахис|глютен|молок|яйц|рыб|соя|мед)\b", re.I)
QTY_IN_NAME = re.compile(r"\b\d+([.,]\d+)?\s*(г|кг|мл|л|шт)\b", re.I)
PRESERVE = re.compile(r"\b(консерв|марин|солени|варень|заготовк)\b", re.I)
BAKING_COMPLEX = re.compile(r"\b(безе|меринг|суфле|бrioche|croissant)\b", re.I)
GARBAGE_TITLE = re.compile(r"^(test|undefined|null|\?+|\.+)$", re.I)


def git_info() -> dict[str, str]:
    try:
        branch = subprocess.check_output(
            ["git", "branch", "--show-current"], cwd=ROOT, text=True
        ).strip()
        commit = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True
        ).strip()
        return {"branch": branch, "commit": commit}
    except Exception:
        return {"branch": "unknown", "commit": "unknown"}


def normalize_title(title: str | None) -> str:
    if not title:
        return ""
    t = title.lower().strip()
    t = re.sub(r"[^\w\s-]", "", t, flags=re.UNICODE)
    return re.sub(r"\s+", " ", t)


def has_nutrition(row: dict) -> bool:
    fields = (
        "calories_per_serving",
        "nutrition_kcal_per_serving",
        "protein_g",
        "nutrition_protein_per_serving",
    )
    return any(row.get(f) not in (None, 0, 0.0, "") for f in fields)


def has_steps(row: dict, step_count: int) -> bool:
    if step_count > 0:
        return True
    steps = row.get("steps_json") or row.get("steps")
    if isinstance(steps, list) and any(str(s).strip() for s in steps):
        return True
    return False


def has_photo(row: dict) -> bool:
    for key in ("image_url", "hero_image_url", "thumbnail_url"):
        val = row.get(key)
        if val and str(val).strip():
            return True
    return False


def ingredient_issues(name: str | None, unit: str | None) -> list[str]:
    issues: list[str] = []
    n = (name or "").strip()
    u = (unit or "").strip()
    if not n or n.lower() == "undefined":
        issues.append("bad_name")
    if len(n) > 80:
        issues.append("long_name")
    if QTY_IN_NAME.search(n):
        issues.append("quantity_in_name")
    if not u or u.lower() in {"null", "undefined", "none"}:
        issues.append("bad_unit")
    if u in SUSPICIOUS_UNITS or " " in u and u.replace(" ", "") in {"лл", "гг"}:
        issues.append("suspicious_unit_spelling")
    if u == "шт" and any(k in n.lower() for k in BULK_PCS_KEYWORDS):
        issues.append("pcs_for_bulk_product")
    if re.search(r"\b(г|мл|л|шт)\b", n, re.I) and QTY_IN_NAME.search(n):
        issues.append("unit_in_name")
    return issues


def recipe_suspicion(recipe: dict, ing_count: int, reasons: list[str]) -> list[str]:
    title = recipe.get("title") or ""
    text_blob = title + " " + (recipe.get("description") or "")
    if recipe.get("is_alcoholic"):
        reasons.append("alcoholic")
    if RESTRICTED_PATTERNS["alcohol"].search(text_blob):
        reasons.append("alcohol_keyword")
    if PRESERVE.search(text_blob):
        reasons.append("preserves")
    if BAKING_COMPLEX.search(text_blob):
        reasons.append("complex_baking")
    if GARBAGE_TITLE.match(title.strip()):
        reasons.append("garbage_title")
    if len(title) > 120:
        reasons.append("long_title")
    if ing_count < 2:
        reasons.append("too_few_ingredients")
    if ing_count > 25:
        reasons.append("too_many_ingredients")
    if not has_nutrition(recipe):
        reasons.append("missing_nutrition")
    if not has_photo(recipe):
        reasons.append("missing_photo")
    if str(recipe.get("category") or "").lower() in OTHER_CATEGORIES:
        reasons.append("category_other")
    return reasons


def run_audit(database_url: str) -> dict[str, Any]:
    engine = create_engine(database_url)
    git = git_info()

    with engine.connect() as conn:
        recipe_count = conn.execute(text("SELECT COUNT(*) FROM recipes")).scalar() or 0
        ing_count = conn.execute(text("SELECT COUNT(*) FROM recipe_ingredients")).scalar() or 0

        by_source = dict(
            conn.execute(
                text(
                    "SELECT COALESCE(source_type, 'null'), COUNT(*) "
                    "FROM recipes GROUP BY 1 ORDER BY 2 DESC"
                )
            ).all()
        )

        recipes = [
            dict(r._mapping)
            for r in conn.execute(
                text(
                    """
                    SELECT id, title, normalized_title, description, meal_type, category,
                           source_type, image_url, hero_image_url, thumbnail_url,
                           calories_per_serving, protein_g, fat_g, carbs_g,
                           nutrition_kcal_per_serving, nutrition_protein_per_serving,
                           nutrition_confidence, ingredients, steps, is_alcoholic,
                           servings, difficulty
                    FROM recipes
                    """
                )
            )
        ]

        ingredients = [
            dict(r._mapping)
            for r in conn.execute(
                text(
                    """
                    SELECT ri.id, ri.recipe_id, ri.name, ri.unit, ri.quantity, ri.category
                    FROM recipe_ingredients ri
                    """
                )
            )
        ]

        step_counts = dict(
            conn.execute(
                text("SELECT recipe_id, COUNT(*) FROM recipe_steps GROUP BY recipe_id")
            ).all()
        )

        related_tables: dict[str, int] = {}
        for table in (
            "recipe_collections",
            "collection_recipes",
            "recipe_history",
            "recipe_favorites",
            "recipe_ratings",
            "meal_checkins",
        ):
            try:
                related_tables[table] = conn.execute(
                    text(f"SELECT COUNT(*) FROM {table}")
                ).scalar() or 0
            except Exception:
                related_tables[table] = -1

    no_photo = sum(1 for r in recipes if not has_photo(r))
    no_nutrition = sum(1 for r in recipes if not has_nutrition(r))
    no_steps = sum(
        1 for r in recipes if not has_steps(r, step_counts.get(r["id"], 0))
    )

    unit_counter: Counter[str] = Counter()
    ing_issue_counter: Counter[str] = Counter()
    bad_ing_examples: list[dict] = []
    category_other = Counter()

    recipe_ing_count: Counter[int] = Counter()
    for ing in ingredients:
        unit_counter[(ing.get("unit") or "").strip() or "(empty)"] += 1
        issues = ingredient_issues(ing.get("name"), ing.get("unit"))
        for issue in issues:
            ing_issue_counter[issue] += 1
        if issues and len(bad_ing_examples) < 40:
            bad_ing_examples.append(
                {
                    "recipe_id": ing.get("recipe_id"),
                    "name": ing.get("name"),
                    "unit": ing.get("unit"),
                    "issues": issues,
                }
            )
        rid = ing.get("recipe_id")
        if rid is not None:
            recipe_ing_count[rid] += 1
        cat = (ing.get("category") or "").strip().lower()
        if cat in OTHER_CATEGORIES or cat == "другое":
            category_other[cat or "(empty)"] += 1

    restricted_hits: dict[str, int] = defaultdict(int)
    restricted_examples: dict[str, list[str]] = defaultdict(list)
    suspicious: list[dict] = []

    title_map: dict[str, list[int]] = defaultdict(list)
    for r in recipes:
        nt = normalize_title(r.get("normalized_title") or r.get("title"))
        if nt:
            title_map[nt].append(r["id"])

        blob = (r.get("title") or "") + " " + (r.get("description") or "")
        for key, pattern in RESTRICTED_PATTERNS.items():
            if pattern.search(blob):
                restricted_hits[key] += 1
                if len(restricted_examples[key]) < 5:
                    restricted_examples[key].append(r.get("title") or "")

        reasons: list[str] = []
        recipe_suspicion(r, recipe_ing_count.get(r["id"], 0), reasons)
        if reasons:
            suspicious.append(
                {
                    "id": r["id"],
                    "title": r.get("title"),
                    "source_type": r.get("source_type"),
                    "reasons": reasons,
                    "score": len(reasons),
                }
            )

    duplicates = [
        {"normalized_title": k, "recipe_ids": v, "count": len(v)}
        for k, v in title_map.items()
        if len(v) > 1
    ]
    duplicates.sort(key=lambda x: x["count"], reverse=True)

    suspicious.sort(key=lambda x: x["score"], reverse=True)
    top50 = suspicious[:50]

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "git": git,
        "database_url_redacted": re.sub(r":[^:@/]+@", ":***@", database_url),
        "totals": {
            "recipes": recipe_count,
            "recipe_ingredients": ing_count,
            "no_photo": no_photo,
            "no_nutrition": no_nutrition,
            "no_steps": no_steps,
        },
        "by_source_type": by_source,
        "ingredient_units": dict(unit_counter.most_common()),
        "ingredient_issues": dict(ing_issue_counter),
        "bad_ingredient_examples": bad_ing_examples,
        "category_other_ingredients": dict(category_other),
        "restricted_products": dict(restricted_hits),
        "restricted_examples": dict(restricted_examples),
        "duplicate_titles": duplicates[:30],
        "duplicate_title_count": len(duplicates),
        "suspicious_recipe_count": len(suspicious),
        "top50_suspicious_recipes": top50,
        "related_tables": related_tables,
    }


def write_md(data: dict[str, Any], path: Path) -> None:
    t = data["totals"]
    lines = [
        "# Recipe Rebuild V2 — Current DB Audit",
        "",
        f"- Generated: {data['generated_at']}",
        f"- Git: `{data['git']['branch']}` @ `{data['git']['commit']}`",
        "",
        "## Totals",
        "",
        f"- Recipes: **{t['recipes']}**",
        f"- Recipe ingredients: **{t['recipe_ingredients']}**",
        f"- Without photo: **{t['no_photo']}**",
        f"- Without KBJU: **{t['no_nutrition']}**",
        f"- Without steps: **{t['no_steps']}**",
        "",
        "## By source_type",
        "",
    ]
    for k, v in data["by_source_type"].items():
        lines.append(f"- `{k}`: {v}")
    lines.extend(["", "## Ingredient units (top)", ""])
    for unit, cnt in list(data["ingredient_units"].items())[:25]:
        lines.append(f"- `{unit}`: {cnt}")
    lines.extend(["", "## Ingredient issues", ""])
    for k, v in data["ingredient_issues"].items():
        lines.append(f"- {k}: {v}")
    lines.extend(["", "## Bad ingredient examples", ""])
    for ex in data["bad_ingredient_examples"][:15]:
        lines.append(
            f"- recipe `{ex['recipe_id']}`: `{ex.get('name')}` unit=`{ex.get('unit')}` → {ex['issues']}"
        )
    lines.extend(["", "## Restricted / sensitive products (recipe-level hits)", ""])
    for k, v in data["restricted_products"].items():
        lines.append(f"- {k}: {v}")
    lines.extend(["", "## Duplicate normalized titles", ""])
    lines.append(f"- Duplicate groups: **{data['duplicate_title_count']}**")
    for dup in data["duplicate_titles"][:10]:
        lines.append(f"- `{dup['normalized_title']}` → ids {dup['recipe_ids']}")
    lines.extend(["", "## Top suspicious recipes", ""])
    for row in data["top50_suspicious_recipes"][:20]:
        lines.append(
            f"- [{row['id']}] {row['title']} ({row['source_type']}): {', '.join(row['reasons'])}"
        )
    lines.extend(
        [
            "",
            "## Conclusion",
            "",
            "Current seed/import base contains inconsistent units, incomplete nutrition, "
            "and weak ingredient structure. Rebuild V2 with gold recipes is justified.",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only recipe rebuild V2 audit")
    parser.add_argument("--database-url", default=os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL))
    parser.add_argument("--md-report", type=Path, default=MD_REPORT)
    parser.add_argument("--json-report", type=Path, default=JSON_REPORT)
    args = parser.parse_args()

    try:
        data = run_audit(args.database_url)
    except Exception as exc:
        data = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "git": git_info(),
            "error": str(exc),
            "note": "Run on VPS with DATABASE_URL to populate live audit.",
        }
        args.md_report.parent.mkdir(parents=True, exist_ok=True)
        args.md_report.write_text(
            f"# Recipe Rebuild V2 Audit\n\nDB unavailable locally: `{exc}`\n\n"
            "Run on VPS:\n```bash\npython backend/scripts/audit_recipe_rebuild_v2.py\n```\n",
            encoding="utf-8",
        )
        args.json_report.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Audit failed (expected offline): {exc}")
        return 0

    args.json_report.parent.mkdir(parents=True, exist_ok=True)
    args.json_report.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    write_md(data, args.md_report)
    print(f"Wrote {args.md_report} and {args.json_report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
