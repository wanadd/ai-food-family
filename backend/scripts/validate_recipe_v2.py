#!/usr/bin/env python3
"""Validate Recipe V2 JSON/JSONL files (no DB writes)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
API_ROOT = ROOT / "apps" / "api"
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.recipes.recipe_v2_validation import validate_recipe_v2  # noqa: E402


def load_recipes(path: Path) -> list[dict]:
    if path.suffix == ".jsonl":
        rows: list[dict] = []
        with path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    rows.append(json.loads(line))
        return rows
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and "recipes" in data:
        return list(data["recipes"])
    raise ValueError("Expected JSON array or JSONL")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Recipe V2 documents")
    parser.add_argument("--file", type=Path, required=True)
    parser.add_argument("--report", type=Path, default=None)
    args = parser.parse_args()

    recipes = load_recipes(args.file)
    results = []
    invalid = 0
    for idx, raw in enumerate(recipes):
        out = validate_recipe_v2(raw)
        out["index"] = idx
        out["title"] = raw.get("title")
        results.append(out)
        if not out["valid"]:
            invalid += 1
            print(f"[INVALID] {raw.get('title')}: {out['errors']}", file=sys.stderr)
        elif out["warnings"]:
            print(f"[WARN] {raw.get('title')}: {out['warnings']}")

    summary = {
        "file": str(args.file),
        "total": len(recipes),
        "valid": len(recipes) - invalid,
        "invalid": invalid,
        "results": results,
    }
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Validated {len(recipes)} recipes: {len(recipes) - invalid} valid, {invalid} invalid")
    return 1 if invalid else 0


if __name__ == "__main__":
    raise SystemExit(main())
