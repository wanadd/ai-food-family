#!/usr/bin/env python3
"""Populate the ingredient quality model (to_taste / nutrition / shopping / photo).

Safe, additive, idempotent. Default is **--dry-run** (no writes). Apply with:

    python backend/scripts/migrate_to_taste_ingredients.py --commit --safe-only

For every ACTIVE source_type=v1_import ingredient row it computes (and on commit
stores) the nullable quality fields:

  quantity_mode, quantity_text, is_to_taste, nutrition_precision,
  shopping_priority, photo_visibility, needs_review, needs_review_reason,
  manual_review_status.

It NEVER changes name / quantity / unit / category, never touches
recipes.ingredients JSONB, and never auto-fixes needs_review rows. Raw text is
preserved: `quantity = "по вкусу"` stays; `quantity_text` keeps a copy and
`quantity_mode = "to_taste"` marks it. `manual_review_status` is only seeded to
"pending" when empty (human decisions are preserved on re-run).

Reports:
  dry-run -> reports/to_taste_ingredients_migration_dry_run.md / .json
  commit  -> reports/to_taste_ingredients_migration_commit.md / .json
  always  -> reports/ingredient_normalization_needs_review.md / .json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, inspect, text

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from canonical_products import (  # noqa: E402
    classify_quantity_mode,
    get_needs_review_reason,
    get_nutrition_precision,
    get_photo_visibility,
    get_shopping_priority,
    resolve_product,
)

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATABASE_URL = "postgresql://aifood:aifood@localhost:5432/aifood"
REPORTS = ROOT / "reports"
DRY_MD = REPORTS / "to_taste_ingredients_migration_dry_run.md"
DRY_JSON = REPORTS / "to_taste_ingredients_migration_dry_run.json"
COMMIT_MD = REPORTS / "to_taste_ingredients_migration_commit.md"
COMMIT_JSON = REPORTS / "to_taste_ingredients_migration_commit.json"
NEEDS_REVIEW_MD = REPORTS / "ingredient_normalization_needs_review.md"
NEEDS_REVIEW_JSON = REPORTS / "ingredient_normalization_needs_review.json"

QUALITY_COLUMNS: list[tuple[str, str, str]] = [
    ("quantity_mode", "VARCHAR(16)", "VARCHAR(16)"),
    ("quantity_text", "VARCHAR(64)", "VARCHAR(64)"),
    ("is_to_taste", "BOOLEAN NOT NULL DEFAULT FALSE", "BOOLEAN NOT NULL DEFAULT 0"),
    ("nutrition_precision", "VARCHAR(24)", "VARCHAR(24)"),
    ("shopping_priority", "VARCHAR(16)", "VARCHAR(16)"),
    ("needs_review", "BOOLEAN NOT NULL DEFAULT FALSE", "BOOLEAN NOT NULL DEFAULT 0"),
    ("needs_review_reason", "VARCHAR(64)", "VARCHAR(64)"),
    ("photo_visibility", "VARCHAR(16)", "VARCHAR(16)"),
    ("manual_review_status", "VARCHAR(16)", "VARCHAR(16)"),
]
_QUALITY_FIELDS = [c[0] for c in QUALITY_COLUMNS]


def ensure_quality_columns(engine) -> list[str]:
    """Idempotently add the quality columns. Returns the columns added now."""
    is_pg = engine.dialect.name == "postgresql"
    existing = {c["name"] for c in inspect(engine).get_columns("recipe_ingredients")}
    added: list[str] = []
    with engine.begin() as conn:
        for name, pg_ddl, sqlite_ddl in QUALITY_COLUMNS:
            if is_pg:
                conn.execute(
                    text(f"ALTER TABLE recipe_ingredients ADD COLUMN IF NOT EXISTS {name} {pg_ddl}")
                )
                added.append(name)
            elif name not in existing:
                conn.execute(text(f"ALTER TABLE recipe_ingredients ADD COLUMN {name} {sqlite_ddl}"))
                added.append(name)
    return added


@dataclass
class Proposal:
    row_id: int
    recipe_id: int
    title: str
    name: str
    quantity: str
    unit: str
    category: str
    notes: str | None
    old: dict[str, Any]
    new: dict[str, Any]

    @property
    def changed_fields(self) -> list[str]:
        return [f for f in _QUALITY_FIELDS if self.old.get(f) != self.new.get(f)]

    @property
    def any_change(self) -> bool:
        return bool(self.changed_fields)


def _norm_bool(value: Any) -> bool:
    return bool(value) if value is not None else False


def compute_new(row: dict[str, Any]) -> dict[str, Any]:
    name = row["name"] or ""
    quantity = row["quantity"] or ""
    unit = row["unit"] or ""
    category = row["category"] or "other"
    notes = row.get("notes")

    product = resolve_product(name)
    generic = product.generic
    mode, is_to_taste = classify_quantity_mode(quantity)

    reason = get_needs_review_reason(
        name, quantity, unit, category=category, generic=generic, is_to_taste=is_to_taste
    )
    needs_review = reason is not None

    # Preserve any human-set manual_review_status; seed "pending" only when empty.
    existing_status = row.get("manual_review_status")
    if existing_status:
        manual_status = existing_status
    else:
        manual_status = "pending" if needs_review else None

    return {
        "quantity_mode": mode,
        "quantity_text": quantity if is_to_taste else None,
        "is_to_taste": is_to_taste,
        "nutrition_precision": get_nutrition_precision(
            name, quantity, unit, category=category, generic=generic, is_to_taste=is_to_taste
        ),
        "shopping_priority": get_shopping_priority(
            name, category, generic=generic, is_to_taste=is_to_taste, notes=notes
        ),
        "needs_review": needs_review,
        "needs_review_reason": reason,
        "photo_visibility": get_photo_visibility(
            name, category, is_to_taste=is_to_taste, generic=generic
        ),
        "manual_review_status": manual_status,
    }


def build_proposals(engine, source_type: str) -> list[Proposal]:
    query = text(
        """
        SELECT ri.id, ri.recipe_id, r.title, ri.name, ri.quantity, ri.unit,
               ri.category, ri.notes, ri.quantity_mode, ri.quantity_text,
               ri.is_to_taste, ri.nutrition_precision, ri.shopping_priority,
               ri.needs_review, ri.needs_review_reason, ri.photo_visibility,
               ri.manual_review_status
        FROM recipe_ingredients ri
        JOIN recipes r ON r.id = ri.recipe_id
        WHERE r.is_active = TRUE AND r.source_type = :source_type
        ORDER BY ri.recipe_id, ri.id
        """
    )
    proposals: list[Proposal] = []
    with engine.connect() as conn:
        for m in conn.execute(query, {"source_type": source_type}).mappings():
            row = dict(m)
            old = {
                "quantity_mode": row.get("quantity_mode"),
                "quantity_text": row.get("quantity_text"),
                "is_to_taste": _norm_bool(row.get("is_to_taste")),
                "nutrition_precision": row.get("nutrition_precision"),
                "shopping_priority": row.get("shopping_priority"),
                "needs_review": _norm_bool(row.get("needs_review")),
                "needs_review_reason": row.get("needs_review_reason"),
                "photo_visibility": row.get("photo_visibility"),
                "manual_review_status": row.get("manual_review_status"),
            }
            proposals.append(
                Proposal(
                    row_id=row["id"],
                    recipe_id=row["recipe_id"],
                    title=row.get("title") or "",
                    name=row["name"] or "",
                    quantity=row["quantity"] or "",
                    unit=row["unit"] or "",
                    category=row["category"] or "other",
                    notes=row.get("notes"),
                    old=old,
                    new=compute_new(row),
                )
            )
    return proposals


def apply_commit(engine, proposals: list[Proposal]) -> int:
    update = text(
        """
        UPDATE recipe_ingredients SET
            quantity_mode = :quantity_mode,
            quantity_text = :quantity_text,
            is_to_taste = :is_to_taste,
            nutrition_precision = :nutrition_precision,
            shopping_priority = :shopping_priority,
            needs_review = :needs_review,
            needs_review_reason = :needs_review_reason,
            photo_visibility = :photo_visibility,
            manual_review_status = :manual_review_status
        WHERE id = :row_id
        """
    )
    changed = 0
    with engine.begin() as conn:
        for p in proposals:
            if not p.any_change:
                continue
            params = dict(p.new)
            params["row_id"] = p.row_id
            conn.execute(update, params)
            changed += 1
    return changed


# --------------------------- summaries ---------------------------

SUGGESTED_ACTION = {
    "generic": "keep_as_generic",
    "ambiguous": "specify_product",
    "unknown_unit": "manual_fix_required",
    "bad_quantity": "manual_fix_required",
    "low_nutrition_precision": "exclude_from_nutrition",
}


def summarize(proposals: list[Proposal]) -> dict[str, Any]:
    to_taste = [p for p in proposals if p.new["is_to_taste"]]
    q = Counter(p.quantity.strip().lower() for p in to_taste)
    return {
        "rows": len(proposals),
        "candidates_to_taste": len(to_taste),
        "quantity_po_vkusu": q.get("по вкусу", 0),
        "quantity_nemnogo": q.get("немного", 0),
        "quantity_shchepotka": q.get("щепотка", 0) + q.get("щепотку", 0),
        "unit_sht_to_taste": sum(1 for p in to_taste if (p.unit or "").strip().lower() == "шт"),
        "is_to_taste": len(to_taste),
        "nutrition_low_confidence": sum(
            1 for p in proposals if p.new["nutrition_precision"] == "low_confidence"
        ),
        "shopping_low": sum(1 for p in proposals if p.new["shopping_priority"] == "low"),
        "photo_hidden": sum(1 for p in proposals if p.new["photo_visibility"] == "hidden"),
        "needs_review": sum(1 for p in proposals if p.new["needs_review"]),
        "rows_to_change": sum(1 for p in proposals if p.any_change),
    }


def render_migration_md(summary: dict, proposals: list[Proposal], *, committed: bool, started_at: str) -> str:
    lines: list[str] = []
    a = lines.append
    a("# PLANAM V1 — to_taste / ingredient quality migration")
    a("")
    a(f"**Режим:** {'COMMIT SAFE-ONLY' if committed else 'DRY-RUN'}")
    a(f"**Запуск:** {started_at}")
    a(f"**DB changed:** {'yes' if committed else 'no'}")
    a("")
    a("## Сводка")
    a("")
    a("| Метрика | Значение |")
    a("|---------|----------|")
    a(f"| Строк обработано | {summary['rows']} |")
    a(f"| Кандидатов to_taste | {summary['candidates_to_taste']} |")
    a(f"| quantity = \"по вкусу\" | {summary['quantity_po_vkusu']} |")
    a(f"| quantity = \"немного\" | {summary['quantity_nemnogo']} |")
    a(f"| quantity = \"щепотка\" | {summary['quantity_shchepotka']} |")
    a(f"| unit = \"шт\" при to_taste | {summary['unit_sht_to_taste']} |")
    a(f"| is_to_taste = true | {summary['is_to_taste']} |")
    a(f"| nutrition_precision = low_confidence | {summary['nutrition_low_confidence']} |")
    a(f"| shopping_priority = low | {summary['shopping_low']} |")
    a(f"| photo_visibility = hidden | {summary['photo_hidden']} |")
    a(f"| needs_review = true | {summary['needs_review']} |")
    a(f"| строк {'изменено' if committed else 'будет изменено'} | {summary['rows_to_change']} |")
    a("")
    a("## Примеры before / after (to_taste)")
    a("")
    examples = [p for p in proposals if p.new["is_to_taste"]][:30]
    if examples:
        a("| recipe_id | название | quantity (сохр.) | quantity_mode | nutrition | shopping | photo |")
        a("|-----------|----------|------------------|---------------|-----------|----------|-------|")
        for p in examples:
            a(
                f"| {p.recipe_id} | {p.name} | `{p.quantity}` | {p.new['quantity_mode']} | "
                f"{p.new['nutrition_precision']} | {p.new['shopping_priority']} | {p.new['photo_visibility']} |"
            )
    else:
        a("_Нет._")
    a("")
    if not committed:
        a("> DRY-RUN: БД не изменена. Применение: `--commit --safe-only` (после backup).")
    a("")
    return "\n".join(lines)


def render_needs_review_md(proposals: list[Proposal]) -> str:
    rows = [p for p in proposals if p.new["needs_review"]]
    lines: list[str] = []
    a = lines.append
    a("# PLANAM V1 — Ingredient needs review")
    a("")
    a(f"Строк, требующих ручного решения: **{len(rows)}**. Авто-fix не выполняется.")
    a("")
    a("| recipe_id | title | ing_id | name | qty | unit | cat | mode | to_taste | nutrition | shopping | photo | reason | suggested_action |")
    a("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for p in rows:
        reason = p.new["needs_review_reason"] or "-"
        action = SUGGESTED_ACTION.get(reason, "manual_fix_required")
        a(
            f"| {p.recipe_id} | {p.title} | {p.row_id} | {p.name} | `{p.quantity}` | `{p.unit}` | "
            f"{p.category} | {p.new['quantity_mode']} | {p.new['is_to_taste']} | "
            f"{p.new['nutrition_precision']} | {p.new['shopping_priority']} | "
            f"{p.new['photo_visibility']} | {reason} | {action} |"
        )
    a("")
    return "\n".join(lines)


def needs_review_json(proposals: list[Proposal]) -> dict:
    rows = [p for p in proposals if p.new["needs_review"]]
    return {
        "count": len(rows),
        "rows": [
            {
                "recipe_id": p.recipe_id,
                "recipe_title": p.title,
                "ingredient_id": p.row_id,
                "name": p.name,
                "quantity": p.quantity,
                "unit": p.unit,
                "category": p.category,
                "quantity_mode": p.new["quantity_mode"],
                "is_to_taste": p.new["is_to_taste"],
                "nutrition_precision": p.new["nutrition_precision"],
                "shopping_priority": p.new["shopping_priority"],
                "photo_visibility": p.new["photo_visibility"],
                "needs_review_reason": p.new["needs_review_reason"],
                "suggested_action": SUGGESTED_ACTION.get(
                    p.new["needs_review_reason"] or "", "manual_fix_required"
                ),
            }
            for p in rows
        ],
    }


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Migrate to_taste / ingredient quality")
    parser.add_argument(
        "--database-url", default=os.environ.get("DATABASE_URL") or DEFAULT_DATABASE_URL
    )
    parser.add_argument("--source-type", default="v1_import")
    parser.add_argument("--safe-only", action="store_true")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="(default) no DB writes")
    mode.add_argument("--commit", action="store_true", help="apply quality fields")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    committed = bool(args.commit)
    started_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    if committed and not args.safe_only:
        print("WARNING: --commit without --safe-only; proceeding as SAFE-ONLY.")

    engine = create_engine(args.database_url)
    # Columns must exist before we can SELECT/UPDATE them (idempotent).
    ensure_quality_columns(engine)

    proposals = build_proposals(engine, args.source_type)
    summary = summarize(proposals)

    if committed:
        changed = apply_commit(engine, proposals)
        summary["rows_to_change"] = changed
        print(f"COMMIT SAFE-ONLY applied: {changed} rows updated.")
    else:
        print(f"DRY-RUN: no DB writes. {summary['rows_to_change']} rows would change.")

    md_path = COMMIT_MD if committed else DRY_MD
    json_path = COMMIT_JSON if committed else DRY_JSON
    _write(md_path, render_migration_md(summary, proposals, committed=committed, started_at=started_at))
    _write(
        json_path,
        json.dumps(
            {
                "mode": "commit_safe_only" if committed else "dry_run",
                "db_changed": committed,
                "started_at": started_at,
                "source_type": args.source_type,
                "summary": summary,
                "changes": [
                    {
                        "row_id": p.row_id,
                        "recipe_id": p.recipe_id,
                        "name": p.name,
                        "quantity": p.quantity,
                        "changed_fields": p.changed_fields,
                        "new": p.new,
                    }
                    for p in proposals
                    if p.any_change
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    _write(NEEDS_REVIEW_MD, render_needs_review_md(proposals))
    _write(NEEDS_REVIEW_JSON, json.dumps(needs_review_json(proposals), ensure_ascii=False, indent=2) + "\n")

    print(
        f"rows={summary['rows']} to_taste={summary['is_to_taste']} "
        f"low_confidence={summary['nutrition_low_confidence']} "
        f"photo_hidden={summary['photo_hidden']} needs_review={summary['needs_review']}"
    )
    print(f"MD:   {md_path}")
    print(f"JSON: {json_path}")
    print(f"NEEDS_REVIEW: {NEEDS_REVIEW_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
