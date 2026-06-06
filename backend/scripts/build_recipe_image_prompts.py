#!/usr/bin/env python3
"""Build PlanAm V1 recipe image prompts from catalog or hero list.

Run from the repository root:
    python backend/scripts/build_recipe_image_prompts.py --pilot 10
    python backend/scripts/build_recipe_image_prompts.py --titles-file reports/planam_v1_hero_top50.json --limit 10
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend" / "scripts"))

from recipe_image_utils import build_pilot_row  # noqa: E402

DEFAULT_CATALOG = ROOT / "data" / "planam_v1_recipes.json"
DEFAULT_HERO = ROOT / "reports" / "planam_v1_hero_top50.json"
DEFAULT_OUTPUT = ROOT / "data" / "planam_v1_image_pilot_batch.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build recipe image pilot prompts")
    parser.add_argument(
        "--catalog",
        default=str(DEFAULT_CATALOG),
        help="V1 catalog JSON path",
    )
    parser.add_argument(
        "--titles-file",
        default=str(DEFAULT_HERO),
        help="JSON list with title field for ordering",
    )
    parser.add_argument(
        "--pilot",
        type=int,
        default=10,
        help="Number of pilot recipes",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT),
        help="Output pilot batch JSON",
    )
    return parser.parse_args()


def load_catalog(path: Path) -> dict[str, dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise SystemExit("Catalog must be a JSON array")
    by_title: dict[str, dict] = {}
    for item in data:
        if isinstance(item, dict) and item.get("title"):
            by_title[str(item["title"]).strip()] = item
    return by_title


def load_title_order(path: Path, limit: int) -> list[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise SystemExit("Titles file must be a JSON array")
    titles: list[str] = []
    for item in data:
        if isinstance(item, dict) and item.get("title"):
            titles.append(str(item["title"]).strip())
        if len(titles) >= limit:
            break
    return titles


def main() -> int:
    args = parse_args()
    catalog_path = Path(args.catalog).resolve()
    titles_path = Path(args.titles_file).resolve()
    output_path = Path(args.output).resolve()

    if not catalog_path.exists():
        raise SystemExit(f"Catalog not found: {catalog_path}")
    if not titles_path.exists():
        raise SystemExit(f"Titles file not found: {titles_path}")

    by_title = load_catalog(catalog_path)
    order = load_title_order(titles_path, args.pilot)
    batch: list[dict] = []
    missing: list[str] = []

    for index, title in enumerate(order, start=1):
        recipe = by_title.get(title)
        if recipe is None:
            missing.append(title)
            continue
        batch.append(build_pilot_row(recipe, recipe_id=index))

    if missing:
        print(f"Warning: {len(missing)} titles not found in catalog", file=sys.stderr)
        for title in missing:
            print(f"  - {title}", file=sys.stderr)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(batch, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {len(batch)} pilot prompts to {output_path}")
    return 0 if batch else 1


if __name__ == "__main__":
    raise SystemExit(main())
