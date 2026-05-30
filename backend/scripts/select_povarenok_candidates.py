#!/usr/bin/env python3
"""Select safe Povarenok candidates for enrichment and test import.

Run from the repository root:
    python backend/scripts/select_povarenok_candidates.py --limit 100
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT_PATH = ROOT / "exports" / "povarenok_planam_raw.jsonl"
DEFAULT_OUTPUT_PATH = ROOT / "exports" / "povarenok_candidates_100.jsonl"
DEFAULT_REPORT_PATH = ROOT / "reports" / "povarenok_candidates_report.md"
DEFAULT_LIMIT = 100
DEFAULT_SAMPLE_SIZE = 20

ALCOHOL_PATTERNS = (
    r"\bалкогол",
    r"\bводк",
    r"\bвино\b",
    r"\bвинн",
    r"\bконьяк",
    r"\bром\b",
    r"\bликер",
    r"\bликёр",
    r"\bпиво\b",
    r"\bспирт",
    r"\bнастойк",
    r"\bналивк",
    r"\bсамогон",
)
PRESERVE_PATTERNS = (
    r"на зиму",
    r"\bзаготов",
    r"\bконсерв",
    r"\bмарин",
    r"\bсолень",
    r"\bваренье",
    r"\bджем\b",
    r"\bкомпот",
    r"\bзакатк",
)
DESSERT_PATTERNS = (
    r"\bторт",
    r"\bтортик",
    r"\bпирожн",
    r"\bдесерт",
    r"\bкекс",
    r"\bпечень",
    r"\bпирог",
    r"\bватруш",
    r"\bбулоч",
    r"\bмаффин",
    r"\bманник",
    r"\bкурд\b",
    r"\bсладк",
    r"\bконфет",
    r"\bморожен",
    r"\bшоколад",
    r"\bсуфле",
)
COMPLEX_BAKING_PATTERNS = (
    r"\bбисквит",
    r"\bкулич",
    r"\bпасхальн",
    r"\bслоен",
    r"\bслоён",
    r"\bзаварн",
    r"\bдрожжев",
    r"\bтесто\b",
    r"\bкрем\b",
    r"\bмастик",
    r"\bглазур",
    r"\bмеренг",
    r"\bэклер",
)
PRIORITY_PATTERNS = (
    r"\bсуп",
    r"\bщи\b",
    r"\bборщ",
    r"\bкаша",
    r"\bкуриц",
    r"\bкурин",
    r"\bиндей",
    r"\bрыб",
    r"\bкартоф",
    r"\bовощ",
    r"\bсалат",
    r"\bзапеканк",
    r"\bкотлет",
    r"\bтефтел",
    r"\bпаста\b",
    r"\bмакарон",
    r"\bдет",
    r"\bзавтрак",
    r"\bомлет",
    r"\bсырник",
    r"\bтворог",
    r"\bрис\b",
    r"\bгреч",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Select Povarenok candidates without AI or DB import"
    )
    parser.add_argument(
        "--input",
        default=str(DEFAULT_INPUT_PATH),
        help="Path to the Povarenok raw JSONL file",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT_PATH),
        help="Path to selected candidates JSONL",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=DEFAULT_LIMIT,
        help="Number of candidates to write",
    )
    parser.add_argument(
        "--report",
        default=str(DEFAULT_REPORT_PATH),
        help="Path to Markdown selection report",
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=DEFAULT_SAMPLE_SIZE,
        help="Number of full selected examples to include in the report",
    )
    return parser.parse_args()


def normalize_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip().lower())


def is_empty(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, list):
        return not value
    text = str(value).strip()
    return not text or text.lower() in {"nan", "none", "null", "[]", "{}"}


def matches_any(text: str, patterns: tuple[str, ...]) -> bool:
    return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in patterns)


def ingredient_names_text(record: dict[str, Any]) -> str:
    names = []
    for ingredient in record.get("ingredients") or []:
        if isinstance(ingredient, dict):
            names.append(str(ingredient.get("name") or ""))
    return " ".join(names)


def has_strange_title(title: Any) -> bool:
    raw = str(title or "").strip()
    text = normalize_text(raw)
    if len(raw) < 3 or len(raw) > 90:
        return True
    if len(raw.split()) == 1 and len(raw) < 10:
        return True
    if re.search(r"[{}<>\[\]@#$%^*_+=~`]", raw):
        return True
    if re.search(r"[!?.,;:]{3,}", raw):
        return True
    if re.search(r"(Ð|Ñ|РЎ|Рµ|Р°|Рё|СЃ|С‚|СЊ)", raw):
        return True

    letters = re.findall(r"[A-Za-zА-Яа-яЁё]", raw)
    latin = re.findall(r"[A-Za-z]", raw)
    cyrillic = re.findall(r"[А-Яа-яЁё]", raw)
    if letters and len(latin) / len(letters) > 0.35:
        return True
    if not cyrillic:
        return True
    if re.search(r"\b(test|demo|copy|new|unknown)\b", text):
        return True
    return False


def reject_reason(record: dict[str, Any]) -> str | None:
    title = record.get("title")
    ingredients = record.get("ingredients")
    if is_empty(title):
        return "empty_title"
    if not isinstance(ingredients, list) or not ingredients:
        return "empty_ingredients"

    ingredient_count = len(ingredients)
    if ingredient_count < 3:
        return "too_few_ingredients"
    if ingredient_count > 18:
        return "too_many_ingredients"

    title_text = normalize_text(title)
    combined_text = f"{title_text} {normalize_text(ingredient_names_text(record))}"
    if matches_any(combined_text, ALCOHOL_PATTERNS):
        return "alcohol_or_tincture"
    if matches_any(combined_text, PRESERVE_PATTERNS):
        return "preserves_or_winter"
    if matches_any(title_text, DESSERT_PATTERNS):
        return "cakes_or_desserts"
    if matches_any(title_text, COMPLEX_BAKING_PATTERNS):
        return "complex_baking"
    if has_strange_title(title):
        return "strange_title"
    if not matches_any(title_text, PRIORITY_PATTERNS):
        return "not_priority_family_meal"
    return None


def compact_record(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "title": record.get("title"),
        "source_url": record.get("source_url"),
        "ingredient_count": len(record.get("ingredients") or []),
    }


def build_report(
    input_path: Path,
    output_path: Path,
    report_path: Path,
    total_read: int,
    selected: int,
    skipped: int,
    skip_reasons: Counter[str],
    selected_titles: list[str],
    examples: list[dict[str, Any]],
) -> str:
    lines = [
        "# Povarenok Candidates Report",
        "",
        "## Source",
        "",
        f"- Input: `{input_path}`",
        f"- Output: `{output_path}`",
        f"- Report: `{report_path}`",
        "",
        "## Summary",
        "",
        f"- Total read: `{total_read}`",
        f"- Selected: `{selected}`",
        f"- Skipped: `{skipped}`",
        "",
        "## Skip Reasons",
        "",
    ]

    if skip_reasons:
        for reason, count in skip_reasons.most_common():
            lines.append(f"- {reason}: `{count}`")
    else:
        lines.append("- `n/a`")

    lines.extend(["", "## Selected Recipe Titles", ""])
    if selected_titles:
        for index, title in enumerate(selected_titles, start=1):
            lines.append(f"{index}. {title}")
    else:
        lines.append("No recipes selected.")

    lines.extend(["", "## Full Examples", ""])
    if examples:
        for index, example in enumerate(examples, start=1):
            lines.append(f"### Example {index}")
            lines.append("")
            lines.append("```json")
            lines.append(json.dumps(example, ensure_ascii=False))
            lines.append("```")
            lines.append("")
    else:
        lines.append("No examples.")

    return "\n".join(lines).rstrip() + "\n"


def select_candidates(args: argparse.Namespace) -> tuple[int, Path, Path]:
    if args.limit < 1:
        raise SystemExit("--limit must be at least 1")
    if args.sample_size < 1:
        raise SystemExit("--sample-size must be at least 1")

    input_path = Path(args.input).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()
    report_path = Path(args.report).expanduser().resolve()
    if not input_path.exists():
        raise SystemExit(f"Input file not found: {input_path}")

    total_read = 0
    selected = 0
    skipped = 0
    skip_reasons: Counter[str] = Counter()
    selected_titles: list[str] = []
    examples: list[dict[str, Any]] = []

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with input_path.open("r", encoding="utf-8") as source, output_path.open(
        "w", encoding="utf-8", newline="\n"
    ) as target:
        for line in source:
            if not line.strip():
                continue
            total_read += 1
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                skipped += 1
                skip_reasons["invalid_json"] += 1
                continue

            reason = reject_reason(record)
            if reason is not None:
                skipped += 1
                skip_reasons[reason] += 1
                continue

            if selected < args.limit:
                target.write(json.dumps(record, ensure_ascii=False) + "\n")
                selected += 1
                selected_titles.append(str(record.get("title") or "").strip())
                if len(examples) < args.sample_size:
                    examples.append(record)
            else:
                skipped += 1
                skip_reasons["after_limit"] += 1

    report = build_report(
        input_path=input_path,
        output_path=output_path,
        report_path=report_path,
        total_read=total_read,
        selected=selected,
        skipped=skipped,
        skip_reasons=skip_reasons,
        selected_titles=selected_titles,
        examples=examples,
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")
    return selected, output_path, report_path


def main() -> int:
    args = parse_args()
    selected, output_path, report_path = select_candidates(args)
    print(f"Selected {selected} candidates")
    print(f"Candidates written to: {output_path}")
    print(f"Report written to: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
