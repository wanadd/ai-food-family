"""Generate Sprint 1.3M frontend visual QA checklist (read-only, no screenshots committed)."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "backend" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from audit_gold_v3_post_apply_common import extract_upgraded_recipe_ids, now, write_json  # noqa: E402


REPORT_MD = ROOT / "reports" / "SPRINT_1_3M_FRONTEND_VISUAL_QA.md"
REPORT_JSON = ROOT / "reports" / "SPRINT_1_3M_FRONTEND_VISUAL_QA.json"
SAMPLE_IDS = 5


def build_report() -> dict[str, Any]:
    id_report = extract_upgraded_recipe_ids()
    recipe_ids = id_report.get("recipe_ids") or []
    sample_ids = recipe_ids[:SAMPLE_IDS]
    routes = [
        {"route": "/plan/recipes", "check": "Recipes catalog lists upgraded titles without null/undefined/NaN"},
        {"route": f"/plan/recipes/{sample_ids[0] if sample_ids else 'ID'}", "check": "Recipe detail renders title, nutrition, ingredients list, steps list (not raw JSON)"},
        {"route": "/plan/today", "check": "Menu screen can surface upgraded recipe if selected; no source leakage"},
        {"route": "/shopping", "check": "Shopping list shows ingredient names/units without duplicate units or technical JSON"},
        {"route": "/wellness", "check": "Nutrition display readable when recipe nutrition referenced"},
    ]
    blockers_to_watch = [
        "white CTA in light theme",
        "image overlap / broken placeholder",
        "null / undefined / NaN in UI",
        "technical labels or source_url leakage",
        "ingredients/steps rendered as raw JSON",
        "broken BackButton after opening recipe from menu/catalog",
    ]
    return {
        "generated_at": now(),
        "mode": "manual_checklist",
        "playwright_available": False,
        "sample_recipe_ids": sample_ids,
        "routes": routes,
        "blockers_to_watch": blockers_to_watch,
        "passed": None,
        "notes": "Automated Playwright recipe smoke not present in repo; perform manual spot-check on sample upgraded IDs after API contract passes.",
    }


def render(report: dict[str, Any]) -> str:
    lines = [
        "# Sprint 1.3M Frontend Visual QA",
        "",
        f"Generated: `{report['generated_at']}`",
        f"mode: `{report['mode']}`",
        f"sample_recipe_ids: `{report.get('sample_recipe_ids')}`",
        "",
        "## Routes to verify",
        "",
    ]
    for item in report.get("routes") or []:
        lines.append(f"- `{item['route']}` — {item['check']}")
    lines.extend(["", "## User-facing blockers to reject", ""])
    for blocker in report.get("blockers_to_watch") or []:
        lines.append(f"- {blocker}")
    lines.extend(
        [
            "",
            "## Result",
            "",
            "Manual QA pending unless API contract + shopping/menu audits pass locally/prod.",
            "No screenshots committed.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    report = build_report()
    write_json(ROOT / "reports" / "SPRINT_1_3M_FRONTEND_VISUAL_QA.json", report)
    REPORT_MD.write_text(render(report), encoding="utf-8")
    print(f"Wrote {REPORT_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
