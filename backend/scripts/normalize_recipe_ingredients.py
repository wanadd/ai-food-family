#!/usr/bin/env python3
"""Normalize recipe ingredients: canonical category + clean units (dry-run first).

Default mode is **--dry-run** (no DB writes): it proposes, per ingredient row,
a canonical shopping category and a normalized unit, and flags `to_taste`
quantities and rows needing manual review. `--commit` applies the SAFE subset
(category + unit + numeric quantity reformat) in one idempotent transaction.

Deliberately NOT changed automatically (surfaced for a human decision instead):
  * ingredient names (catalog has 0 spelling variants — renaming is unnecessary);
  * `to_taste` quantities ("по вкусу"/"немного") — need a dedicated flag/column;
  * unmapped names -> category "другое" with needs_review=true.

Run from repo root (or inside the api container):
    python backend/scripts/normalize_recipe_ingredients.py --dry-run
    python backend/scripts/normalize_recipe_ingredients.py --commit

Requires DATABASE_URL (or --database-url).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, text

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from canonical_products import (  # noqa: E402
    DEFAULT_CATEGORY,
    is_valid_quantity,
    normalize_quantity,
    normalize_unit,
    resolve_product,
)

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATABASE_URL = "postgresql://aifood:aifood@localhost:5432/aifood"
DEFAULT_MD = ROOT / "reports" / "planam_v1_ingredient_normalization_dry_run.md"
DEFAULT_JSON = ROOT / "reports" / "planam_v1_ingredient_normalization.json"


@dataclass
class Proposal:
    row_id: int
    recipe_id: int
    name: str
    old_category: str
    new_category: str
    old_unit: str
    new_unit: str
    old_quantity: str
    new_quantity: str
    to_taste: bool
    needs_review: bool

    @property
    def category_changed(self) -> bool:
        return self.new_category != self.old_category

    @property
    def unit_changed(self) -> bool:
        return self.new_unit != self.old_unit

    @property
    def quantity_changed(self) -> bool:
        return self.new_quantity != self.old_quantity

    @property
    def any_change(self) -> bool:
        return self.category_changed or self.unit_changed or self.quantity_changed


@dataclass
class Summary:
    rows: int = 0
    category_changes: int = 0
    unit_changes: int = 0
    quantity_changes: int = 0
    to_taste: int = 0
    needs_review: int = 0
    new_category_counts: Counter = field(default_factory=Counter)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Normalize recipe ingredients")
    parser.add_argument(
        "--database-url", default=os.environ.get("DATABASE_URL") or DEFAULT_DATABASE_URL
    )
    parser.add_argument("--source-type", default="v1_import")
    parser.add_argument("--md", default=str(DEFAULT_MD))
    parser.add_argument("--json", default=str(DEFAULT_JSON))
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="(default) no DB writes")
    mode.add_argument("--commit", action="store_true", help="apply safe changes")
    return parser.parse_args()


def build_proposals(engine, source_type: str) -> list[Proposal]:
    query = text(
        """
        SELECT ri.id, ri.recipe_id, ri.name, ri.quantity, ri.unit, ri.category
        FROM recipe_ingredients ri
        JOIN recipes r ON r.id = ri.recipe_id
        WHERE r.is_active = TRUE AND r.source_type = :source_type
        ORDER BY ri.recipe_id, ri.id
        """
    )
    proposals: list[Proposal] = []
    with engine.connect() as conn:
        for row in conn.execute(query, {"source_type": source_type}):
            row_id, recipe_id, name, quantity, unit, category = row
            name = name or ""
            quantity = quantity or ""
            unit = unit or ""
            category = category or "other"

            product = resolve_product(name)
            new_unit, _ = normalize_unit(unit, quantity)
            new_qty, to_taste = normalize_quantity(quantity)
            # Safe commit subset keeps quantity for to_taste / unparseable values.
            commit_qty = new_qty if (is_valid_quantity(quantity) and not to_taste) else quantity

            proposals.append(
                Proposal(
                    row_id=row_id,
                    recipe_id=recipe_id,
                    name=name,
                    old_category=category,
                    new_category=product.category,
                    old_unit=unit,
                    new_unit=new_unit,
                    old_quantity=quantity,
                    new_quantity=commit_qty,
                    to_taste=to_taste,
                    needs_review=(product.category == DEFAULT_CATEGORY) or product.generic,
                )
            )
    return proposals


def summarize(proposals: list[Proposal]) -> Summary:
    s = Summary(rows=len(proposals))
    for p in proposals:
        if p.category_changed:
            s.category_changes += 1
        if p.unit_changed:
            s.unit_changes += 1
        if p.quantity_changed:
            s.quantity_changes += 1
        if p.to_taste:
            s.to_taste += 1
        if p.needs_review:
            s.needs_review += 1
        s.new_category_counts[p.new_category] += 1
    return s


def apply_commit(engine, proposals: list[Proposal]) -> int:
    update = text(
        """
        UPDATE recipe_ingredients
        SET category = :category, unit = :unit, quantity = :quantity
        WHERE id = :row_id
        """
    )
    changed = 0
    with engine.begin() as conn:
        for p in proposals:
            if not p.any_change:
                continue
            conn.execute(
                update,
                {
                    "row_id": p.row_id,
                    "category": p.new_category,
                    "unit": p.new_unit,
                    "quantity": p.new_quantity,
                },
            )
            changed += 1
    return changed


def render_markdown(summary: Summary, proposals: list[Proposal], *, committed: bool) -> str:
    lines: list[str] = []
    a = lines.append
    mode = "COMMIT (применено)" if committed else "DRY-RUN (изменения не записаны)"
    a("# PLANAM V1 — Ingredient Normalization")
    a("")
    a(f"**Режим:** {mode}")
    a("")
    a("## Сводка")
    a("")
    a("| Метрика | Значение |")
    a("|---------|----------|")
    a(f"| Строк-ингредиентов | {summary.rows} |")
    a(f"| Изменений категории | {summary.category_changes} |")
    a(f"| Изменений единицы | {summary.unit_changes} |")
    a(f"| Изменений количества | {summary.quantity_changes} |")
    a(f"| `to_taste` (по вкусу/немного) | {summary.to_taste} |")
    a(f"| Требуют ручного решения | {summary.needs_review} |")
    a("")
    a("## Распределение по новым категориям")
    a("")
    a("| категория | строк |")
    a("|-----------|-------|")
    for cat, count in summary.new_category_counts.most_common():
        a(f"| {cat} | {count} |")
    a("")
    a("## Предлагаемые изменения единиц (примеры)")
    a("")
    unit_changes = [p for p in proposals if p.unit_changed][:40]
    if unit_changes:
        a("| recipe_id | название | unit было → станет |")
        a("|-----------|----------|--------------------|")
        for p in unit_changes:
            a(f"| {p.recipe_id} | {p.name} | `{p.old_unit}` → `{p.new_unit}` |")
    else:
        a("_Нет._")
    a("")
    a("## `to_taste` количества (НЕ меняются автоматически)")
    a("")
    to_taste = [p for p in proposals if p.to_taste][:40]
    if to_taste:
        a("| recipe_id | название | quantity |")
        a("|-----------|----------|----------|")
        for p in to_taste:
            a(f"| {p.recipe_id} | {p.name} | `{p.old_quantity}` |")
    else:
        a("_Нет._")
    a("")
    a("## Требуют ручного решения (категория `другое` / generic)")
    a("")
    review = [p for p in proposals if p.needs_review][:60]
    if review:
        a("| recipe_id | название | предложенная категория |")
        a("|-----------|----------|------------------------|")
        for p in review:
            a(f"| {p.recipe_id} | {p.name} | {p.new_category} |")
    else:
        a("_Нет._")
    a("")
    if not committed:
        a("> DRY-RUN: ни одна строка не изменена. Для применения безопасного "
          "набора (категория + единица + числовое количество) запустите `--commit`.")
    a("")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    committed = bool(args.commit)
    engine = create_engine(args.database_url)

    proposals = build_proposals(engine, args.source_type)
    summary = summarize(proposals)

    if committed:
        changed = apply_commit(engine, proposals)
        print(f"COMMIT applied: {changed} rows changed.")
    else:
        print("DRY-RUN: no DB writes.")

    md_path = Path(args.md).resolve()
    json_path = Path(args.json).resolve()
    md_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(render_markdown(summary, proposals, committed=committed), encoding="utf-8")
    json_path.write_text(
        json.dumps(
            {
                "mode": "commit" if committed else "dry_run",
                "source_type": args.source_type,
                "summary": {
                    "rows": summary.rows,
                    "category_changes": summary.category_changes,
                    "unit_changes": summary.unit_changes,
                    "quantity_changes": summary.quantity_changes,
                    "to_taste": summary.to_taste,
                    "needs_review": summary.needs_review,
                    "new_category_counts": dict(summary.new_category_counts),
                },
                "proposals": [
                    {
                        "row_id": p.row_id,
                        "recipe_id": p.recipe_id,
                        "name": p.name,
                        "category": [p.old_category, p.new_category],
                        "unit": [p.old_unit, p.new_unit],
                        "quantity": [p.old_quantity, p.new_quantity],
                        "to_taste": p.to_taste,
                        "needs_review": p.needs_review,
                    }
                    for p in proposals
                    if p.any_change or p.to_taste or p.needs_review
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    print(
        f"rows={summary.rows} category_changes={summary.category_changes} "
        f"unit_changes={summary.unit_changes} quantity_changes={summary.quantity_changes} "
        f"to_taste={summary.to_taste} needs_review={summary.needs_review}"
    )
    print(f"MD:   {md_path}")
    print(f"JSON: {json_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
