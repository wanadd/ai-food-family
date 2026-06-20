#!/usr/bin/env python3
"""Build PlanAm V1 recipe catalog JSON from Povarenok candidates.

Pipeline step after select_povarenok_candidates.py — enriches raw records with
meal_type, category, steps, and V1 metadata required by import_recipes.py.

Run from the repository root:
    python backend/scripts/build_planam_v1_catalog.py
    python backend/scripts/build_planam_v1_catalog.py --input exports/povarenok_candidates_150.jsonl
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from recipe_image_utils import short_visual_description  # noqa: E402


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT_PATH = ROOT / "exports" / "povarenok_candidates_150.jsonl"
DEFAULT_OUTPUT_PATH = ROOT / "data" / "planam_v1_recipes.json"
DEFAULT_REPORT_PATH = ROOT / "reports" / "planam_v1_catalog_build_report.md"

BREAKFAST_PATTERNS = (
    r"\bкаш[аеиу]",
    r"\bомлет",
    r"\bсырник",
    r"\bтворог",
    r"\bовсян",
    r"\bгречн",
    r"\bзавтрак",
    r"\bблин",
    r"\bйогурт",
)
SOUP_PATTERNS = (
    r"\bсуп",
    r"\bборщ",
    r"\bщ[иь]",
    r"\bуха\b",
    r"\bбульон",
    r"\bсолянк",
    r"\bхарч",
)
SALAD_PATTERNS = (
    r"\bсалат",
    r"\bвинегрет",
)
KIDS_PATTERNS = (
    r"\bдет",
    r"\bмалыш",
    r"\bдля детей",
)
QUICK_PATTERNS = (
    r"\bбыстр",
    r"\b15 мин",
    r"\b10 мин",
    r"\bза \d+ мин",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build PlanAm V1 catalog JSON")
    parser.add_argument(
        "--input",
        default=str(DEFAULT_INPUT_PATH),
        help="Selected Povarenok candidates JSONL",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT_PATH),
        help="Output import JSON path",
    )
    parser.add_argument(
        "--report",
        default=str(DEFAULT_REPORT_PATH),
        help="Markdown build report path",
    )
    return parser.parse_args()


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


def matches_any(text: str, patterns: tuple[str, ...]) -> bool:
    return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in patterns)


def infer_meal_type(title: str) -> str:
    text = normalize_text(title)
    if matches_any(text, BREAKFAST_PATTERNS):
        return "breakfast"
    if matches_any(text, SOUP_PATTERNS):
        return "lunch"
    return "dinner"


SIDE_PATTERNS = (
    r"\bгарнир\b",
)


def display_title_from(title: str) -> str | None:
    cleaned = re.sub(r"\s+", " ", title.strip())
    unquoted = re.sub(r'^["«»\']+|["«»\']+$', "", cleaned).strip()
    if not unquoted or unquoted == cleaned:
        return None
    return unquoted[:200]


def infer_category(title: str, meal_type: str) -> str:
    text = normalize_text(title)
    if matches_any(text, SOUP_PATTERNS):
        return "soup"
    if matches_any(text, SALAD_PATTERNS):
        return "salad"
    if matches_any(text, KIDS_PATTERNS):
        return "kids"
    if matches_any(text, SIDE_PATTERNS):
        return "side"
    if meal_type == "breakfast":
        return "breakfast"
    if matches_any(text, QUICK_PATTERNS):
        return "quick"
    return "main"


def infer_tags(title: str, meal_type: str, category: str) -> list[str]:
    text = normalize_text(title)
    tags = ["v1", "family", meal_type, category]
    for keyword, tag in (
        ("куриц", "chicken"),
        ("курин", "chicken"),
        ("говядин", "beef"),
        ("индейк", "turkey"),
        ("рыб", "fish"),
        ("суп", "soup"),
        ("каш", "porridge"),
        ("запекан", "casserole"),
        ("паст", "pasta"),
        ("макарон", "pasta"),
        ("овощ", "vegetables"),
    ):
        if keyword in text and tag not in tags:
            tags.append(tag)
    return tags[:8]


def default_steps(title: str) -> list[str]:
    return [
        f"Подготовьте все ингредиенты для блюда «{title}».",
        "Приготовьте блюдо по классической технологии: обжарка, тушение или запекание.",
        "Проверьте готовность, при необходимости доведите до вкуса и подайте к столу.",
    ]


def default_description(title: str, category: str) -> str:
    labels = {
        "soup": "Семейный суп на каждый день.",
        "main": "Сытное домашнее блюдо для всей семьи.",
        "salad": "Простой салат из обычных продуктов.",
        "quick": "Быстрое блюдо на будни.",
        "kids": "Подходит для семейного стола и детей.",
    }
    return labels.get(category, f"Домашний рецепт «{title}» для повседневного меню.")


def normalize_ingredients(raw: list[Any]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "").strip()
        if not name:
            continue
        quantity = str(item.get("quantity") or item.get("amount") or "1").strip()
        unit = str(item.get("unit") or "шт").strip() or "шт"
        amount = str(item.get("amount") or f"{quantity} {unit}".strip()).strip()
        result.append(
            {
                "name": name[:120],
                "quantity": quantity[:32],
                "unit": unit[:32],
                "amount": amount[:64],
                "category": str(item.get("category") or "other")[:32],
            }
        )
    return result


def enrich_record(record: dict[str, Any]) -> dict[str, Any]:
    title = str(record.get("title") or "").strip()
    meal_type = infer_meal_type(title)
    category = infer_category(title, meal_type)
    ingredients = normalize_ingredients(record.get("ingredients") or [])
    if len(ingredients) < 3:
        raise ValueError("too few ingredients")
    if len(ingredients) > 25:
        raise ValueError("too many ingredients")

    tags = infer_tags(title, meal_type, category)
    if "steps_generated" not in tags:
        tags.append("steps_generated")

    return {
        "title": title[:200],
        "original_title": title[:200],
        "normalized_title": normalize_text(title)[:200],
        "display_title": display_title_from(title),
        "description": default_description(title, category),
        "meal_type": meal_type,
        "category": category,
        "cuisine": "home",
        "difficulty": "easy",
        "prep_time_minutes": 15,
        "cooking_time_minutes": 35,
        "servings": 4,
        "source_type": "v1_import",
        "source_url": str(record.get("source_url") or "").strip() or None,
        "image_url": record.get("image_url"),
        "hero_image_url": record.get("hero_image_url"),
        "thumbnail_url": record.get("thumbnail_url"),
        "short_visual_description": short_visual_description(title, meal_type, category),
        "steps_quality": "steps_generated",
        "suitable_for_children": True,
        "suitable_for_sport": False,
        "suitable_for_event": False,
        "is_drink": False,
        "is_alcoholic": False,
        "diets": ["budget"],
        "tags": tags,
        "allergens": [],
        "restrictions": [],
        "ingredients": ingredients,
        "steps": default_steps(title),
    }


def build_report(
    *,
    input_path: Path,
    output_path: Path,
    report_path: Path,
    total: int,
    written: int,
    skipped: int,
    skip_reasons: Counter[str],
    meal_counts: Counter[str],
    category_counts: Counter[str],
) -> str:
    lines = [
        "# PlanAm V1 Catalog Build Report",
        "",
        "## Source",
        "",
        f"- Input: `{input_path}`",
        f"- Output: `{output_path}`",
        f"- Report: `{report_path}`",
        "",
        "## Summary",
        "",
        f"- Total read: `{total}`",
        f"- Written: `{written}`",
        f"- Skipped: `{skipped}`",
        "",
        "## Meal Types",
        "",
    ]
    for key, count in meal_counts.most_common():
        lines.append(f"- {key}: `{count}`")
    lines.extend(["", "## Categories", ""])
    for key, count in category_counts.most_common():
        lines.append(f"- {key}: `{count}`")
    lines.extend(["", "## Skip Reasons", ""])
    if skip_reasons:
        for reason, count in skip_reasons.most_common():
            lines.append(f"- {reason}: `{count}`")
    else:
        lines.append("- `n/a`")
    return "\n".join(lines).rstrip() + "\n"


def build_catalog(args: argparse.Namespace) -> tuple[int, Path, Path]:
    input_path = Path(args.input).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()
    report_path = Path(args.report).expanduser().resolve()
    if not input_path.exists():
        raise SystemExit(f"Input file not found: {input_path}")

    recipes: list[dict[str, Any]] = []
    seen_titles: set[str] = set()
    total = 0
    skipped = 0
    skip_reasons: Counter[str] = Counter()
    meal_counts: Counter[str] = Counter()
    category_counts: Counter[str] = Counter()

    with input_path.open("r", encoding="utf-8") as source:
        for line in source:
            if not line.strip():
                continue
            total += 1
            try:
                record = json.loads(line)
                enriched = enrich_record(record)
            except Exception as exc:
                skipped += 1
                skip_reasons[str(exc)] += 1
                continue

            title_key = normalize_text(enriched["title"])
            if title_key in seen_titles:
                skipped += 1
                skip_reasons["duplicate_title"] += 1
                continue
            seen_titles.add(title_key)
            recipes.append(enriched)
            meal_counts[enriched["meal_type"]] += 1
            category_counts[enriched["category"]] += 1

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(recipes, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        build_report(
            input_path=input_path,
            output_path=output_path,
            report_path=report_path,
            total=total,
            written=len(recipes),
            skipped=skipped,
            skip_reasons=skip_reasons,
            meal_counts=meal_counts,
            category_counts=category_counts,
        ),
        encoding="utf-8",
    )
    return len(recipes), output_path, report_path


def main() -> int:
    args = parse_args()
    written, output_path, report_path = build_catalog(args)
    print(f"Built {written} V1 recipes")
    print(f"Catalog written to: {output_path}")
    print(f"Report written to: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
