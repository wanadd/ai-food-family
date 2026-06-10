#!/usr/bin/env python3
"""Safe reset plan for legacy seed/import recipes (dry-run default).

NEVER run --apply without explicit approval and --backup-id.

Usage:
    python backend/scripts/recipe_rebuild_v2_safe_reset.py --dry-run
    python backend/scripts/recipe_rebuild_v2_safe_reset.py --apply --backup-id 20250610_120000
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from sqlalchemy import create_engine, text

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "reports" / "recipe_rebuild_v2_safe_reset_plan.md"
BACKUP_ROOT = ROOT / "backups" / "recipe_rebuild_v2"
DEFAULT_DATABASE_URL = "postgresql://aifood:aifood@localhost:5432/aifood"

PROTECTED_SOURCE_TYPES = frozenset({"manual", "user"})
GOLD_PROTECTION_TAGS = frozenset({"gold_v2", "recipe_schema_v2", "status:gold"})


def normalize_tags(tags: Any) -> list[str]:
    if not tags:
        return []
    if isinstance(tags, list):
        return [str(t) for t in tags]
    return []


def is_gold_protected(tags: Any) -> bool:
    """True if recipe carries any V2 gold protection tag."""
    return bool(GOLD_PROTECTION_TAGS.intersection(normalize_tags(tags)))


def classify_reset_candidate(
    recipe_id: int,
    title: str,
    source_type: str | None,
    tags: Any,
    protected_ids: set[int],
) -> tuple[Literal["deletable", "blocked"], dict[str, Any]]:
    """Classify a recipe for safe reset. Gold/status tags always block deletion."""
    st = source_type or ""

    if is_gold_protected(tags):
        return "blocked", {"id": recipe_id, "title": title, "reason": "gold_recipe_v2"}

    if st in PROTECTED_SOURCE_TYPES:
        return "blocked", {"id": recipe_id, "title": title, "reason": "user_manual_recipe"}

    if recipe_id in protected_ids:
        return "blocked", {
            "id": recipe_id,
            "title": title,
            "reason": "has_favorites_history_or_checkins",
        }

    return "deletable", {"id": recipe_id, "title": title, "source_type": st}


def analyze_candidates(
    candidates: list[tuple[int, str, str | None, Any]],
    protected_ids: set[int],
) -> dict[str, Any]:
    deletable: list[dict] = []
    blocked: list[dict] = []
    protected_gold = 0

    for rid, title, source_type, tags in candidates:
        kind, info = classify_reset_candidate(rid, title, source_type, tags, protected_ids)
        if kind == "blocked":
            blocked.append(info)
            if info.get("reason") == "gold_recipe_v2":
                protected_gold += 1
        else:
            deletable.append(info)

    return {
        "candidate_count": len(candidates),
        "deletable_count": len(deletable),
        "blocked_count": len(blocked),
        "protected_gold_status": protected_gold,
        "deletable_sample": deletable[:50],
        "blocked_sample": blocked[:30],
        "deletable_ids": [row["id"] for row in deletable],
    }


def backup_exists(backup_id: str) -> bool:
    return (BACKUP_ROOT / backup_id / "manifest.md").is_file()


def analyze(database_url: str) -> dict[str, Any]:
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

    protected_ids = set(protected_favorites) | set(protected_history) | set(protected_checkins)
    result = analyze_candidates(list(candidates), protected_ids)
    result.update(
        {
            "protected_favorites": len(protected_favorites),
            "protected_history": len(protected_history),
            "protected_checkins": len(protected_checkins),
        }
    )
    return result


def apply_deletions(database_url: str, deletable_ids: list[int]) -> int:
    """Delete only recipes classified as deletable (gold-protected never included)."""
    if not deletable_ids:
        return 0
    engine = create_engine(database_url)
    with engine.begin() as conn:
        result = conn.execute(
            text("DELETE FROM recipes WHERE id = ANY(:ids)"),
            {"ids": deletable_ids},
        )
        return result.rowcount or 0


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
                f"- Protected by gold/status: **{data.get('protected_gold_status', 0)}**",
                f"- Protected by favorites: **{data['protected_favorites']}**",
                f"- Protected by history: **{data['protected_history']}**",
                f"- Protected by meal checkins: **{data['protected_checkins']}**",
                "",
                "## Risks",
                "",
                "- Active menus may reference deleted recipes if not covered by checkins.",
                "- User favorites on seed recipes are blocked but should be reviewed.",
                "- Gold V2 recipes (tags gold_v2 / recipe_schema_v2 / status:gold) are never deleted.",
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
            "- Gold V2 recipes are excluded from deletion even when source_type is seed/import.",
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
        deleted = apply_deletions(args.database_url, data["deletable_ids"])
        print(f"Apply: deleted {deleted} recipes (gold-protected skipped: {data['protected_gold_status']})")
    else:
        print(
            f"Dry-run: would delete {data['deletable_count']} recipes "
            f"(blocked {data['blocked_count']}, gold-protected {data['protected_gold_status']})"
        )
    print(f"Report: {REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
