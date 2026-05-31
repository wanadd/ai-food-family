#!/usr/bin/env python3
"""Run a 10-recipe OpenAI enrichment pilot.

Dry run does not call the API:
    python backend/scripts/run_enrichment_pilot.py --input exports/povarenok_enrichment_batch_10.json --dry-run
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import traceback
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT_PATH = ROOT / "exports" / "povarenok_enrichment_batch_10.json"
DEFAULT_OUTPUT_PATH = ROOT / "exports" / "povarenok_enriched_10.jsonl"
DEFAULT_FAILED_PATH = ROOT / "exports" / "povarenok_enrichment_failed_10.jsonl"
DEFAULT_REPORT_PATH = ROOT / "reports" / "enrichment_pilot_report.md"
DEFAULT_MODEL = "gpt-4.1-mini"
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

REQUIRED_FIELDS = [
    "title",
    "description",
    "meal_type",
    "category",
    "cuisine",
    "difficulty",
    "prep_time_minutes",
    "cooking_time_minutes",
    "servings",
    "steps",
    "tags",
    "allergens",
    "restrictions",
    "suitable_for_children",
    "suitable_for_sport",
    "suitable_for_event",
    "is_drink",
    "is_alcoholic",
    "calories_per_serving",
    "protein_g",
    "fat_g",
    "carbs_g",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run OpenAI enrichment pilot for Povarenok recipes"
    )
    parser.add_argument(
        "--input",
        default=str(DEFAULT_INPUT_PATH),
        help="Path to enrichment batch JSON",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT_PATH),
        help="Path to enriched JSONL output",
    )
    parser.add_argument(
        "--failed-output",
        default=str(DEFAULT_FAILED_PATH),
        help="Path to failed records JSONL",
    )
    parser.add_argument(
        "--report",
        default=str(DEFAULT_REPORT_PATH),
        help="Path to Markdown pilot report",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print prompts without calling OpenAI",
    )
    return parser.parse_args()


def effective_model() -> str:
    return (os.environ.get("OPENAI_MODEL") or "").strip() or DEFAULT_MODEL


def load_batch(input_path: Path) -> dict[str, Any]:
    with input_path.open("r", encoding="utf-8") as handle:
        batch = json.load(handle)
    if not isinstance(batch.get("recipes"), list) or not batch["recipes"]:
        raise SystemExit("Input batch must contain a non-empty recipes list")
    return batch


def build_system_prompt() -> str:
    return (
        "Ты обогащаешь русскоязычные рецепты для PlanAm. "
        "Верни строго один валидный JSON-объект без markdown. "
        "Не добавляй ингредиенты. Если значение нельзя надежно оценить, используй null. "
        "steps должны быть практичными шагами приготовления на русском языке."
    )


def build_user_prompt(
    recipe: dict[str, Any],
    expected_output_schema: dict[str, Any],
) -> str:
    payload = {
        "recipe": recipe,
        "required_fields": REQUIRED_FIELDS,
        "allowed_values": {
            "meal_type": ["breakfast", "lunch", "dinner", "snack"],
            "category": [
                "soup",
                "main",
                "salad",
                "dessert",
                "quick",
                "kids",
                "drink",
                "event",
                "bbq",
            ],
            "difficulty": ["easy", "medium", "hard"],
        },
        "expected_output_schema": expected_output_schema,
    }
    return (
        "Обогати рецепт и верни JSON-объект с полями из required_fields. "
        "Не возвращай исходный wrapper, только enriched recipe object.\n\n"
        + json.dumps(payload, ensure_ascii=False, indent=2)
    )


def strip_json_fence(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return text.strip()


def flatten_to_strings(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if isinstance(value, list):
        items: list[str] = []
        for item in value:
            items.extend(flatten_to_strings(item))
        return items
    text = str(value).strip()
    return [text] if text else []


def normalize_list_fields(data: Any) -> None:
    if not isinstance(data, dict):
        return
    for field in ("tags", "allergens", "restrictions", "steps"):
        values = flatten_to_strings(data.get(field))
        data[field] = list(dict.fromkeys(values))


def normalize_scalar_field(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        text = value.strip()
        return text if text else None
    if isinstance(value, list):
        for item in value:
            normalized = normalize_scalar_field(item)
            if normalized:
                return normalized
        return None
    text = str(value).strip()
    return text if text else None


def normalize_scalar_fields(data: Any) -> None:
    if not isinstance(data, dict):
        return

    for field in ("meal_type", "category", "difficulty", "cuisine", "title", "description"):
        data[field] = normalize_scalar_field(data.get(field))

    if data.get("meal_type") not in ALLOWED_MEAL_TYPES:
        data["meal_type"] = "lunch"
    if data.get("category") not in ALLOWED_CATEGORIES:
        data["category"] = "main"
    if data.get("difficulty") not in ALLOWED_DIFFICULTIES:
        data["difficulty"] = "easy"


def normalize_enriched_response(data: Any) -> None:
    normalize_list_fields(data)
    normalize_scalar_fields(data)


def validate_enriched(data: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["response_is_not_object"]
    for field in REQUIRED_FIELDS:
        if field not in data:
            errors.append(f"missing_{field}")
    if data.get("meal_type") not in ALLOWED_MEAL_TYPES:
        errors.append("invalid_meal_type")
    if data.get("category") not in ALLOWED_CATEGORIES:
        errors.append("invalid_category")
    if data.get("difficulty") not in ALLOWED_DIFFICULTIES:
        errors.append("invalid_difficulty")
    if not isinstance(data.get("steps"), list) or not data.get("steps"):
        errors.append("empty_steps")
    return errors


def enrich_recipe(
    client: Any,
    model: str,
    recipe: dict[str, Any],
    expected_output_schema: dict[str, Any],
) -> dict[str, Any]:
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": build_system_prompt()},
            {
                "role": "user",
                "content": build_user_prompt(recipe, expected_output_schema),
            },
        ],
        temperature=0.2,
        max_tokens=1800,
        response_format={"type": "json_object"},
    )
    raw = response.choices[0].message.content or ""
    data = json.loads(strip_json_fence(raw))
    normalize_enriched_response(data)
    errors = validate_enriched(data)
    if errors:
        raise ValueError(", ".join(errors))
    return {
        "id": recipe.get("id"),
        "source": recipe.get("source"),
        "source_url": recipe.get("source_url"),
        "raw_title": recipe.get("title"),
        "ingredients": recipe.get("ingredients") or [],
        "enriched": data,
    }


def build_report(
    input_path: Path,
    output_path: Path,
    failed_path: Path,
    report_path: Path,
    model: str,
    total: int,
    succeeded: int,
    failed: int,
    failures: list[dict[str, Any]],
) -> str:
    lines = [
        "# Enrichment Pilot Report",
        "",
        "## Source",
        "",
        f"- Input: `{input_path}`",
        f"- Output: `{output_path}`",
        f"- Failed output: `{failed_path}`",
        f"- Report: `{report_path}`",
        f"- Model: `{model}`",
        "",
        "## Summary",
        "",
        f"- Total recipes: `{total}`",
        f"- Succeeded: `{succeeded}`",
        f"- Failed: `{failed}`",
        "",
        "## Failures",
        "",
    ]
    if failures:
        for item in failures:
            recipe = item.get("recipe") or {}
            lines.append(
                f"- {recipe.get('id')}: {recipe.get('title')} — {item.get('error')}"
            )
            if item.get("traceback"):
                lines.append("")
                lines.append("```text")
                lines.append(str(item["traceback"]).rstrip())
                lines.append("```")
                lines.append("")
    else:
        lines.append("- `n/a`")
    return "\n".join(lines).rstrip() + "\n"


def print_dry_run(batch: dict[str, Any], model: str) -> None:
    recipes = batch["recipes"]
    schema = batch.get("expected_output_schema") or {}
    print(f"DRY RUN: no OpenAI API call will be made")
    print(f"Model: {model}")
    print(f"Recipes: {len(recipes)}")
    print("\n=== SYSTEM PROMPT ===")
    print(build_system_prompt())
    print("\n=== USER PROMPT EXAMPLE: recipe 1 ===")
    print(build_user_prompt(recipes[0], schema))


def run_pilot(args: argparse.Namespace) -> tuple[int, int]:
    input_path = Path(args.input).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()
    failed_path = Path(args.failed_output).expanduser().resolve()
    report_path = Path(args.report).expanduser().resolve()
    if not input_path.exists():
        raise SystemExit(f"Input file not found: {input_path}")

    batch = load_batch(input_path)
    model = effective_model()
    if args.dry_run:
        print_dry_run(batch, model)
        return 0, 0

    api_key = (os.environ.get("OPENAI_API_KEY") or "").strip()
    if not api_key:
        raise SystemExit("OPENAI_API_KEY is required unless --dry-run is used")

    try:
        from openai import OpenAI
    except ImportError as exc:
        raise SystemExit("openai package is required to run enrichment") from exc

    client = OpenAI(api_key=api_key)
    recipes = batch["recipes"]
    schema = batch.get("expected_output_schema") or {}
    output_path.parent.mkdir(parents=True, exist_ok=True)
    failed_path.parent.mkdir(parents=True, exist_ok=True)

    succeeded = 0
    failed = 0
    failures: list[dict[str, Any]] = []
    with output_path.open("w", encoding="utf-8", newline="\n") as ok_file, failed_path.open(
        "w", encoding="utf-8", newline="\n"
    ) as failed_file:
        for recipe in recipes:
            try:
                enriched = enrich_recipe(client, model, recipe, schema)
                ok_file.write(json.dumps(enriched, ensure_ascii=False) + "\n")
                succeeded += 1
            except Exception as exc:
                failed_record = {
                    "recipe": recipe,
                    "error": f"{type(exc).__name__}: {exc}",
                    "traceback": traceback.format_exc(),
                }
                failed_file.write(json.dumps(failed_record, ensure_ascii=False) + "\n")
                failures.append(failed_record)
                failed += 1
                print(
                    f"Failed {recipe.get('id')}: {type(exc).__name__}",
                    file=sys.stderr,
                )

    report = build_report(
        input_path=input_path,
        output_path=output_path,
        failed_path=failed_path,
        report_path=report_path,
        model=model,
        total=len(recipes),
        succeeded=succeeded,
        failed=failed,
        failures=failures,
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")
    return succeeded, failed


def main() -> int:
    args = parse_args()
    succeeded, failed = run_pilot(args)
    if not args.dry_run:
        print(f"Enriched: {succeeded}")
        print(f"Failed: {failed}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
