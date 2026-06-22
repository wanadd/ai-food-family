"""Identify upgraded Gold V3 recipe IDs from plan/manifest sources (read-only)."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "backend" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from audit_gold_v3_post_apply_common import extract_upgraded_recipe_ids, write_json  # noqa: E402


REPORT_JSON = ROOT / "reports" / "SPRINT_1_3M_UPGRADED_RECIPE_IDS.json"
REPORT_MD = ROOT / "reports" / "SPRINT_1_3M_UPGRADED_RECIPE_IDS.md"


def render(report: dict[str, Any]) -> str:
    lines = [
        "# Sprint 1.3M Upgraded Recipe IDs",
        "",
        f"Generated: `{report['generated_at']}`",
        f"passed: `{report['passed']}`",
        f"confirmed_plan_id: `{report['confirmed_plan_id']}`",
        f"computed_plan_id: `{report['computed_plan_id']}`",
        f"plan_id_matches_confirmed: `{report['plan_id_matches_confirmed']}`",
        f"backup_path: `{report.get('backup_path')}`",
        f"recipe_id_count: `{report['recipe_id_count']}`",
        "",
        "## Sources",
        "",
    ]
    for source in report.get("sources") or []:
        lines.append(
            f"- `{source['name']}` count=`{source['count']}` path=`{source.get('path')}`"
        )
    if report.get("source_mismatches"):
        lines.extend(["", "## Source mismatches", ""])
        for name, ids in report["source_mismatches"].items():
            lines.append(f"- `{name}`: `{ids}`")
    lines.extend(["", "## Recipe IDs", "", ", ".join(str(recipe_id) for recipe_id in report.get("recipe_ids") or [])])
    return "\n".join(lines) + "\n"


def run() -> dict[str, Any]:
    report = extract_upgraded_recipe_ids()
    write_json(REPORT_JSON, report)
    REPORT_MD.write_text(render(report), encoding="utf-8")
    return report


def main() -> int:
    report = run()
    print(f"Wrote {REPORT_MD}")
    print(
        f"recipe_id_count={report['recipe_id_count']} "
        f"plan_id_matches={report['plan_id_matches_confirmed']} "
        f"plan_id_verification_skipped={report.get('plan_id_verification_skipped')}"
    )
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
