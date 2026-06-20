#!/usr/bin/env python3
"""Resync recipes.ingredients JSONB from recipe_ingredients (dry-run first).

WHY: `recipe_ingredients` is the source of truth (the API reads it first via
`get_structured_ingredients`). `recipes.ingredients` JSONB is a legacy
denormalized COPY used only as a fallback for old clients. After a safe-only
normalization commit the JSONB `amount` strings can be stale; this script
rebuilds them WITHOUT changing the JSONB structure.

Structure is intentionally kept identical to the project's own
`sync_jsonb_from_rows` / `persist_recipe_structure`:

    [{"name": <name>, "amount": "<quantity> <unit>"}]

So no new technical fields are introduced and frontend/API compatibility is
preserved. Names are never changed. Amounts use the honest formatter
(``app.services.ingredient_format``): to_taste phrases like "по вкусу" never
get a unit, and an empty unit never becomes "шт".

Default mode is **--dry-run** (no writes). Apply with:

    python backend/scripts/resync_recipe_ingredients_jsonb.py --commit --safe-only

Only active `source_type=v1_import` recipes that HAVE ingredient rows are
touched. manual/import recipes and recipes without rows are skipped. Idempotent.

Reports:
  dry-run -> reports/recipe_ingredients_jsonb_resync_dry_run.md / .json
  commit  -> reports/recipe_ingredients_jsonb_resync_commit.md / .json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, text

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

ROOT = Path(__file__).resolve().parents[2]
API_ROOT = ROOT / "apps" / "api"
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.services.ingredient_format import format_ingredient_amount  # noqa: E402
DEFAULT_DATABASE_URL = "postgresql://aifood:aifood@localhost:5432/aifood"
REPORTS = ROOT / "reports"
DRY_MD = REPORTS / "recipe_ingredients_jsonb_resync_dry_run.md"
DRY_JSON = REPORTS / "recipe_ingredients_jsonb_resync_dry_run.json"
COMMIT_MD = REPORTS / "recipe_ingredients_jsonb_resync_commit.md"
COMMIT_JSON = REPORTS / "recipe_ingredients_jsonb_resync_commit.json"


@dataclass
class RecipeDiff:
    recipe_id: int
    title: str
    current: list[dict[str, Any]]
    proposed: list[dict[str, Any]]

    @property
    def changed(self) -> bool:
        return self.current != self.proposed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Resync recipes.ingredients JSONB")
    parser.add_argument(
        "--database-url", default=os.environ.get("DATABASE_URL") or DEFAULT_DATABASE_URL
    )
    parser.add_argument("--source-type", default="v1_import")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--md", default=None)
    parser.add_argument("--json", default=None)
    parser.add_argument("--safe-only", action="store_true")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="(default) no DB writes")
    mode.add_argument("--commit", action="store_true", help="apply JSONB resync")
    return parser.parse_args()


def _coerce_jsonb(value: Any) -> list[dict[str, Any]]:
    if value is None:
        return []
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except (ValueError, TypeError):
            return []
    return value if isinstance(value, list) else []


def build_amount(quantity: str, unit: str) -> str:
    # Honest formatter: to_taste phrases ("по вкусу") drop the unit, empty unit
    # never becomes "шт".
    return format_ingredient_amount(quantity, unit)


def build_diffs(engine, source_type: str, limit: int | None) -> list[RecipeDiff]:
    recipe_query = text(
        """
        SELECT r.id, r.title, r.ingredients
        FROM recipes r
        WHERE r.is_active = TRUE AND r.source_type = :source_type
        ORDER BY r.id
        """
    )
    rows_query = text(
        """
        SELECT recipe_id, name, quantity, unit
        FROM recipe_ingredients
        WHERE recipe_id = :recipe_id
        ORDER BY id
        """
    )
    diffs: list[RecipeDiff] = []
    with engine.connect() as conn:
        recipes = list(conn.execute(recipe_query, {"source_type": source_type}))
        for recipe_id, title, ingredients in recipes:
            rows = list(conn.execute(rows_query, {"recipe_id": recipe_id}))
            if not rows:
                # never overwrite JSONB for recipes without normalized rows
                continue
            proposed = [
                {"name": name or "", "amount": build_amount(quantity, unit)}
                for (_rid, name, quantity, unit) in rows
            ]
            current = _coerce_jsonb(ingredients)
            diffs.append(
                RecipeDiff(recipe_id=recipe_id, title=title or "", current=current, proposed=proposed)
            )
            if limit is not None and len(diffs) >= limit:
                break
    return diffs


def apply_commit(engine, diffs: list[RecipeDiff]) -> int:
    is_pg = engine.dialect.name == "postgresql"
    if is_pg:
        update = text("UPDATE recipes SET ingredients = CAST(:payload AS jsonb) WHERE id = :id")
    else:
        update = text("UPDATE recipes SET ingredients = :payload WHERE id = :id")
    changed = 0
    with engine.begin() as conn:
        for d in diffs:
            if not d.changed:
                continue
            payload = json.dumps(d.proposed, ensure_ascii=False)
            conn.execute(update, {"payload": payload, "id": d.recipe_id})
            changed += 1
    return changed


def render_markdown(diffs: list[RecipeDiff], *, committed: bool, started_at: str, changed: int) -> str:
    changed_diffs = [d for d in diffs if d.changed]
    lines: list[str] = []
    a = lines.append
    mode = "COMMIT SAFE-ONLY" if committed else "DRY-RUN"
    a("# PLANAM V1 — recipes.ingredients JSONB resync")
    a("")
    a(f"**Режим:** {mode}")
    a(f"**Запуск:** {started_at}")
    a(f"**DB changed:** {'yes' if committed else 'no'}")
    a("")
    a("## Сводка")
    a("")
    a("| Метрика | Значение |")
    a("|---------|----------|")
    a(f"| Рецептов с ingredient_rows | {len(diffs)} |")
    a(f"| Рецептов будет/обновлено | {changed if committed else len(changed_diffs)} |")
    a(f"| Рецептов без изменений | {len(diffs) - len(changed_diffs)} |")
    a("")
    a("## Структура JSONB (диагностика)")
    a("")
    a("Целевая структура (как в `sync_jsonb_from_rows`): `[{\"name\", \"amount\"}]`. "
      "Новые поля не добавляются; `name` не меняется.")
    a("")
    a("## Примеры current → proposed (до 5)")
    a("")
    for d in changed_diffs[:5]:
        a(f"### recipe_id={d.recipe_id} — {d.title}")
        a("")
        a("```json")
        a("current:  " + json.dumps(d.current[:4], ensure_ascii=False))
        a("proposed: " + json.dumps(d.proposed[:4], ensure_ascii=False))
        a("```")
        a("")
    if not changed_diffs:
        a("_Расхождений нет (идемпотентно)._")
        a("")
    if not committed:
        a("> DRY-RUN: записи в БД не было. Применение: `--commit --safe-only`.")
        a("")
    return "\n".join(lines)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def main() -> int:
    args = parse_args()
    committed = bool(args.commit)
    started_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    if committed and not args.safe_only:
        print(
            "WARNING: --commit without --safe-only. Proceeding as SAFE-ONLY "
            "(only active v1_import recipes with rows; structure unchanged)."
        )

    engine = create_engine(args.database_url)
    diffs = build_diffs(engine, args.source_type, args.limit)
    changed_diffs = [d for d in diffs if d.changed]

    applied = 0
    if committed:
        applied = apply_commit(engine, diffs)
        print(f"COMMIT SAFE-ONLY applied: {applied} recipes updated.")
    else:
        print(f"DRY-RUN: no DB writes. {len(changed_diffs)} recipes would change.")

    md_path = Path(args.md).resolve() if args.md else (COMMIT_MD if committed else DRY_MD)
    json_path = Path(args.json).resolve() if args.json else (COMMIT_JSON if committed else DRY_JSON)

    _write(md_path, render_markdown(diffs, committed=committed, started_at=started_at, changed=applied))
    _write(
        json_path,
        json.dumps(
            {
                "mode": "commit_safe_only" if committed else "dry_run",
                "db_changed": committed,
                "started_at": started_at,
                "source_type": args.source_type,
                "recipes_with_rows": len(diffs),
                "recipes_changed": applied if committed else len(changed_diffs),
                "changes": [
                    {
                        "recipe_id": d.recipe_id,
                        "title": d.title,
                        "current": d.current,
                        "proposed": d.proposed,
                    }
                    for d in changed_diffs
                ],
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
