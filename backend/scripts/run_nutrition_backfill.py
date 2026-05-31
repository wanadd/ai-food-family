#!/usr/bin/env python3
"""Run an OpenAI nutrition backfill pilot without changing the database.

Dry run does not call the API:
    python backend/scripts/run_nutrition_backfill.py --dry-run
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
DEFAULT_INPUT_PATH = ROOT / "exports" / "nutrition_backfill_batch_20.json"
DEFAULT_OUTPUT_PATH = ROOT / "exports" / "nutrition_backfill_20.jsonl"
DEFAULT_FAILED_PATH = ROOT / "exports" / "nutrition_backfill_failed_20.jsonl"
DEFAULT_REPORT_PATH = ROOT / "reports" / "nutrition_backfill_20_report.md"
DEFAULT_MODEL = "gpt-4.1-mini"

REQUIRED_FIELDS = [
    "calories_per_serving",
    "protein_g",
    "fat_g",
    "carbs_g",
    "alcohol_percent",
    "confidence",
    "notes",
]
ALLOWED_CONFIDENCE = {"low", "medium", "high"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run OpenAI nutrition backfill pilot"
    )
    parser.add_argument(
        "--input",
        default=str(DEFAULT_INPUT_PATH),
        help="Path to nutrition backfill batch JSON",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT_PATH),
        help="Path to successful JSONL output",
    )
    parser.add_argument(
        "--failed-output",
        default=str(DEFAULT_FAILED_PATH),
        help="Path to failed JSONL output",
    )
    parser.add_argument(
        "--report",
        default=str(DEFAULT_REPORT_PATH),
        help="Path to Markdown report",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print prompt preview without calling OpenAI",
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
        "Ты оцениваешь КБЖУ рецептов для PlanAm. "
        "Верни строго один валидный JSON-объект без markdown. "
        "Не меняй название, ингредиенты и рецепт. "
        "Никогда не возвращай null для calories_per_serving, protein_g, fat_g, carbs_g. "
        "Если значение неизвестно, верни 0. "
        "Для неалкогольных рецептов alcohol_percent должен быть null. "
        "Для алкогольных рецептов alcohol_percent должен быть числом."
    )


def build_user_prompt(recipe: dict[str, Any]) -> str:
    payload = {
        "recipe": recipe,
        "required_fields": REQUIRED_FIELDS,
        "required_output_schema": recipe.get("required_output_schema"),
        "rules": [
            "Return calories_per_serving, protein_g, fat_g, carbs_g as numbers.",
            "Never return null for calories_per_serving, protein_g, fat_g, carbs_g.",
            "If calories or macros cannot be estimated, return 0.",
            "If is_alcoholic=false, return alcohol_percent=null.",
            "If is_alcoholic=true, estimate alcohol_percent as a number.",
            "Use confidence: low, medium, or high.",
            "Write notes in Russian, short and practical.",
        ],
    }
    return (
        "Оцени недостающие nutrition-поля для этого рецепта. "
        "Верни только JSON-объект с required_fields.\n\n"
        + json.dumps(payload, ensure_ascii=False, indent=2)
    )


def strip_json_fence(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return text.strip()


def number_or_zero(value: Any) -> float:
    if value is None:
        return 0.0
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, list):
        for item in value:
            parsed = number_or_zero(item)
            if parsed != 0:
                return parsed
        return 0.0
    text = str(value).strip().replace(",", ".")
    match = re.search(r"-?\d+(?:\.\d+)?", text)
    if not match:
        return 0.0
    try:
        return float(match.group(0))
    except ValueError:
        return 0.0


def normalize_confidence(value: Any) -> str:
    if isinstance(value, list):
        value = value[0] if value else None
    text = str(value or "").strip().lower()
    return text if text in ALLOWED_CONFIDENCE else "low"


def normalize_notes(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return "; ".join(str(item).strip() for item in value if str(item).strip())
    return str(value).strip()


def normalize_backfill(data: Any, recipe: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ValueError("response_is_not_object")

    normalized = {
        "calories_per_serving": number_or_zero(data.get("calories_per_serving")),
        "protein_g": number_or_zero(data.get("protein_g")),
        "fat_g": number_or_zero(data.get("fat_g")),
        "carbs_g": number_or_zero(data.get("carbs_g")),
        "alcohol_percent": None,
        "confidence": normalize_confidence(data.get("confidence")),
        "notes": normalize_notes(data.get("notes")),
    }

    if recipe.get("is_alcoholic") is True:
        normalized["alcohol_percent"] = number_or_zero(data.get("alcohol_percent"))

    return normalized


def validate_backfill(data: dict[str, Any], recipe: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in REQUIRED_FIELDS:
        if field not in data:
            errors.append(f"missing_{field}")
    for field in ("calories_per_serving", "protein_g", "fat_g", "carbs_g"):
        if data.get(field) is None:
            errors.append(f"null_{field}")
        if not isinstance(data.get(field), (int, float)):
            errors.append(f"non_numeric_{field}")
    if recipe.get("is_alcoholic") is True and data.get("alcohol_percent") is None:
        errors.append("missing_alcohol_percent")
    if recipe.get("is_alcoholic") is not True and data.get("alcohol_percent") is not None:
        errors.append("non_alcoholic_alcohol_percent")
    if data.get("confidence") not in ALLOWED_CONFIDENCE:
        errors.append("invalid_confidence")
    return errors


def completion_token_param(model: str, tokens: int) -> dict[str, int]:
    normalized_model = model.strip().lower()
    if normalized_model == "gpt-5" or normalized_model.startswith("gpt-5."):
        return {"max_completion_tokens": tokens}
    return {"max_tokens": tokens}


def model_generation_params(model: str) -> dict[str, float]:
    normalized_model = model.strip().lower()
    if normalized_model == "gpt-5" or normalized_model.startswith("gpt-5."):
        return {}
    return {"temperature": 0.1}


def call_openai(
    client: Any,
    model: str,
    recipe: dict[str, Any],
) -> dict[str, Any]:
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": build_system_prompt()},
            {"role": "user", "content": build_user_prompt(recipe)},
        ],
        response_format={"type": "json_object"},
        **model_generation_params(model),
        **completion_token_param(model, 900),
    )
    raw = response.choices[0].message.content or ""
    parsed = json.loads(strip_json_fence(raw))
    backfill = normalize_backfill(parsed, recipe)
    errors = validate_backfill(backfill, recipe)
    if errors:
        raise ValueError(", ".join(errors))
    return {
        "id": recipe.get("id"),
        "title": recipe.get("title"),
        "current": recipe.get("current") or {},
        "is_alcoholic": bool(recipe.get("is_alcoholic")),
        "current_alcohol_percent": recipe.get("current_alcohol_percent"),
        "backfill": backfill,
    }


def read_existing_ids(output_path: Path) -> set[str]:
    if not output_path.exists():
        return set()
    processed: set[str] = set()
    with output_path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                print(
                    f"Warning: ignoring invalid JSONL line {line_number} in {output_path}",
                    file=sys.stderr,
                )
                continue
            if isinstance(record, dict) and record.get("id") is not None:
                processed.add(str(record["id"]))
    return processed


def build_report(
    input_path: Path,
    output_path: Path,
    failed_path: Path,
    report_path: Path,
    model: str,
    total: int,
    skipped_existing: int,
    succeeded: int,
    failed: int,
    failures: list[dict[str, Any]],
    examples: list[dict[str, Any]],
) -> str:
    lines = [
        "# Nutrition Backfill Pilot Report",
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
        f"- Total recipes in batch: `{total}`",
        f"- Skipped existing: `{skipped_existing}`",
        f"- Succeeded this run: `{succeeded}`",
        f"- Failed this run: `{failed}`",
        "",
        "## Failures",
        "",
    ]
    if failures:
        for item in failures[:20]:
            recipe = item.get("recipe") or {}
            lines.append(
                f"- `#{recipe.get('id')}` {recipe.get('title')} — {item.get('error')}"
            )
            if item.get("traceback"):
                lines.append("")
                lines.append("```text")
                lines.append(str(item["traceback"]).rstrip())
                lines.append("```")
                lines.append("")
    else:
        lines.append("- `n/a`")

    lines.extend(["", "## Examples", ""])
    if examples:
        for index, example in enumerate(examples[:5], start=1):
            lines.append(f"### Example {index}")
            lines.append("")
            lines.append("```json")
            lines.append(json.dumps(example, ensure_ascii=False, indent=2))
            lines.append("```")
            lines.append("")
    else:
        lines.append("- `n/a`")

    return "\n".join(lines).rstrip() + "\n"


def print_dry_run(batch: dict[str, Any], model: str) -> None:
    recipes = batch["recipes"]
    print("DRY RUN: no OpenAI API call will be made")
    print(f"Model: {model}")
    print(f"Recipes: {len(recipes)}")
    print("\n=== SYSTEM PROMPT ===")
    print(build_system_prompt())
    print("\n=== USER PROMPT EXAMPLE ===")
    print(build_user_prompt(recipes[0]))


def run_backfill(args: argparse.Namespace) -> tuple[int, int]:
    input_path = Path(args.input).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()
    failed_path = Path(args.failed_output).expanduser().resolve()
    report_path = Path(args.report).expanduser().resolve()
    if not input_path.exists():
        raise SystemExit(f"Input file not found: {input_path}")

    batch = load_batch(input_path)
    recipes = batch["recipes"]
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
        raise SystemExit("openai package is required to run nutrition backfill") from exc

    client = OpenAI(api_key=api_key)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    failed_path.parent.mkdir(parents=True, exist_ok=True)
    processed_ids = read_existing_ids(output_path)

    succeeded = 0
    failed = 0
    skipped_existing = 0
    failures: list[dict[str, Any]] = []
    examples: list[dict[str, Any]] = []

    with output_path.open("a", encoding="utf-8", newline="\n") as ok_file, failed_path.open(
        "a", encoding="utf-8", newline="\n"
    ) as failed_file:
        for index, recipe in enumerate(recipes, start=1):
            recipe_id = str(recipe.get("id"))
            if recipe_id in processed_ids:
                skipped_existing += 1
                print(f"SKIP {recipe_id}")
                print(f"Processed {index}/{len(recipes)}")
                continue

            print(f"PROCESS {recipe_id}")
            try:
                result = call_openai(client, model, recipe)
                ok_file.write(json.dumps(result, ensure_ascii=False) + "\n")
                processed_ids.add(recipe_id)
                succeeded += 1
                if len(examples) < 5:
                    examples.append(result)
            except Exception as exc:
                failed_record = {
                    "recipe": recipe,
                    "error": f"{type(exc).__name__}: {exc}",
                    "traceback": traceback.format_exc(),
                }
                failed_file.write(json.dumps(failed_record, ensure_ascii=False) + "\n")
                failures.append(failed_record)
                failed += 1
                print(f"Failed {recipe_id}: {type(exc).__name__}", file=sys.stderr)
            print(f"Processed {index}/{len(recipes)}")

    report = build_report(
        input_path=input_path,
        output_path=output_path,
        failed_path=failed_path,
        report_path=report_path,
        model=model,
        total=len(recipes),
        skipped_existing=skipped_existing,
        succeeded=succeeded,
        failed=failed,
        failures=failures,
        examples=examples,
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")
    return succeeded, failed


def main() -> int:
    args = parse_args()
    succeeded, failed = run_backfill(args)
    if not args.dry_run:
        print(f"Succeeded: {succeeded}")
        print(f"Failed: {failed}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
