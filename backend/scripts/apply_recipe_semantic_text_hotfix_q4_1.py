#!/usr/bin/env python3
"""Stage Q4.1: persist prod semantic text hotfix for recipes 256-263.

Dry-run by default; pass --commit to write title/display_title/description only.
"""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from _image_paths import ensure_app_on_path  # noqa: E402

ensure_app_on_path()

ALLOWED_RECIPE_IDS = frozenset(range(256, 264))
UPDATABLE_FIELDS = frozenset({"title", "display_title", "description"})

TEXT_HOTFIX: dict[int, dict[str, str]] = {
    256: {
        "title": "Нежные куриные котлеты с овощами",
        "display_title": "Куриные котлеты",
        "description": (
            "Запечённые куриные котлеты с морковью, луком и чесноком. "
            "Мягкое семейное блюдо для обеда или ужина без жарки на сковороде."
        ),
    },
    257: {
        "title": "Перловка с овощами и брокколи",
        "display_title": "Перловка с брокколи",
        "description": (
            "Сытная перловка с морковью, луком и брокколи. "
            "Подходит как самостоятельный гарнир или основа для простого семейного ужина."
        ),
    },
    258: {
        "title": "Куриный суп с овощами",
        "display_title": "Куриный суп",
        "description": (
            "Простой домашний суп с куриным филе, картофелем, морковью и зеленью. "
            "Лёгкий вариант для семейного обеда."
        ),
    },
    259: {
        "title": "Курица с овощами и яблоками",
        "display_title": "Курица с яблоками",
        "description": (
            "Горячее блюдо из куриной грудки, брокколи, сладкого перца и яблок. "
            "Получается мягким, ароматным и немного сладковатым."
        ),
    },
    260: {
        "title": "Курица с брокколи под сыром",
        "display_title": "Курица с брокколи",
        "description": (
            "Запечённое куриное филе с брокколи, цветной капустой, сливками и сыром. "
            "Сытное горячее блюдо для семейного ужина."
        ),
    },
    261: {
        "title": "Суп со свиным фаршем и овощами",
        "display_title": "Суп со свиным фаршем",
        "description": (
            "Сытный суп со свининой, картофелем, морковью, луком и зеленью. "
            "Мясо измельчается в фарш и варится вместе с овощами."
        ),
    },
    262: {
        "title": "Овощной суп-пюре с брокколи",
        "display_title": "Овощной суп-пюре",
        "description": (
            "Нежный суп-пюре из картофеля, моркови, брокколи и лука. "
            "Овощи варятся до мягкости и пробиваются блендером."
        ),
    },
    263: {
        "title": "Салат с креветками и свежим огурцом",
        "display_title": "Салат с креветками",
        "description": (
            "Лёгкий салат с креветками, огурцом, помидорами черри и лимонной заправкой. "
            "Подходит для обеда или лёгкого ужина."
        ),
    },
}


@dataclass
class HotfixResult:
    recipe_id: int
    changed: bool
    before: dict[str, str | None]
    after: dict[str, str]


def _snapshot(recipe: Any) -> dict[str, str | None]:
    return {
        "title": recipe.title,
        "display_title": recipe.display_title,
        "description": recipe.description,
    }


def apply_text_hotfix_to_recipe(recipe: Any, payload: dict[str, str], *, commit: bool) -> HotfixResult:
    """Update only title/display_title/description on a recipe row."""
    before = _snapshot(recipe)
    after = {field: payload[field] for field in UPDATABLE_FIELDS}
    changed = any(before.get(field) != after.get(field) for field in UPDATABLE_FIELDS)
    if commit and changed:
        recipe.title = after["title"]
        recipe.display_title = after["display_title"]
        recipe.description = after["description"]
    return HotfixResult(recipe_id=recipe.id, changed=changed, before=before, after=after)


def run_hotfix(session: Any, *, commit: bool) -> list[HotfixResult]:
    from app.models.recipe import Recipe

    results: list[HotfixResult] = []
    for recipe_id in sorted(TEXT_HOTFIX):
        if recipe_id not in ALLOWED_RECIPE_IDS:
            raise ValueError(f"recipe id {recipe_id} outside allowed range 256-263")
        recipe = session.get(Recipe, recipe_id)
        if recipe is None:
            continue
        results.append(apply_text_hotfix_to_recipe(recipe, TEXT_HOTFIX[recipe_id], commit=commit))
    if commit:
        session.commit()
    return results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Apply semantic text hotfix for recipes 256-263 (dry-run by default)",
    )
    parser.add_argument(
        "--commit",
        action="store_true",
        help="Persist title/display_title/description changes",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    os.environ.setdefault("DATABASE_URL", os.environ.get("DATABASE_URL", ""))
    if not os.environ.get("DATABASE_URL"):
        print("ERROR: DATABASE_URL required", file=sys.stderr)
        return 1

    from app.database import SessionLocal

    session = SessionLocal()
    try:
        results = run_hotfix(session, commit=args.commit)
    finally:
        session.close()

    updated = 0
    skipped = 0
    for row in results:
        if not row.changed:
            skipped += 1
            print(f"UNCHANGED #{row.recipe_id}")
            continue
        updated += 1
        print(f"UPDATE #{row.recipe_id}")
        for field in UPDATABLE_FIELDS:
            print(f"  {field}: {row.before.get(field)!r} -> {row.after[field]!r}")
        print(f"  title: {row.after['title']}")
        print(f"  display_title: {row.after['display_title']}")
        print(f"  description: {row.after['description']}")

    print(
        f"summary updated={updated} skipped={skipped} "
        f"mode={'commit' if args.commit else 'dry-run'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
