"""Menu candidate safety audit for upgraded Gold V3 recipes (read-only)."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "backend" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from audit_gold_v3_post_apply_common import (  # noqa: E402
    extract_upgraded_recipe_ids,
    fetch_recipe_rows,
    forbidden_for_profile,
    has_source_leakage,
    import_sqlalchemy,
    now,
    recipe_text_blob,
    redact_url,
    row_tags,
    write_json,
)


REPORT_JSON = ROOT / "reports" / "SPRINT_1_3M_MENU_SAFETY.json"
REPORT_MD = ROOT / "reports" / "SPRINT_1_3M_MENU_SAFETY.md"
PROFILES = ("no_pork", "vegetarian", "no_seafood", "halal_possible", "child_safe")


def menu_candidate_eligible(row: dict[str, Any]) -> bool:
    if row.get("is_active") is False:
        return False
    source_type = str(row.get("source_type") or "").lower()
    if source_type in {"blocked", "deleted"}:
        return False
    tags = {tag.lower() for tag in row_tags(row.get("tags"))}
    if "blocked" in tags or "hidden" in tags:
        return False
    return True


def evaluate_menu_safety(
    rows: list[dict[str, Any]],
    ingredients_by_id: dict[int, list[dict[str, Any]]],
    steps_by_id: dict[int, list[dict[str, Any]]],
) -> dict[str, Any]:
    items = []
    hard_fail = 0
    profile_summary: dict[str, dict[str, Any]] = {}

    for row in rows:
        recipe_id = int(row["id"])
        ingredients = ingredients_by_id.get(recipe_id) or []
        steps = steps_by_id.get(recipe_id) or []
        text = recipe_text_blob(row, ingredients, steps)
        tags = {tag.lower() for tag in row_tags(row.get("tags"))}
        blockers = []
        warnings = []

        if not menu_candidate_eligible(row):
            blockers.append("not_candidate_eligible")
        leakage = has_source_leakage(text)
        if leakage:
            blockers.append(f"source_leakage:{','.join(leakage)}")
        if "source_url" in json.dumps(row, ensure_ascii=False).lower():
            blockers.append("source_url_in_payload")

        if forbidden_for_profile(text, "no_pork") and ("no_pork" in tags or "no pork" in tags):
            blockers.append("no_pork_plus_pork")
        if forbidden_for_profile(text, "vegetarian") and "vegetarian" in tags:
            blockers.append("vegetarian_plus_meat_fish")
        if forbidden_for_profile(text, "no_seafood") and ("no_seafood" in tags or "no seafood" in tags):
            blockers.append("no_seafood_plus_seafood")

        if blockers:
            hard_fail += 1
        items.append(
            {
                "id": recipe_id,
                "title": row.get("display_title") or row.get("title"),
                "eligible": menu_candidate_eligible(row),
                "blockers": blockers,
                "warnings": warnings,
            }
        )

    for profile in PROFILES:
        excluded = []
        eligible = []
        for row in rows:
            recipe_id = int(row["id"])
            text = recipe_text_blob(row, ingredients_by_id.get(recipe_id) or [], steps_by_id.get(recipe_id) or [])
            if forbidden_for_profile(text, profile):
                excluded.append(row.get("display_title") or row.get("title"))
            elif menu_candidate_eligible(row):
                eligible.append(row.get("display_title") or row.get("title"))
        profile_summary[profile] = {
            "eligible_count": len(eligible),
            "excluded_count": len(excluded),
            "excluded_titles": excluded[:10],
        }

    upgraded_eligible = sum(1 for item in items if item["eligible"] and not item["blockers"])
    return {
        "generated_at": now(),
        "records": len(rows),
        "passed": hard_fail == 0,
        "hard_fail": hard_fail,
        "upgraded_candidate_eligible_count": upgraded_eligible,
        "restriction_scenarios": profile_summary,
        "items": items,
    }


def build_report() -> dict[str, Any]:
    database_url = os.environ.get("DATABASE_URL")
    if import_sqlalchemy() is None:
        return {
            "generated_at": now(),
            "ok": False,
            "db_available": False,
            "hard_fail": 1,
            "error": "sqlalchemy_unavailable",
            "database_url": redact_url(database_url or ""),
            "items": [],
        }
    recipe_ids = extract_upgraded_recipe_ids().get("recipe_ids") or []
    try:
        rows, ingredients_by_id, steps_by_id = fetch_recipe_rows(recipe_ids, database_url)
    except Exception as exc:
        return {
            "generated_at": now(),
            "ok": False,
            "db_available": False,
            "hard_fail": 1,
            "error": repr(exc),
            "items": [],
        }
    report = evaluate_menu_safety(rows, ingredients_by_id, steps_by_id)
    report["ok"] = report["passed"]
    report["db_available"] = True
    return report


def render(report: dict[str, Any]) -> str:
    lines = [
        "# Sprint 1.3M Menu Safety",
        "",
        f"Generated: `{report['generated_at']}`",
        f"passed: `{report.get('passed')}`",
        f"hard_fail: `{report.get('hard_fail')}`",
        f"upgraded_candidate_eligible_count: `{report.get('upgraded_candidate_eligible_count')}`",
        "",
        "## Restriction scenarios",
        "",
    ]
    for profile, summary in (report.get("restriction_scenarios") or {}).items():
        lines.append(
            f"- `{profile}` eligible=`{summary['eligible_count']}` excluded=`{summary['excluded_count']}`"
        )
    blocked = [item for item in report.get("items") or [] if item.get("blockers")]
    if blocked:
        lines.extend(["", "## Blocked recipes", ""])
        for item in blocked:
            lines.append(f"- {item['id']} {item['title']}: {item['blockers']}")
    return "\n".join(lines) + "\n"


def main() -> int:
    report = build_report()
    write_json(REPORT_JSON, report)
    REPORT_MD.write_text(render(report), encoding="utf-8")
    print(f"Wrote {REPORT_MD}")
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
