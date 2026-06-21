"""Quality gate for data/recipe_v2/gold_recipes_30_repaired_candidate.jsonl."""

from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
INPUT = ROOT / "data" / "recipe_v2" / "gold_recipes_30_repaired_candidate.jsonl"
REPORTS = ROOT / "reports"
REPORT_JSON = REPORTS / "SPRINT_1_3C_GOLD_RECIPES_30_QUALITY_GATE.json"
REPORT_MD = REPORTS / "SPRINT_1_3C_GOLD_RECIPES_30_QUALITY_GATE.md"
ENGLISH_PREFIX_RE = re.compile(
    r"^\s*(high protein|pro weight loss|pre-workout|pro\s+[a-z][a-z\s-]*)\s*:",
    re.I,
)
PORK_WORDS = ("свинина", "свиной", "свиная", "свиные", "свиным", "бекон", "ветчина")
MEAT_WORDS = ("куриц", "курин", "индейк", "говядин", "свинин", "бекон", "ветчина", "фарш", "рыб", "лосось", "кревет")
SEAFOOD_WORDS = ("кревет", "морепродукт", "мидии", "кальмар")
ALCOHOL_WORDS = ("вино", "пиво", "водка", "коньяк", "ром", "алкоголь")
CAFFEINE_WORDS = ("кофе", "энергетик", "матча")
SOURCE_MARKERS = ("povarenok", "поваренок", "source_url", "original_url", "http://", "https://")


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "").strip()).lower()


def ingredient_names(recipe: dict[str, Any]) -> list[str]:
    return [
        str(item.get("name") or item.get("display_name") or item.get("canonical_name") or "")
        for item in recipe.get("ingredients") or []
    ]


def full_text(recipe: dict[str, Any]) -> str:
    parts = [
        recipe.get("title"),
        recipe.get("display_title"),
        recipe.get("description"),
        " ".join(ingredient_names(recipe)),
        " ".join(str(step.get("text") or step.get("instruction") or "") for step in recipe.get("steps") or []),
        " ".join(str(tag) for tag in recipe.get("tags") or []),
    ]
    return normalize(" ".join(str(part or "") for part in parts))


def has_any(text: str, markers: tuple[str, ...]) -> bool:
    return any(marker in text for marker in markers)


def nutrition_core_complete(recipe: dict[str, Any]) -> bool:
    nutrition = recipe.get("nutrition_per_serving") or {}
    return all(nutrition.get(field) is not None for field in ("kcal", "protein_g", "fat_g", "carbs_g"))


def shopping_ready(recipe: dict[str, Any]) -> bool:
    for item in recipe.get("ingredients") or []:
        if not (item.get("name") or item.get("display_name")):
            return False
        if not item.get("shopping_category_slug"):
            return False
        if item.get("amount") is None or not item.get("unit"):
            return False
    return bool(recipe.get("ingredients"))


def contradiction_codes(recipe: dict[str, Any]) -> list[str]:
    tags = {normalize(tag) for tag in recipe.get("tags") or []}
    tags.update(normalize(tag) for tag in recipe.get("diet_tags") or [])
    tags.update(normalize(tag) for tag in recipe.get("excludes") or [])
    text = full_text(recipe)
    codes = []
    if ("no_pork" in tags or "no_pork_possible" in tags) and has_any(text, PORK_WORDS):
        codes.append("no_pork_plus_pork")
    if "vegetarian" in tags and has_any(text, MEAT_WORDS):
        codes.append("vegetarian_plus_meat_fish")
    if "halal_possible" in tags and (has_any(text, PORK_WORDS) or has_any(text, ALCOHOL_WORDS)):
        codes.append("halal_plus_pork_or_alcohol")
    if ("child_safe" in tags or "suitable_for_children" in tags) and (
        has_any(text, ALCOHOL_WORDS) or has_any(text, CAFFEINE_WORDS)
    ):
        codes.append("child_safe_plus_alcohol_or_caffeine")
    if ("no_seafood" in tags or "no_seafood_possible" in tags) and has_any(text, SEAFOOD_WORDS):
        codes.append("no_seafood_plus_seafood")
    return codes


def validate_record(recipe: dict[str, Any], duplicate_titles: set[str]) -> tuple[bool, list[str]]:
    blockers: list[str] = []
    title = str(recipe.get("title") or "")
    text = full_text(recipe)
    if recipe.get("schema_version") != "recipe_gold_v3":
        blockers.append("schema_version_missing")
    if not recipe.get("source_type"):
        blockers.append("source_type_missing")
    if recipe.get("meal_type") not in {"breakfast", "lunch", "dinner", "snack"}:
        blockers.append("meal_type_missing")
    if not title.strip() or ENGLISH_PREFIX_RE.search(title) or "#" in title:
        blockers.append("title_garbage")
    if normalize(title) in duplicate_titles:
        blockers.append("duplicate_normalized_title")
    if len(recipe.get("ingredients") or []) < 3:
        blockers.append("ingredients_lt_3")
    if len(recipe.get("steps") or []) < 3:
        blockers.append("steps_lt_3")
    if not nutrition_core_complete(recipe):
        blockers.append("nutrition_core_incomplete")
    if not shopping_ready(recipe):
        blockers.append("shopping_fields_incomplete")
    if not recipe.get("image_prompt"):
        blockers.append("image_prompt_missing")
    if any(marker in text for marker in SOURCE_MARKERS):
        blockers.append("source_leakage")
    blockers.extend(contradiction_codes(recipe))
    return not blockers, blockers


def load_records() -> tuple[list[dict[str, Any]], list[str]]:
    records = []
    errors = []
    if not INPUT.exists():
        return [], [f"Missing input: {INPUT}"]
    for index, line in enumerate(INPUT.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError as exc:
            errors.append(f"line {index}: {exc}")
    return records, errors


def evaluate(records: list[dict[str, Any]], json_errors: list[str] | None = None) -> dict[str, Any]:
    json_errors = json_errors or []
    title_counts = Counter(normalize(recipe.get("title") or "") for recipe in records)
    duplicate_titles = {title for title, count in title_counts.items() if title and count > 1}
    items = []
    blocker_counts: Counter[str] = Counter()
    valid_for_import = 0
    for index, recipe in enumerate(records, start=1):
        ok, blockers = validate_record(recipe, duplicate_titles)
        blocker_counts.update(blockers)
        if ok:
            valid_for_import += 1
        items.append(
            {
                "index": index,
                "title": recipe.get("title"),
                "ok": ok,
                "blockers": blockers,
                "ingredients_count": len(recipe.get("ingredients") or []),
                "steps_count": len(recipe.get("steps") or []),
                "tags": recipe.get("tags") or [],
                "meal_type": recipe.get("meal_type"),
            }
        )
    hard_fail = len(json_errors) + sum(1 for item in items if item["blockers"])
    return {
        "generated_at": now(),
        "input": str(INPUT.relative_to(ROOT)),
        "valid_json": len(json_errors) == 0,
        "record_count": len(records),
        "json_errors": json_errors,
        "valid_for_import": valid_for_import,
        "hard_fail": hard_fail,
        "blocker_counts": dict(blocker_counts),
        "top_blockers": blocker_counts.most_common(10),
        "acceptance": {
            "hard_fail_eq_0": hard_fail == 0,
            "valid_for_import_gte_25": valid_for_import >= 25,
            "ready_for_1_3d_import": hard_fail == 0 and valid_for_import >= 25,
        },
        "items": items,
    }


def render(report: dict[str, Any]) -> str:
    lines = [
        "# Sprint 1.3C Gold Recipes 30 Quality Gate",
        "",
        f"Generated: `{report['generated_at']}`",
        f"Input: `{report['input']}`",
        f"Valid JSON: `{report['valid_json']}`",
        f"Record count: `{report['record_count']}`",
        f"valid_for_import: `{report['valid_for_import']}`",
        f"hard_fail: `{report['hard_fail']}`",
        f"ready_for_1_3d_import: `{report['acceptance']['ready_for_1_3d_import']}`",
        "",
        "## Top Blockers",
        "",
    ]
    if report["top_blockers"]:
        lines.extend(f"- {code}: `{count}`" for code, count in report["top_blockers"])
    else:
        lines.append("- none")
    lines.extend(["", "## Items", ""])
    for item in report["items"]:
        lines.append(f"- {item['index']}. {item['title']}: ok=`{item['ok']}`, blockers=`{item['blockers']}`")
    return "\n".join(lines) + "\n"


def run() -> dict[str, Any]:
    REPORTS.mkdir(exist_ok=True)
    records, json_errors = load_records()
    report = evaluate(records, json_errors)
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    REPORT_MD.write_text(render(report), encoding="utf-8")
    return report


def main() -> int:
    report = run()
    print(f"Wrote {REPORT_MD}")
    return 0 if report["record_count"] == 30 and report["valid_json"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
