#!/usr/bin/env python3
"""Stage Q4: set display_title for catalog-ready seed batch 256-265."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from _image_paths import ensure_app_on_path  # noqa: E402

ensure_app_on_path()

DISPLAY_TITLES: dict[int, str] = {
    256: "Куриные котлеты с овощами",
    257: "Перловка с овощами",
    258: "Суп с курицей и морковью",
    259: "Курица с яблоками",
    260: "Куриная запеканка с овощами",
    261: "Сливочный суп с овощами",
    262: "Овощной суп с тофу",
    263: "Салат с кальмарами",
    264: "Салат с курицей и яблоком",
    265: "Овощной суп с фасолью",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Set display_title for seed batch 256-265")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--commit", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    os.environ.setdefault("DATABASE_URL", os.environ.get("DATABASE_URL", ""))
    if not os.environ.get("DATABASE_URL"):
        print("ERROR: DATABASE_URL required", file=sys.stderr)
        return 1

    from app.database import SessionLocal
    from app.models.recipe import Recipe

    session = SessionLocal()
    updated = 0
    skipped = 0
    try:
        for rid, display_title in DISPLAY_TITLES.items():
            recipe = session.get(Recipe, rid)
            if recipe is None:
                print(f"SKIP #{rid}: not found")
                skipped += 1
                continue
            if recipe.display_title == display_title:
                print(f"UNCHANGED #{rid}: {display_title!r}")
                skipped += 1
                continue
            print(f"UPDATE #{rid}: {recipe.display_title!r} -> {display_title!r}")
            if args.commit:
                recipe.display_title = display_title
            updated += 1
        if args.commit and updated:
            session.commit()
    finally:
        session.close()

    print(f"summary updated={updated} skipped={skipped} mode={'commit' if args.commit else 'dry-run'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
