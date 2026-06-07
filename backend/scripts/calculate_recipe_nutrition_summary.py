#!/usr/bin/env python3
"""Persist recipe-level nutrition summary (dry-run / safe-only commit).

Computes KБЖУ totals + per-serving + confidence for active v1_import recipes and
writes them into the additive recipes.nutrition_* columns. Default is dry-run.

    python backend/scripts/calculate_recipe_nutrition_summary.py --dry-run
    python backend/scripts/calculate_recipe_nutrition_summary.py --dry-run --limit 20
    python backend/scripts/calculate_recipe_nutrition_summary.py --commit --safe-only

SAFE: only writes nutrition_* columns, never touches title / ingredients / steps
/ images / JSONB / recipe_ingredients. Idempotent — re-run changes 0 rows
(nutrition_calculated_at is only bumped when the computed content actually
changes).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import bindparam, create_engine, text

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from recipe_nutrition_calculator import (  # noqa: E402
    NUTRITION_SOURCE,
    RecipeNutritionSummary,
    calculate_recipe_nutrition,
)

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATABASE_URL = "postgresql://aifood:aifood@localhost:5432/aifood"
REPORTS = ROOT / "reports"
DRY_MD = REPORTS / "recipe_nutrition_summary_dry_run.md"
DRY_JSON = REPORTS / "recipe_nutrition_summary_dry_run.json"
COMMIT_MD = REPORTS / "recipe_nutrition_summary_commit.md"
COMMIT_JSON = REPORTS / "recipe_nutrition_summary_commit.json"

MAIN_DISH_MEALS = {"lunch", "dinner"}
MAIN_DISH_CATEGORIES = {"soup", "main", "salad"}

# Columns written on commit (content) + calculated_at handled separately.
_CONTENT_COLUMNS = [
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
    "nutrition_source",
    "nutrition_needs_review",
    "nutrition_review_reason",
]


def _b(v) -> bool:
    return bool(v) if v is not None else False


def load_recipes(engine, source_type: str, limit: int | None) -> list[dict]:
    query = (
        "SELECT id, title, servings, meal_type, category "
        "FROM recipes WHERE is_active = TRUE AND source_type = :source_type "
        "ORDER BY id"
    )
    if limit:
        query += f" LIMIT {int(limit)}"
    with engine.connect() as conn:
        return [dict(m) for m in conn.execute(text(query), {"source_type": source_type}).mappings()]


def load_ingredients(engine, recipe_ids: list[int]) -> dict[int, list[dict]]:
    if not recipe_ids:
        return {}
    out: dict[int, list[dict]] = {rid: [] for rid in recipe_ids}
    query = text(
        "SELECT recipe_id, name, quantity, unit, category, is_to_taste, needs_review "
        "FROM recipe_ingredients WHERE recipe_id IN :ids ORDER BY recipe_id, id"
    ).bindparams(bindparam("ids", expanding=True))
    with engine.connect() as conn:
        for m in conn.execute(query, {"ids": recipe_ids}).mappings():
            out.setdefault(m["recipe_id"], []).append(
                {
                    "name": m["name"] or "",
                    "quantity": m["quantity"] or "",
                    "unit": m["unit"] or "",
                    "category": m["category"] or "other",
                    "is_to_taste": _b(m["is_to_taste"]),
                    "needs_review": _b(m["needs_review"]),
                }
            )
    return out


def compute_all(engine, source_type: str, limit: int | None) -> list[RecipeNutritionSummary]:
    recipes = load_recipes(engine, source_type, limit)
    ingredients = load_ingredients(engine, [r["id"] for r in recipes])
    summaries: list[RecipeNutritionSummary] = []
    for r in recipes:
        summaries.append(
            calculate_recipe_nutrition(
                recipe_id=r["id"],
                title=r["title"] or "",
                servings=r["servings"],
                meal_type=r["meal_type"] or "",
                category=r["category"] or "",
                ingredients=ingredients.get(r["id"], []),
            )
        )
    return summaries


def _content_values(s: RecipeNutritionSummary) -> dict:
    total = s.total or {}
    ps = s.per_serving or {}
    return {
        "nutrition_kcal_total": total.get("kcal"),
        "nutrition_protein_total": total.get("protein"),
        "nutrition_fat_total": total.get("fat"),
        "nutrition_carbs_total": total.get("carbs"),
        "nutrition_kcal_per_serving": ps.get("kcal"),
        "nutrition_protein_per_serving": ps.get("protein"),
        "nutrition_fat_per_serving": ps.get("fat"),
        "nutrition_carbs_per_serving": ps.get("carbs"),
        "nutrition_servings": s.servings,
        "nutrition_serving_size_text": s.serving_size_text,
        "nutrition_confidence": s.confidence,
        "nutrition_source": s.source,
        "nutrition_needs_review": bool(s.needs_review),
        "nutrition_review_reason": s.review_reason,
    }


def _norm_num(v):
    return None if v is None else round(float(v), 1)


def _content_equal(current: dict, proposed: dict, current_coverage, proposed_coverage) -> bool:
    for col in _CONTENT_COLUMNS:
        cv, pv = current.get(col), proposed.get(col)
        if col == "nutrition_needs_review":
            if _b(cv) != bool(pv):
                return False
        elif col in {"nutrition_serving_size_text", "nutrition_confidence",
                     "nutrition_source", "nutrition_review_reason"}:
            if (cv or None) != (pv or None):
                return False
        else:
            if _norm_num(cv) != _norm_num(pv):
                return False
    return current_coverage == proposed_coverage


def load_current(engine, recipe_ids: list[int]) -> dict[int, dict]:
    if not recipe_ids:
        return {}
    cols = ", ".join(_CONTENT_COLUMNS)
    query = text(
        f"SELECT id, {cols}, nutrition_coverage_json FROM recipes WHERE id IN :ids"
    ).bindparams(bindparam("ids", expanding=True))
    out: dict[int, dict] = {}
    with engine.connect() as conn:
        for m in conn.execute(query, {"ids": recipe_ids}).mappings():
            row = dict(m)
            cov = row.get("nutrition_coverage_json")
            if isinstance(cov, str):
                try:
                    cov = json.loads(cov)
                except (ValueError, TypeError):
                    cov = None
            row["_coverage"] = cov
            out[row["id"]] = row
    return out


def apply_commit(engine, summaries: list[RecipeNutritionSummary]) -> int:
    is_pg = engine.dialect.name == "postgresql"
    current = load_current(engine, [s.recipe_id for s in summaries])
    cov_expr = "CAST(:coverage AS jsonb)" if is_pg else ":coverage"
    set_cols = ", ".join(f"{c} = :{c}" for c in _CONTENT_COLUMNS)
    update = text(
        f"UPDATE recipes SET {set_cols}, nutrition_coverage_json = {cov_expr}, "
        "nutrition_calculated_at = :calculated_at WHERE id = :id"
    )
    now = datetime.now(timezone.utc)
    changed = 0
    with engine.begin() as conn:
        for s in summaries:
            proposed = _content_values(s)
            cur = current.get(s.recipe_id, {})
            if cur and _content_equal(cur, proposed, cur.get("_coverage"), s.coverage):
                continue
            params = dict(proposed)
            params["coverage"] = json.dumps(s.coverage, ensure_ascii=False)
            params["calculated_at"] = now
            params["id"] = s.recipe_id
            conn.execute(update, params)
            changed += 1
    return changed


# --------------------------- suspicious checks ---------------------------

def suspicious_flags(s: RecipeNutritionSummary, meal_type: str, category: str) -> list[str]:
    flags: list[str] = []
    ps = s.per_serving or {}
    total = s.total or {}
    kcal_ps = ps.get("kcal")
    is_main = (meal_type or "").lower() in MAIN_DISH_MEALS or (category or "").lower() in MAIN_DISH_CATEGORIES
    if kcal_ps is not None and kcal_ps > 1500:
        flags.append("kcal_per_serving>1500")
    if kcal_ps is not None and kcal_ps < 50 and is_main:
        flags.append("kcal_per_serving<50_for_main")
    if kcal_ps and kcal_ps > 0 and not any(ps.get(k) for k in ("protein", "fat", "carbs")):
        flags.append("macros_missing_with_kcal")
    if total.get("kcal") is not None and total["kcal"] > 8000:
        flags.append("total_kcal_extreme")
    if s.servings is None:
        flags.append("servings_missing")
    if s.confidence == "unavailable":
        flags.append("unavailable_core")
    return flags


# --------------------------- reporting ---------------------------

def _meta_lookup(engine, source_type: str) -> dict[int, dict]:
    with engine.connect() as conn:
        return {
            m["id"]: {"meal_type": m["meal_type"], "category": m["category"]}
            for m in conn.execute(
                text("SELECT id, meal_type, category FROM recipes WHERE source_type = :st"),
                {"st": source_type},
            ).mappings()
        }


def build_summary(summaries: list[RecipeNutritionSummary]) -> dict:
    conf = Counter(s.confidence for s in summaries)
    with_ps = sum(1 for s in summaries if s.per_serving)
    return {
        "total_recipes": len(summaries),
        "calculated_recipes": sum(1 for s in summaries if s.confidence != "unavailable"),
        "exact_recipes": conf.get("exact", 0),
        "estimated_recipes": conf.get("estimated", 0),
        "low_confidence_recipes": conf.get("low_confidence", 0),
        "unavailable_recipes": conf.get("unavailable", 0),
        "recipes_with_per_serving": with_ps,
        "recipes_without_per_serving": len(summaries) - with_ps,
        "recipes_needs_review": sum(1 for s in summaries if s.needs_review),
    }


def _example_row(s: RecipeNutritionSummary) -> str:
    ps = s.per_serving or {}
    total = s.total or {}
    cov = s.coverage
    coverage = f"{cov.get('used_ingredients', 0)}/{cov.get('total_ingredients', 0)}"
    return (
        f"| {s.recipe_id} | {s.title} | {total.get('kcal', '—')} | {ps.get('kcal', '—')} | "
        f"{ps.get('protein', '—')} | {ps.get('fat', '—')} | {ps.get('carbs', '—')} | "
        f"{s.confidence} | {coverage} | {s.review_reason or '—'} |"
    )


def _example_table(title: str, rows: list[RecipeNutritionSummary]) -> list[str]:
    lines = [f"### {title}", ""]
    if not rows:
        lines += ["_нет_", ""]
        return lines
    lines.append("| id | рецепт | ккал всего | ккал/порц | Б | Ж | У | confidence | покрытие | review |")
    lines.append("|----|--------|------------|-----------|---|---|---|------------|----------|--------|")
    lines += [_example_row(s) for s in rows]
    lines.append("")
    return lines


def render_md(summaries, summary, suspicious, *, committed, started_at, applied) -> str:
    lines: list[str] = []
    a = lines.append
    a("# PLANAM V1 — Recipe nutrition summary")
    a("")
    a(f"**Режим:** {'COMMIT SAFE-ONLY' if committed else 'DRY-RUN'}")
    a(f"**Запуск:** {started_at}")
    a(f"**DB changed:** {'yes' if committed else 'no'}")
    a(f"**Источник:** {NUTRITION_SOURCE}")
    a("")
    a("## Summary")
    a("")
    a("| метрика | значение |")
    a("|---------|----------|")
    for key, label in [
        ("total_recipes", "всего рецептов"),
        ("calculated_recipes", "рассчитано"),
        ("exact_recipes", "exact"),
        ("estimated_recipes", "estimated"),
        ("low_confidence_recipes", "low_confidence"),
        ("unavailable_recipes", "unavailable"),
        ("recipes_with_per_serving", "с per_serving"),
        ("recipes_without_per_serving", "без per_serving"),
        ("recipes_needs_review", "needs_review"),
    ]:
        a(f"| {label} | {summary[key]} |")
    a("")
    if committed:
        a(f"- строк обновлено: **{applied}**")
    else:
        a("- DRY-RUN: БД не изменена.")
    a("")
    a("## Top examples")
    a("")
    by_conf = {c: [s for s in summaries if s.confidence == c] for c in
               ("exact", "estimated", "low_confidence", "unavailable")}
    best = sorted(by_conf["exact"] + by_conf["estimated"],
                  key=lambda s: (s.coverage.get("coverage_pct", 0)), reverse=True)[:20]
    lines += _example_table("Top 20 best confidence", best)
    lines += _example_table("Top 20 low confidence", by_conf["low_confidence"][:20])
    lines += _example_table("Top 20 unavailable", by_conf["unavailable"][:20])
    high_kcal = sorted(
        [s for s in summaries if (s.per_serving or {}).get("kcal")],
        key=lambda s: s.per_serving["kcal"], reverse=True,
    )[:20]
    lines += _example_table("Top 20 high kcal (per serving)", high_kcal)
    susp_rows = [s for s, _ in suspicious][:20]
    lines += _example_table("Top 20 suspicious", susp_rows)
    a("## Suspicious details")
    a("")
    if suspicious:
        a("| id | рецепт | флаги |")
        a("|----|--------|-------|")
        for s, flags in suspicious[:40]:
            a(f"| {s.recipe_id} | {s.title} | {', '.join(flags)} |")
    else:
        a("_нет подозрительных значений_")
    a("")
    if not committed:
        a("> Применение: `--commit --safe-only` (после backup БД).")
    a("")
    return "\n".join(lines)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_json(summaries, summary, suspicious, *, committed, started_at, applied) -> str:
    return json.dumps(
        {
            "mode": "commit_safe_only" if committed else "dry_run",
            "db_changed": committed,
            "started_at": started_at,
            "source": NUTRITION_SOURCE,
            "summary": summary,
            "rows_changed": applied,
            "recipes": [s.to_dict() for s in summaries],
            "suspicious": [
                {"recipe_id": s.recipe_id, "title": s.title, "flags": flags}
                for s, flags in suspicious
            ],
        },
        ensure_ascii=False,
        indent=2,
    ) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Recipe nutrition summary (dry-run/commit)")
    parser.add_argument(
        "--database-url", default=os.environ.get("DATABASE_URL") or DEFAULT_DATABASE_URL
    )
    parser.add_argument("--source-type", default="v1_import")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--safe-only", action="store_true")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="(default) no DB writes")
    mode.add_argument("--commit", action="store_true", help="write nutrition_* columns")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    committed = bool(args.commit)
    started_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    if committed and not args.safe_only:
        print("WARNING: --commit without --safe-only; proceeding as SAFE-ONLY.")

    engine = create_engine(args.database_url)
    summaries = compute_all(engine, args.source_type, args.limit)
    meta = _meta_lookup(engine, args.source_type)
    suspicious = []
    for s in summaries:
        m = meta.get(s.recipe_id, {})
        flags = suspicious_flags(s, m.get("meal_type", ""), m.get("category", ""))
        if flags:
            suspicious.append((s, flags))

    summary = build_summary(summaries)
    applied = 0
    if committed:
        applied = apply_commit(engine, summaries)
        print(f"COMMIT SAFE-ONLY applied: {applied} recipes updated.")
    else:
        print(f"DRY-RUN: no DB writes. {len(summaries)} recipes computed.")

    md_path = COMMIT_MD if committed else DRY_MD
    json_path = COMMIT_JSON if committed else DRY_JSON
    _write(md_path, render_md(summaries, summary, suspicious,
                              committed=committed, started_at=started_at, applied=applied))
    _write(json_path, build_json(summaries, summary, suspicious,
                                 committed=committed, started_at=started_at, applied=applied))
    print(
        f"recipes={summary['total_recipes']} exact={summary['exact_recipes']} "
        f"estimated={summary['estimated_recipes']} low={summary['low_confidence_recipes']} "
        f"unavailable={summary['unavailable_recipes']}"
    )
    print(f"MD:   {md_path}")
    print(f"JSON: {json_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
