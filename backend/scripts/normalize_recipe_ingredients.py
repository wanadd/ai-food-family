#!/usr/bin/env python3
"""Normalize recipe ingredients: canonical category + clean units (dry-run first).

Default mode is **--dry-run** (no DB writes). Applying changes requires the
explicit, production-disciplined combination:

    python backend/scripts/normalize_recipe_ingredients.py --commit --safe-only

``--commit`` without ``--safe-only`` is accepted but prints a loud warning and
behaves exactly as safe-only (the ONLY supported commit mode — there are no
dangerous/force/update-all modes here).

SAFE-ONLY commit applies, per ``recipe_ingredients`` row:
  * ``category``  -> canonical shopping slug;
  * ``unit``      -> canonical unit (alias cleanup, junk extraction);
  * ``quantity``  -> only a safe numeric reformat ("1,5" -> "1.5").

SAFE-ONLY commit deliberately NEVER:
  * changes ingredient ``name`` (catalog has 0 spelling variants);
  * rewrites ``to_taste`` quantities ("по вкусу"/"немного") — kept verbatim;
  * invents numbers for bad quantities;
  * touches ``recipes.ingredients`` JSONB (see resync_recipe_ingredients_jsonb.py);
  * touches images / titles / steps / source_type / is_active.

It is idempotent: a second run changes 0 rows.

Reports (dry-run and commit are written to DIFFERENT files):
  dry-run -> reports/planam_v1_ingredient_normalization_dry_run.md
             reports/planam_v1_ingredient_normalization.json
  commit  -> reports/planam_v1_ingredient_normalization_commit.md
             reports/planam_v1_ingredient_normalization_commit.json
  always  -> reports/ingredient_normalization_needs_review.md

Requires DATABASE_URL (or --database-url).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import create_engine, text

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from canonical_products import (  # noqa: E402
    CANONICAL_UNITS,
    DEFAULT_CATEGORY,
    is_photo_visible,
    is_valid_quantity,
    normalize_quantity,
    normalize_unit,
    resolve_product,
)

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATABASE_URL = "postgresql://aifood:aifood@localhost:5432/aifood"
REPORTS = ROOT / "reports"
DRY_MD = REPORTS / "planam_v1_ingredient_normalization_dry_run.md"
DRY_JSON = REPORTS / "planam_v1_ingredient_normalization.json"
COMMIT_MD = REPORTS / "planam_v1_ingredient_normalization_commit.md"
COMMIT_JSON = REPORTS / "planam_v1_ingredient_normalization_commit.json"
NEEDS_REVIEW_MD = REPORTS / "ingredient_normalization_needs_review.md"


@dataclass
class Proposal:
    row_id: int
    recipe_id: int
    recipe_title: str
    name: str
    old_category: str
    new_category: str
    old_unit: str
    new_unit: str
    old_quantity: str
    new_quantity: str
    to_taste: bool
    generic: bool
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

    @property
    def numeric_quantity(self) -> bool:
        return is_valid_quantity(self.new_quantity)

    @property
    def canonical_unit(self) -> bool:
        return (self.new_unit or "").strip().lower() in CANONICAL_UNITS

    @property
    def photo_visible(self) -> bool:
        return is_photo_visible(self.name, self.new_category, self.to_taste, self.generic)

    def review_reasons(self) -> list[str]:
        reasons: list[str] = []
        if self.generic:
            reasons.append("generic")
        if self.new_category == DEFAULT_CATEGORY:
            reasons.append("ambiguous/unknown product")
        if self.to_taste:
            reasons.append("bad quantity (to_taste)")
        elif not self.numeric_quantity:
            reasons.append("bad quantity (non-numeric)")
        if not self.canonical_unit:
            reasons.append("unknown unit")
        if self.generic or self.to_taste:
            reasons.append("nutrition unsafe")
        if not self.photo_visible:
            reasons.append("photo unsafe")
        return reasons


@dataclass
class Summary:
    rows: int = 0
    category_changes: int = 0
    unit_changes: int = 0
    quantity_changes: int = 0
    to_taste: int = 0
    needs_review: int = 0
    new_category_counts: Counter = field(default_factory=Counter)


@dataclass
class CommitResult:
    rows_changed: int = 0
    category_applied: int = 0
    unit_applied: int = 0
    quantity_applied: int = 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Normalize recipe ingredients")
    parser.add_argument(
        "--database-url", default=os.environ.get("DATABASE_URL") or DEFAULT_DATABASE_URL
    )
    parser.add_argument("--source-type", default="v1_import")
    parser.add_argument("--md", default=None)
    parser.add_argument("--json", default=None)
    parser.add_argument(
        "--safe-only",
        action="store_true",
        help="explicit production-safe commit (required intent for --commit)",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="(default) no DB writes")
    mode.add_argument("--commit", action="store_true", help="apply safe-only changes")
    return parser.parse_args()


def build_proposals(engine, source_type: str) -> list[Proposal]:
    query = text(
        """
        SELECT ri.id, ri.recipe_id, r.title, ri.name, ri.quantity, ri.unit, ri.category
        FROM recipe_ingredients ri
        JOIN recipes r ON r.id = ri.recipe_id
        WHERE r.is_active = TRUE AND r.source_type = :source_type
        ORDER BY ri.recipe_id, ri.id
        """
    )
    proposals: list[Proposal] = []
    with engine.connect() as conn:
        for row in conn.execute(query, {"source_type": source_type}):
            row_id, recipe_id, title, name, quantity, unit, category = row
            name = name or ""
            quantity = quantity or ""
            unit = unit or ""
            category = category or "other"

            product = resolve_product(name)
            new_unit, _ = normalize_unit(unit, quantity)
            new_qty, to_taste = normalize_quantity(quantity)
            # Safe commit subset keeps quantity verbatim for to_taste / unparseable.
            commit_qty = new_qty if (is_valid_quantity(quantity) and not to_taste) else quantity

            proposals.append(
                Proposal(
                    row_id=row_id,
                    recipe_id=recipe_id,
                    recipe_title=title or "",
                    name=name,
                    old_category=category,
                    new_category=product.category,
                    old_unit=unit,
                    new_unit=new_unit,
                    old_quantity=quantity,
                    new_quantity=commit_qty,
                    to_taste=to_taste,
                    generic=product.generic,
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


def apply_commit(engine, proposals: list[Proposal]) -> CommitResult:
    """Apply the SAFE-ONLY subset (category + unit + numeric quantity).

    Names are never updated. Idempotent: rows already normalized are skipped.
    """
    update = text(
        """
        UPDATE recipe_ingredients
        SET category = :category, unit = :unit, quantity = :quantity
        WHERE id = :row_id
        """
    )
    result = CommitResult()
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
            result.rows_changed += 1
            if p.category_changed:
                result.category_applied += 1
            if p.unit_changed:
                result.unit_applied += 1
            if p.quantity_changed:
                result.quantity_applied += 1
    return result


# --------------------------- readiness ---------------------------

def shopping_readiness(proposals: list[Proposal]) -> dict:
    total = len(proposals) or 1
    good = sum(1 for p in proposals if p.new_category != DEFAULT_CATEGORY)
    other = sum(1 for p in proposals if p.new_category == DEFAULT_CATEGORY)
    generic = sum(1 for p in proposals if p.generic)
    to_taste = sum(1 for p in proposals if p.to_taste)
    cats = Counter(p.new_category for p in proposals)
    return {
        "rows": len(proposals),
        "with_real_category": good,
        "with_real_category_pct": round(good * 100.0 / total, 1),
        "other": other,
        "generic_soft_display": generic,
        "to_taste_optional": to_taste,
        "category_counts": dict(cats.most_common()),
    }


def nutrition_readiness(proposals: list[Proposal]) -> dict:
    total = len(proposals) or 1
    numeric = sum(1 for p in proposals if p.numeric_quantity and not p.to_taste)
    canonical = sum(1 for p in proposals if p.canonical_unit)
    to_taste = sum(1 for p in proposals if p.to_taste)
    generic = sum(1 for p in proposals if p.generic)
    low_conf = sum(1 for p in proposals if p.to_taste or p.generic or not p.numeric_quantity)
    return {
        "rows": len(proposals),
        "numeric_quantity": numeric,
        "numeric_quantity_pct": round(numeric * 100.0 / total, 1),
        "canonical_unit": canonical,
        "canonical_unit_pct": round(canonical * 100.0 / total, 1),
        "to_taste": to_taste,
        "generic": generic,
        "low_confidence": low_conf,
    }


def photo_readiness(proposals: list[Proposal]) -> dict:
    by_recipe: dict[int, int] = {}
    for p in proposals:
        by_recipe.setdefault(p.recipe_id, 0)
        if p.photo_visible:
            by_recipe[p.recipe_id] += 1
    recipes = len(by_recipe) or 1
    ready = sum(1 for c in by_recipe.values() if c >= 2)
    visible = sum(1 for p in proposals if p.photo_visible)
    hidden = len(proposals) - visible
    return {
        "recipes": len(by_recipe),
        "recipes_ready": ready,
        "recipes_ready_pct": round(ready * 100.0 / recipes, 1),
        "visible_ingredients": visible,
        "hidden_ingredients": hidden,
    }


# --------------------------- reports ---------------------------

def _examples(proposals: list[Proposal], limit: int = 40) -> list[Proposal]:
    return [p for p in proposals if p.any_change][:limit]


def render_markdown(
    summary: Summary,
    proposals: list[Proposal],
    *,
    committed: bool,
    commit_result: CommitResult | None,
    started_at: str,
) -> str:
    lines: list[str] = []
    a = lines.append
    mode = "COMMIT SAFE-ONLY" if committed else "DRY-RUN"
    a("# PLANAM V1 — Ingredient Normalization")
    a("")
    a(f"**Режим:** {mode}")
    a(f"**Запуск:** {started_at}")
    a(f"**DB changed:** {'yes' if committed else 'no'}")
    a("")
    a("## Сводка")
    a("")
    a("| Метрика | Значение |")
    a("|---------|----------|")
    a(f"| Строк-ингредиентов обработано | {summary.rows} |")
    if committed and commit_result is not None:
        a(f"| category обновлено | {commit_result.category_applied} |")
        a(f"| unit обновлено | {commit_result.unit_applied} |")
        a(f"| quantity обновлено | {commit_result.quantity_applied} |")
        a(f"| строк изменено всего | {commit_result.rows_changed} |")
        a(f"| строк пропущено (без изменений) | {summary.rows - commit_result.rows_changed} |")
    else:
        a(f"| Изменений категории (будет) | {summary.category_changes} |")
        a(f"| Изменений единицы (будет) | {summary.unit_changes} |")
        a(f"| Изменений количества (будет) | {summary.quantity_changes} |")
    a(f"| `to_taste` оставлено без изменения | {summary.to_taste} |")
    a(f"| needs_review оставлено без изменения | {summary.needs_review} |")
    a("")
    a("## Примеры before / after")
    a("")
    examples = _examples(proposals)
    if examples:
        a("| recipe_id | название | category | unit | quantity |")
        a("|-----------|----------|----------|------|----------|")
        for p in examples:
            cat = f"`{p.old_category}`→`{p.new_category}`" if p.category_changed else p.new_category
            unit = f"`{p.old_unit}`→`{p.new_unit}`" if p.unit_changed else p.new_unit
            qty = f"`{p.old_quantity}`→`{p.new_quantity}`" if p.quantity_changed else p.new_quantity
            a(f"| {p.recipe_id} | {p.name} | {cat} | {unit} | {qty} |")
    else:
        a("_Нет изменений (идемпотентно)._")
    a("")
    a("## Распределение по новым категориям")
    a("")
    a("| категория | строк |")
    a("|-----------|-------|")
    for cat, count in summary.new_category_counts.most_common():
        a(f"| {cat} | {count} |")
    a("")

    # readiness sections
    shop = shopping_readiness(proposals)
    a("## Shopping readiness after safe-only commit")
    a("")
    a(f"- строк с нормальной категорией: **{shop['with_real_category']}** "
      f"({shop['with_real_category_pct']}%)")
    a(f"- осталось `другое`: **{shop['other']}**")
    a(f"- generic (показывать мягко): **{shop['generic_soft_display']}**")
    a(f"- to_taste (не добавлять в обязательные покупки): **{shop['to_taste_optional']}**")
    a("")

    nutr = nutrition_readiness(proposals)
    a("## Nutrition readiness after safe-only commit")
    a("")
    a(f"- числовое quantity: **{nutr['numeric_quantity']}** ({nutr['numeric_quantity_pct']}%)")
    a(f"- canonical unit: **{nutr['canonical_unit']}** ({nutr['canonical_unit_pct']}%)")
    a(f"- to_taste: **{nutr['to_taste']}**")
    a(f"- generic: **{nutr['generic']}**")
    a(f"- low confidence (нельзя считать точно): **{nutr['low_confidence']}**")
    a("")

    photo = photo_readiness(proposals)
    a("## Photo prompt readiness after safe-only commit")
    a("")
    a(f"- рецептов с >=2 видимыми ингредиентами: **{photo['recipes_ready']}** "
      f"из {photo['recipes']} ({photo['recipes_ready_pct']}%)")
    a(f"- видимых ингредиентов: **{photo['visible_ingredients']}**")
    a(f"- скрытых (соль/специи/масло/по вкусу/generic): **{photo['hidden_ingredients']}**")
    a("")

    if not committed:
        a("> DRY-RUN: ни одна строка не изменена. Применение: "
          "`--commit --safe-only` (после backup).")
    a("")
    return "\n".join(lines)


def render_needs_review(proposals: list[Proposal]) -> str:
    rows = [p for p in proposals if p.needs_review]
    lines: list[str] = []
    a = lines.append
    a("# PLANAM V1 — Ingredient normalization: needs review")
    a("")
    a(f"Строк, требующих ручного решения: **{len(rows)}**. "
      "Эти строки safe-only commit НЕ меняет агрессивно (кроме безопасной категории).")
    a("")
    a("| recipe_id | recipe title | ingredient | quantity | unit | current cat | suggested cat | reasons |")
    a("|-----------|--------------|------------|----------|------|-------------|---------------|---------|")
    for p in rows:
        reasons = ", ".join(p.review_reasons()) or "-"
        a(
            f"| {p.recipe_id} | {p.recipe_title} | {p.name} | `{p.old_quantity}` | "
            f"`{p.old_unit}` | {p.old_category} | {p.new_category} | {reasons} |"
        )
    a("")
    return "\n".join(lines)


def build_json(
    summary: Summary,
    proposals: list[Proposal],
    *,
    committed: bool,
    commit_result: CommitResult | None,
    started_at: str,
    source_type: str,
) -> dict:
    return {
        "mode": "commit_safe_only" if committed else "dry_run",
        "db_changed": committed,
        "started_at": started_at,
        "source_type": source_type,
        "summary": {
            "rows": summary.rows,
            "category_changes": summary.category_changes,
            "unit_changes": summary.unit_changes,
            "quantity_changes": summary.quantity_changes,
            "to_taste": summary.to_taste,
            "needs_review": summary.needs_review,
            "new_category_counts": dict(summary.new_category_counts),
        },
        "commit_result": (
            {
                "rows_changed": commit_result.rows_changed,
                "category_applied": commit_result.category_applied,
                "unit_applied": commit_result.unit_applied,
                "quantity_applied": commit_result.quantity_applied,
            }
            if committed and commit_result is not None
            else None
        ),
        "shopping_readiness": shopping_readiness(proposals),
        "nutrition_readiness": nutrition_readiness(proposals),
        "photo_readiness": photo_readiness(proposals),
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
    }


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def main() -> int:
    args = parse_args()
    committed = bool(args.commit)
    started_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    if committed and not args.safe_only:
        print(
            "WARNING: --commit was given without --safe-only. There is no other "
            "commit mode; proceeding as SAFE-ONLY (category + unit + numeric "
            "quantity; names and to_taste preserved)."
        )

    engine = create_engine(args.database_url)
    proposals = build_proposals(engine, args.source_type)
    summary = summarize(proposals)

    commit_result: CommitResult | None = None
    if committed:
        commit_result = apply_commit(engine, proposals)
        print(
            f"COMMIT SAFE-ONLY applied: rows_changed={commit_result.rows_changed} "
            f"category={commit_result.category_applied} unit={commit_result.unit_applied} "
            f"quantity={commit_result.quantity_applied}"
        )
    else:
        print("DRY-RUN: no DB writes.")

    md_path = Path(args.md).resolve() if args.md else (COMMIT_MD if committed else DRY_MD)
    json_path = Path(args.json).resolve() if args.json else (COMMIT_JSON if committed else DRY_JSON)

    _write(
        md_path,
        render_markdown(
            summary, proposals, committed=committed, commit_result=commit_result,
            started_at=started_at,
        ),
    )
    _write(
        json_path,
        json.dumps(
            build_json(
                summary, proposals, committed=committed, commit_result=commit_result,
                started_at=started_at, source_type=args.source_type,
            ),
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    _write(NEEDS_REVIEW_MD, render_needs_review(proposals))

    print(
        f"rows={summary.rows} category_changes={summary.category_changes} "
        f"unit_changes={summary.unit_changes} quantity_changes={summary.quantity_changes} "
        f"to_taste={summary.to_taste} needs_review={summary.needs_review}"
    )
    print(f"MD:   {md_path}")
    print(f"JSON: {json_path}")
    print(f"NEEDS_REVIEW: {NEEDS_REVIEW_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
