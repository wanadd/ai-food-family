"""Menu and shopping dry-run audit for repaired Gold V3 candidate recipes."""

from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "backend" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from import_gold_v3_repaired_30_dry_run import DEFAULT_INPUT, load_jsonl, normalize  # noqa: E402


REPORT_MD = ROOT / "reports" / "SPRINT_1_3D_GOLD_V3_MENU_SHOPPING_DRY_RUN.md"
REPORT_JSON = ROOT / "reports" / "SPRINT_1_3D_GOLD_V3_MENU_SHOPPING_DRY_RUN.json"
PORK_WORDS = ("свинина", "свиной", "свиная", "свиные", "бекон", "ветчина")
MEAT_WORDS = ("куриц", "курин", "индейк", "говядин", "свинин", "бекон", "ветчина", "фарш", "рыб", "лосось", "кревет")
SEAFOOD_WORDS = ("кревет", "морепродукт", "мидии", "кальмар")
ALCOHOL_WORDS = ("вино", "пиво", "водка", "коньяк", "ром", "алкоголь")
CAFFEINE_WORDS = ("кофе", "энергетик", "матча")


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def recipe_text(record: dict[str, Any]) -> str:
    ingredients = " ".join(
        str(item.get("name") or item.get("display_name") or item.get("canonical_name") or "")
        for item in record.get("ingredients") or []
    )
    tags = " ".join(str(tag) for tag in record.get("tags") or [])
    return normalize(f"{record.get('title')} {record.get('display_title')} {ingredients} {tags}")


def has_any(text: str, words: tuple[str, ...]) -> bool:
    return any(word in text for word in words)


def forbidden_for_profile(record: dict[str, Any], profile: str) -> bool:
    text = recipe_text(record)
    if profile == "no_pork":
        return has_any(text, PORK_WORDS)
    if profile == "vegetarian":
        return has_any(text, MEAT_WORDS)
    if profile == "no_seafood":
        return has_any(text, SEAFOOD_WORDS)
    if profile == "child_safe":
        return has_any(text, ALCOHOL_WORDS) or has_any(text, CAFFEINE_WORDS)
    return False


def shopping_extractable(record: dict[str, Any]) -> bool:
    ingredients = record.get("ingredients") or []
    return bool(ingredients) and all(
        (item.get("name") or item.get("display_name"))
        and item.get("amount") is not None
        and item.get("unit")
        and (item.get("shopping_category_slug") or item.get("pantry_category_slug"))
        for item in ingredients
    )


def tag_values(record: dict[str, Any]) -> set[str]:
    values: set[str] = set()
    for tag in record.get("tags") or []:
        raw = str(tag or "").strip().lower()
        if raw:
            values.add(raw)
            values.add(normalize(raw))
    return values


def evaluate_menu_shopping(records: list[dict[str, Any]], json_errors: list[str] | None = None) -> dict[str, Any]:
    json_errors = json_errors or []
    profiles = ("no_pork", "vegetarian", "no_seafood", "child_safe", "athlete_high_protein")
    items = []
    hard_fail = len(json_errors)
    profile_summary: dict[str, dict[str, Any]] = {}
    shopping_missing = []
    ingredient_count = 0
    for index, record in enumerate(records, start=1):
        ingredient_count += len(record.get("ingredients") or [])
        blockers = []
        tags = tag_values(record)
        if not shopping_extractable(record):
            blockers.append("shopping_not_extractable")
            shopping_missing.append({"index": index, "title": record.get("title")})
        if forbidden_for_profile(record, "no_pork") and ("no_pork" in tags or "no pork" in tags):
            blockers.append("no_pork_plus_pork")
        if forbidden_for_profile(record, "vegetarian") and "vegetarian" in tags:
            blockers.append("vegetarian_plus_meat_fish")
        if blockers:
            hard_fail += 1
        items.append({"index": index, "title": record.get("title"), "blockers": blockers})

    for profile in profiles:
        if profile == "athlete_high_protein":
            eligible = [
                record.get("title")
                for record in records
                if (record.get("nutrition_per_serving") or {}).get("protein_g", 0) >= 25
                or "high_protein" in tag_values(record)
                or "high protein" in tag_values(record)
            ]
            excluded = []
        else:
            excluded = [record.get("title") for record in records if forbidden_for_profile(record, profile)]
            eligible = [record.get("title") for record in records if not forbidden_for_profile(record, profile)]
        profile_summary[profile] = {
            "eligible_count": len(eligible),
            "excluded_count": len(excluded),
            "excluded_titles": excluded,
        }

    return {
        "generated_at": now(),
        "records": len(records),
        "valid_json": not json_errors,
        "json_errors": json_errors,
        "passed": hard_fail == 0 and len(records) == 30 and not shopping_missing,
        "hard_fail": hard_fail,
        "meal_type_distribution": dict(Counter(record.get("meal_type") for record in records)),
        "category_distribution": dict(Counter(record.get("category") for record in records)),
        "protein_distribution": {
            "high_protein_count": sum(
                1 for record in records if (record.get("nutrition_per_serving") or {}).get("protein_g", 0) >= 25
            )
        },
        "ingredient_total": ingredient_count,
        "shopping_missing": shopping_missing,
        "restriction_scenarios": profile_summary,
        "items": items,
    }


def render(report: dict[str, Any]) -> str:
    lines = [
        "# Sprint 1.3D Gold V3 Menu Shopping Dry-Run",
        "",
        f"Generated: `{report['generated_at']}`",
        f"records: `{report['records']}`",
        f"passed: `{report['passed']}`",
        f"hard_fail: `{report['hard_fail']}`",
        f"ingredient_total: `{report['ingredient_total']}`",
        "",
        "## Restriction Scenarios",
        "",
    ]
    for profile, data in report["restriction_scenarios"].items():
        lines.append(f"- {profile}: eligible=`{data['eligible_count']}`, excluded=`{data['excluded_count']}`")
    lines.extend(["", "## Shopping Missing", ""])
    if report["shopping_missing"]:
        lines.extend(f"- {item['index']}. {item['title']}" for item in report["shopping_missing"])
    else:
        lines.append("- none")
    return "\n".join(lines) + "\n"


def run() -> dict[str, Any]:
    records, errors = load_jsonl(DEFAULT_INPUT)
    report = evaluate_menu_shopping(records, errors)
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
