#!/usr/bin/env python3
"""Safe reset plan for legacy seed/import recipes (dry-run default).

NEVER run --apply without explicit approval and --backup-id.

Usage:
    python backend/scripts/recipe_rebuild_v2_safe_reset.py --dry-run
    python backend/scripts/recipe_rebuild_v2_safe_reset.py --apply --backup-id 20250610_120000
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import create_engine, text

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "reports" / "recipe_rebuild_v2_safe_reset_plan.md"
BACKUP_ROOT = ROOT / "backups" / "recipe_rebuild_v2"
DEFAULT_DATABASE_URL = "postgresql://aifood:aifood@localhost:5432/aifood"

PROTECTED_SOURCE_TYPES = frozenset({"manual", "user"})


def backup_exists(backup_id: str) -> bool:
    return (BACKUP_ROOT / backup_id / "manifest.md").is_file()


def analyze(database_url: str) -> dict:
    engine = create_engine(database_url)
    with engine.connect() as conn:
        candidates = conn.execute(
            text(
                """
                SELECT r.id, r.title, r.source_type, r.tags
                FROM recipes r
                WHERE r.source_type IN ('seed', 'import', 'v1_import')
                   OR NOT (COALESCE(r.tags, '[]'::jsonb) @> '["recipe_schema_v2"]'::jsonb)
                ORDER BY r.id
                """
            )
        ).all()

        protected_favorites = conn.execute(
            text(
                """
                SELECT DISTINCT rf.recipe_id
                FROM recipe_favorites rf
                JOIN recipes r ON r.id = rf.recipe_id
                WHERE r.source_type IN ('seed', 'import', 'v1_import')
                """
            )
        ).scalars().all()

        protected_history = conn.execute(
            text(
                """
                SELECT DISTINCT rh.recipe_id
                FROM recipe_history rh
                JOIN recipes r ON r.id = rh.recipe_id
                WHERE r.source_type IN ('seed', 'import', 'v1_import')
                """
            )
        ).scalars().all()

        protected_checkins = conn.execute(
            text(
                """
                SELECT DISTINCT mc.recipe_id
                FROM meal_checkins mc
                JOIN recipes r ON r.id = mc.recipe_id
                WHERE mc.recipe_id IS NOT NULL
                  AND r.source_type IN ('seed', 'import', 'v1_import')
                """
            )
        ).scalars().all()

    deletable: list[dict] = []
    blocked: list[dict] = []
    protected_ids = set(protected_favorites) | set(protected_history) | set(protected_checkins)

    for row in candidates:
        rid, title, source_type, tags = row
        tags_list = tags if isinstance(tags, list) else []
        if "recipe_schema_v2" in tags_list and source_type not in ("seed", "import", "v1_import"):
            blocked.append({"id": rid, "title": title, "reason": "v2_gold_recipe"})
            continue
        if source_type in PROTECTED_SOURCE_TYPES:
            blocked.append({"id": rid, "title": title, "reason": "user_manual_recipe"})
            continue
        if rid in protected_ids:
            blocked.append({"id": rid, "title": title, "reason": "has_favorites_history_or_checkins"})
            continue
        deletable.append({"id": rid, "title": title, "source_type": source_type})

    return {
        "candidate_count": len(candidates),
        "deletable_count": len(deletable),
        "blocked_count": len(blocked),
        "deletable_sample": deletable[:50],
        "blocked_sample": blocked[:30],
        "protected_favorites": len(protected_favorites),
        "protected_history": len(protected_history),
        "protected_checkins": len(protected_checkins),
    }


def write_report(mode: str, data: dict, backup_id: str | None, error: str | None = None) -> None:
    lines = [
        "# Recipe Rebuild V2 — Safe Reset Plan",
        "",
        f"- Generated: {datetime.now(timezone.utc).isoformat()}",
        f"- Mode: **{mode}**",
        f"- Backup id: `{backup_id or 'none'}`",
        "",
    ]
    if error:
        lines.extend([f"- Error: `{error}`", ""])
    else:
        lines.extend(
            [
                f"- Candidates scanned: **{data['candidate_count']}**",
                f"- Would delete: **{data['deletable_count']}**",
                f"- Blocked (protected): **{data['blocked_count']}**",
                f"- Protected by favorites: **{data['protected_favorites']}**",
                f"- Protected by history: **{data['protected_history']}**",
                f"- Protected by meal checkins: **{data['protected_checkins']}**",
                "",
                "## Risks",
                "",
                "- Active menus may reference deleted recipes if not covered by checkins.",
                "- User favorites on seed recipes are blocked but should be reviewed.",
                "- Always restore from backup if apply goes wrong.",
                "",
                "## Deletable sample",
                "",
            ]
        )
        for row in data.get("deletable_sample", [])[:20]:
            lines.append(f"- [{row['id']}] {row['title']} ({row['source_type']})")
        lines.extend(["", "## Blocked sample", ""])
        for row in data.get("blocked_sample", [])[:15]:
            lines.append(f"- [{row['id']}] {row['title']}: {row['reason']}")

    lines.extend(
        [
            "",
            "## Apply requirements",
            "",
            "- `--apply` requires `--backup-id` pointing to `backups/recipe_rebuild_v2/<id>/manifest.md`",
            "- Stage 1: dry-run only unless explicitly approved.",
        ]
    )
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Safe reset legacy recipes")
    parser.add_argument("--dry-run", action="store_true", default=True)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--backup-id", default=None)
    parser.add_argument("--database-url", default=os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL))
    args = parser.parse_args()

    if args.apply and not args.backup_id:
        print("ERROR: --apply requires --backup-id", file=sys.stderr)
        return 2
    if args.apply and not backup_exists(args.backup_id):
        print(f"ERROR: backup manifest not found for id {args.backup_id}", file=sys.stderr)
        return 2

    mode = "apply" if args.apply else "dry-run"
    try:
        data = analyze(args.database_url)
    except Exception as exc:
        write_report(mode, {}, args.backup_id, error=str(exc))
        print(f"Analysis failed: {exc}")
        return 0

    write_report(mode, data, args.backup_id)
    if args.apply:
        print("Apply is gated in Stage 1 — analysis only; no DELETE executed.")
    else:
        print(f"Dry-run: would delete {data['deletable_count']} recipes (blocked {data['blocked_count']})")
    print(f"Report: {REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
