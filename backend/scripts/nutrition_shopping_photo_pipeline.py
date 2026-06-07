#!/usr/bin/env python3
"""Pipeline: nutrition + shopping grouping + photo readiness (dry-run / safe-only).

Loads ingredient rows once, runs the three read-only reports, and computes the
SAFE-ONLY DB updates:

  * nutrition_precision — refined using the nutrition facts dictionary
    (exact / estimated / low_confidence / unavailable);
  * shopping_priority   — recomputed deterministically (stable / idempotent).

Default is **--dry-run** (no writes). Apply with:

    python backend/scripts/nutrition_shopping_photo_pipeline.py --commit --safe-only

NEVER changes name / quantity / unit / category, never touches JSONB / images /
recipe nutrition columns, and is idempotent (re-run changes 0 rows). KБЖУ values
and groupings live in the reports, not in the DB (no schema churn).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import create_engine, text

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from calculate_nutrition import (  # noqa: E402
    aggregate_by_recipe,
    load_rows,
    nutrition_for,
    summarize as nutrition_summary,
    write_reports as write_nutrition_reports,
)
from canonical_products import get_shopping_priority  # noqa: E402
from evaluate_photo_prompt_readiness import evaluate as evaluate_photo
from evaluate_photo_prompt_readiness import write_reports as write_photo_reports
from generate_shopping_list_groups import build_summary as shopping_summary
from generate_shopping_list_groups import write_reports as write_shopping_reports

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATABASE_URL = "postgresql://aifood:aifood@localhost:5432/aifood"
REPORTS = ROOT / "reports"
DRY_MD = REPORTS / "nutrition_shopping_photo_pipeline_dry_run.md"
DRY_JSON = REPORTS / "nutrition_shopping_photo_pipeline_dry_run.json"
COMMIT_MD = REPORTS / "nutrition_shopping_photo_pipeline_commit.md"
COMMIT_JSON = REPORTS / "nutrition_shopping_photo_pipeline_commit.json"


def proposed_updates(rows) -> list[dict]:
    """Per-row proposed (nutrition_precision, shopping_priority) and current values."""
    updates: list[dict] = []
    for row in rows:
        new_precision = nutrition_for(row).precision
        new_priority = get_shopping_priority(
            row.name,
            row.category,
            generic=row.generic,
            is_to_taste=row.is_to_taste,
            notes=row.notes,
        )
        changed = (
            new_precision != row.nutrition_precision
            or new_priority != row.shopping_priority
        )
        updates.append(
            {
                "id": row.id,
                "recipe_id": row.recipe_id,
                "name": row.name,
                "old_precision": row.nutrition_precision,
                "new_precision": new_precision,
                "old_priority": row.shopping_priority,
                "new_priority": new_priority,
                "changed": changed,
            }
        )
    return updates


def apply_commit(engine, updates: list[dict]) -> int:
    stmt = text(
        """
        UPDATE recipe_ingredients
        SET nutrition_precision = :precision, shopping_priority = :priority
        WHERE id = :id
        """
    )
    changed = 0
    with engine.begin() as conn:
        for u in updates:
            if not u["changed"]:
                continue
            conn.execute(
                stmt,
                {"precision": u["new_precision"], "priority": u["new_priority"], "id": u["id"]},
            )
            changed += 1
    return changed


def render_md(*, committed, started_at, nutr, shop, photo, updates, applied) -> str:
    changed = sum(1 for u in updates if u["changed"])
    lines: list[str] = []
    a = lines.append
    a("# PLANAM V1 — Nutrition / Shopping / Photo pipeline")
    a("")
    a(f"**Режим:** {'COMMIT SAFE-ONLY' if committed else 'DRY-RUN'}")
    a(f"**Запуск:** {started_at}")
    a(f"**DB changed:** {'yes' if committed else 'no'}")
    a("")
    a("## Safe-only DB updates (recipe_ingredients)")
    a("")
    a("| поле | что обновляется |")
    a("|------|-----------------|")
    a("| nutrition_precision | exact/estimated/low_confidence/unavailable (по фактам КБЖУ) |")
    a("| shopping_priority | normal/low/optional/hidden (детерминированно) |")
    a("")
    a(f"- строк {'изменено' if committed else 'будет изменено'}: **{applied if committed else changed}**")
    a("")
    a("## Nutrition")
    a("")
    pc = nutr["precision_counts"]
    for key in ("exact", "estimated", "low_confidence", "unavailable"):
        a(f"- {key}: **{pc.get(key, 0)}**")
    a(f"- рецептов можно считать: **{nutr['recipes_estimable']}** / {nutr['recipes']}")
    a("")
    a("## Shopping list")
    a("")
    a(f"- обязательных: **{shop['mandatory']}** · необязательных: **{shop['non_mandatory']}** · "
      f"скрытых: **{shop['hidden']}** · to_taste: **{shop['to_taste']}**")
    a("")
    a("## Photo prompt")
    a("")
    v = photo["visibility_counts"]
    a(f"- visible: **{v['visible']}** · optional: **{v['optional']}** · "
      f"hidden: **{v['hidden']}** · unsafe: **{v['unsafe']}**")
    a(f"- рецептов готовы: **{photo['recipes_ready']}** / {photo['recipes']}")
    a("")
    if not committed:
        a("> DRY-RUN: БД не изменена. Применение: `--commit --safe-only` (после backup).")
        a("> Полные отчёты: nutrition_estimate.*, shopping_list_groups.*, photo_prompt_readiness.*")
    a("")
    return "\n".join(lines)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Nutrition/shopping/photo pipeline")
    parser.add_argument(
        "--database-url", default=os.environ.get("DATABASE_URL") or DEFAULT_DATABASE_URL
    )
    parser.add_argument("--source-type", default="v1_import")
    parser.add_argument("--safe-only", action="store_true")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="(default) no DB writes")
    mode.add_argument("--commit", action="store_true", help="apply safe-only updates")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    committed = bool(args.commit)
    started_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    if committed and not args.safe_only:
        print("WARNING: --commit without --safe-only; proceeding as SAFE-ONLY.")

    engine = create_engine(args.database_url)
    rows = load_rows(engine, args.source_type)

    # Read-only sub-reports (always written).
    recipes = aggregate_by_recipe(rows)
    write_nutrition_reports(rows, recipes, started_at)
    write_shopping_reports(rows, started_at)
    write_photo_reports(rows, started_at)

    nutr = nutrition_summary(rows, recipes)
    shop = shopping_summary(rows)
    photo = evaluate_photo(rows)

    updates = proposed_updates(rows)
    applied = 0
    if committed:
        applied = apply_commit(engine, updates)
        print(f"COMMIT SAFE-ONLY applied: {applied} rows updated.")
    else:
        changed = sum(1 for u in updates if u["changed"])
        print(f"DRY-RUN: no DB writes. {changed} rows would change.")

    md_path = COMMIT_MD if committed else DRY_MD
    json_path = COMMIT_JSON if committed else DRY_JSON
    _write(
        md_path,
        render_md(
            committed=committed, started_at=started_at, nutr=nutr, shop=shop,
            photo=photo, updates=updates, applied=applied,
        ),
    )
    _write(
        json_path,
        json.dumps(
            {
                "mode": "commit_safe_only" if committed else "dry_run",
                "db_changed": committed,
                "started_at": started_at,
                "rows": len(rows),
                "rows_changed": applied if committed else sum(1 for u in updates if u["changed"]),
                "nutrition": nutr,
                "shopping": shop,
                "photo": {k: v for k, v in photo.items() if k != "recipe_list"},
                "changes": [u for u in updates if u["changed"]],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    print(f"MD:   {md_path}")
    print(f"JSON: {json_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
