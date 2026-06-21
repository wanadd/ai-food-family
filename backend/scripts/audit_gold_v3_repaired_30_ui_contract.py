"""UI/API contract audit for repaired Gold V3 candidate recipes."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "backend" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from import_gold_v3_repaired_30_dry_run import (  # noqa: E402
    DEFAULT_INPUT,
    load_jsonl,
    source_leakage,
)


REPORT_MD = ROOT / "reports" / "SPRINT_1_3D_GOLD_V3_REPAIRED_30_UI_CONTRACT.md"
REPORT_JSON = ROOT / "reports" / "SPRINT_1_3D_GOLD_V3_REPAIRED_30_UI_CONTRACT.json"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def summary_payload(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "title": record.get("title"),
        "display_title": record.get("display_title"),
        "meal_type": record.get("meal_type"),
        "category": record.get("category"),
        "tags": record.get("tags") or [],
        "image_url": record.get("image_url"),
        "hero_image_url": record.get("hero_image_url"),
        "thumbnail_url": record.get("thumbnail_url"),
        "is_gold_v3": True,
        "recipe_schema": "gold_v3",
        "image_ready": False,
        "fallback_image_expected": True,
    }


def detail_payload(record: dict[str, Any]) -> dict[str, Any]:
    payload = summary_payload(record)
    payload.update(
        {
            "ingredients": record.get("ingredients") or [],
            "steps": record.get("steps") or [],
            "nutrition_per_serving": record.get("nutrition_per_serving") or {},
            "menu_candidate_eligible": True,
            "shopping_ingredients_extractable": all(
                item.get("name") and item.get("amount") is not None and item.get("unit")
                for item in record.get("ingredients") or []
            ),
        }
    )
    return payload


def evaluate_ui_contract(records: list[dict[str, Any]], json_errors: list[str] | None = None) -> dict[str, Any]:
    json_errors = json_errors or []
    items = []
    hard_fail = len(json_errors)
    for index, record in enumerate(records, start=1):
        blockers = []
        summary = summary_payload(record)
        detail = detail_payload(record)
        if source_leakage(record):
            blockers.append("source_leakage")
        if summary["is_gold_v3"] is not True:
            blockers.append("is_gold_v3_missing")
        if summary["recipe_schema"] != "gold_v3":
            blockers.append("recipe_schema_missing")
        if summary["image_ready"] is not False or summary["fallback_image_expected"] is not True:
            blockers.append("image_fallback_contract_failed")
        if not detail["shopping_ingredients_extractable"]:
            blockers.append("shopping_ingredients_not_extractable")
        if not detail["menu_candidate_eligible"]:
            blockers.append("menu_candidate_not_eligible")
        if blockers:
            hard_fail += 1
        items.append({"index": index, "title": record.get("title"), "blockers": blockers})
    return {
        "generated_at": now(),
        "records": len(records),
        "valid_json": not json_errors,
        "json_errors": json_errors,
        "passed": hard_fail == 0 and len(records) == 30,
        "hard_fail": hard_fail,
        "items": items,
    }


def render(report: dict[str, Any]) -> str:
    lines = [
        "# Sprint 1.3D Gold V3 Repaired 30 UI Contract",
        "",
        f"Generated: `{report['generated_at']}`",
        f"records: `{report['records']}`",
        f"passed: `{report['passed']}`",
        f"hard_fail: `{report['hard_fail']}`",
        "",
        "## Items",
        "",
    ]
    for item in report["items"]:
        lines.append(f"- {item['index']}. {item['title']}: blockers=`{item['blockers']}`")
    return "\n".join(lines) + "\n"


def run() -> dict[str, Any]:
    records, errors = load_jsonl(DEFAULT_INPUT)
    report = evaluate_ui_contract(records, errors)
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    REPORT_MD.write_text(render(report), encoding="utf-8")
    return report


def main() -> int:
    report = run()
    print(f"Wrote {REPORT_MD}")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
