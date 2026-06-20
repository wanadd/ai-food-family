#!/usr/bin/env python3
"""Convert Povarenok JSONL (enriched or raw candidates) to import_recipes.py JSON.

Run from the repository root:
    python backend/scripts/convert_enriched_to_import_json.py --input exports/povarenok_enriched_10.jsonl --output exports/povarenok_import_10.json
    python backend/scripts/convert_enriched_to_import_json.py --input exports/povarenok_candidates_100.jsonl --output exports/povarenok_import_100.json
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT_PATH = ROOT / "exports" / "povarenok_enriched_10.jsonl"
DEFAULT_OUTPUT_PATH = ROOT / "exports" / "povarenok_import_10.json"

ALLOWED_MEAL_TYPES = {"breakfast", "lunch", "dinner", "snack"}
ALLOWED_CATEGORIES = {
    "soup",
    "main",
    "salad",
    "dessert",
    "quick",
    "kids",
    "drink",
    "event",
    "bbq",
}
ALLOWED_DIFFICULTIES = {"easy", "medium", "hard"}

BREAKFAST_PATTERNS = (
    r"\bзавтрак",
    r"\bомлет",
    r"\bкаша",
    r"\bсырник",
    r"\bтворог",
    r"\bгранол",
)
SOUP_PATTERNS = (r"\bсуп", r"\bщи\b", r"\bборщ", r"\bсолянк")
SALAD_PATTERNS = (r"\bсалат",)
DESSERT_PATTERNS = (
    r"\bторт",
    r"\bпирог",
    r"\bдесерт",
    r"\bкекс",
    r"\bпечень",
)
SNACK_PATTERNS = (r"\bперекус", r"\bсэндвич", r"\bбутерброд")
KIDS_PATTERNS = (r"\bдет", r"\bмалыш")


def normalize_title_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip().lower())


def infer_meal_type(title: str) -> str:
    text = normalize_title_text(title)
    if any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in BREAKFAST_PATTERNS):
        return "breakfast"
    if any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in DESSERT_PATTERNS):
        return "dessert"
    if any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in SNACK_PATTERNS):
        return "snack"
    return "lunch"


def infer_category(title: str) -> str:
    text = normalize_title_text(title)
    if any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in SOUP_PATTERNS):
        return "soup"
    if any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in SALAD_PATTERNS):
        return "salad"
    if any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in DESSERT_PATTERNS):
        return "dessert"
    if any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in KIDS_PATTERNS):
        return "kids"
    if any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in BREAKFAST_PATTERNS):
        return "quick"
    return "main"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert enriched Povarenok JSONL to import_recipes.py JSON"
    )
    parser.add_argument(
        "--input",
        default=str(DEFAULT_INPUT_PATH),
        help="Path to enriched Povarenok JSONL",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT_PATH),
        help="Path to import_recipes.py JSON file",
    )
    return parser.parse_args()


def is_empty(value: Any) -> bool:
    if value is None:
        return True
    text = str(value).strip()
    return not text or text.lower() in {"none", "null", "nan", "[]", "{}"}


def text_or_none(value: Any) -> str | None:
    if is_empty(value):
        return None
    return str(value).strip()


def scalar(value: Any, default: Any = None) -> Any:
    if isinstance(value, list):
        for item in value:
            if not is_empty(item):
                return scalar(item, default)
        return default
    if is_empty(value):
        return default
    return value


def string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        items: list[str] = []
        for item in value:
            items.extend(string_list(item))
        return list(dict.fromkeys(item for item in items if item))
    text = str(value).strip()
    return [text] if text else []


def int_or_default(value: Any, default: int) -> int:
    value = scalar(value)
    if value is None:
        return default
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def number_or_none(value: Any) -> float | int | None:
    value = scalar(value)
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return int(number) if number.is_integer() else number


def bool_or_default(value: Any, default: bool = False) -> bool:
    value = scalar(value)
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"true", "1", "yes", "да"}:
        return True
    if text in {"false", "0", "no", "нет"}:
        return False
    return default


def normalize_amount(quantity: Any, unit: Any, raw: Any) -> str:
    raw_text = text_or_none(raw)
    if raw_text:
        return raw_text

    quantity_text = text_or_none(quantity)
    unit_text = text_or_none(unit)
    amount = " ".join(part for part in (quantity_text, unit_text) if part).strip()
    return amount or "по вкусу"


def normalize_ingredient(raw: Any) -> dict[str, Any] | None:
    if not isinstance(raw, dict):
        return None
    name = text_or_none(raw.get("name"))
    if not name:
        return None
    quantity = text_or_none(raw.get("quantity"))
    unit = text_or_none(raw.get("unit"))
    return {
        "name": name,
        "quantity": quantity,
        "unit": unit,
        "amount": normalize_amount(quantity, unit, raw.get("raw")),
    }


def normalize_ingredients(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    ingredients = []
    for item in value:
        ingredient = normalize_ingredient(item)
        if ingredient is not None:
            ingredients.append(ingredient)
    return ingredients


def normalize_steps(value: Any) -> list[str]:
    steps = string_list(value)
    return steps or ["Подготовить ингредиенты.", "Приготовить блюдо до готовности."]


def convert_record(record: dict[str, Any]) -> dict[str, Any]:
    enriched = record.get("enriched")
    if not isinstance(enriched, dict):
        enriched = {}

    title = (
        text_or_none(enriched.get("title"))
        or text_or_none(record.get("title"))
        or text_or_none(record.get("raw_title"))
    )
    if not title:
        title = "Без названия"

    meal_type = str(scalar(enriched.get("meal_type"), "")).strip()
    if meal_type not in ALLOWED_MEAL_TYPES:
        meal_type = infer_meal_type(title)

    category = str(scalar(enriched.get("category"), "")).strip()
    if category not in ALLOWED_CATEGORIES:
        category = infer_category(title)

    difficulty = str(scalar(enriched.get("difficulty"), "easy")).strip()
    if difficulty not in ALLOWED_DIFFICULTIES:
        difficulty = "easy"

    cooking_time = int_or_default(enriched.get("cooking_time_minutes"), 30)
    prep_time = int_or_default(enriched.get("prep_time_minutes"), cooking_time or 30)

    raw_steps = enriched.get("steps")
    if is_empty(raw_steps):
        raw_steps = record.get("steps")
    steps = normalize_steps(raw_steps)

    tags = string_list(enriched.get("tags"))
    source = text_or_none(record.get("source"))
    if source and source not in tags:
        tags.append(source)

    ingredients = normalize_ingredients(record.get("ingredients"))
    if not ingredients:
        raise ValueError(f"recipe has no ingredients: {title}")

    return {
        "title": title,
        "description": str(enriched.get("description") or "").strip(),
        "meal_type": meal_type,
        "category": category,
        "cuisine": text_or_none(enriched.get("cuisine")) or "russian",
        "difficulty": difficulty,
        "cooking_time_minutes": cooking_time,
        "prep_time_minutes": prep_time,
        "servings": int_or_default(enriched.get("servings"), 4),
        "calories_per_serving": number_or_none(enriched.get("calories_per_serving")),
        "protein_g": number_or_none(enriched.get("protein_g")),
        "fat_g": number_or_none(enriched.get("fat_g")),
        "carbs_g": number_or_none(enriched.get("carbs_g")),
        "source_type": "import",
        "source_url": text_or_none(record.get("source_url")),
        "is_drink": bool_or_default(enriched.get("is_drink"), False),
        "is_alcoholic": bool_or_default(enriched.get("is_alcoholic"), False),
        "suitable_for_children": bool_or_default(
            enriched.get("suitable_for_children"), True
        ),
        "suitable_for_sport": bool_or_default(enriched.get("suitable_for_sport"), False),
        "suitable_for_event": bool_or_default(enriched.get("suitable_for_event"), False),
        "diets": [],
        "tags": tags,
        "allergens": string_list(enriched.get("allergens")),
        "restrictions": string_list(enriched.get("restrictions")),
        "ingredients": ingredients,
        "steps": steps,
    }


def convert_file(input_path: Path, output_path: Path) -> int:
    recipes: list[dict[str, Any]] = []
    with input_path.open("r", encoding="utf-8") as source:
        for line_number, line in enumerate(source, start=1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise SystemExit(f"Invalid JSONL at line {line_number}: {exc}") from exc
            if not isinstance(record, dict):
                raise SystemExit(f"JSONL line {line_number} must be an object")
            try:
                recipes.append(convert_record(record))
            except ValueError as exc:
                raise SystemExit(f"JSONL line {line_number}: {exc}") from exc

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(recipes, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return len(recipes)


def main() -> int:
    args = parse_args()
    input_path = Path(args.input).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()
    if not input_path.exists():
        raise SystemExit(f"Input file not found: {input_path}")
    converted = convert_file(input_path, output_path)
    print(f"Converted {converted} recipes")
    print(f"Import JSON written to: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
