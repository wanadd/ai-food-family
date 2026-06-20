#!/usr/bin/env python3
"""Run AI enrichment for placeholder recipe steps.

This script reads placeholder recipe records, asks OpenAI for replacement
preparation steps, validates the response, and writes JSONL artifacts. It does
not write to the database.

Do not run a real AI pass unless explicitly requested:
    python backend/scripts/run_steps_enrichment.py

Prompt preview without API calls:
    python backend/scripts/run_steps_enrichment.py --dry-run
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import traceback
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT_PATH = ROOT / "exports" / "placeholder_recipe_steps_16.json"
DEFAULT_OUTPUT_PATH = ROOT / "exports" / "placeholder_recipe_steps_enriched_16.jsonl"
DEFAULT_FAILED_PATH = ROOT / "exports" / "placeholder_recipe_steps_failed_16.jsonl"
DEFAULT_REPORT_PATH = ROOT / "reports" / "placeholder_recipe_steps_enrichment_report.md"
DEFAULT_MODEL = "gpt-5-mini"
DEFAULT_FALLBACK_MODEL = "gpt-4.1"
PRIMARY_MAX_ATTEMPTS = 3
FALLBACK_MAX_ATTEMPTS = 2
PRIMARY_RETRY_DELAYS = (2, 5)

ALLOWED_CONFIDENCE = {"low", "medium", "high"}
FORBIDDEN_PHRASES = (
    "приготовьте по классическому рецепту",
    "подготовьте продукты",
    "подавайте теплым",
    "подавайте тёплым",
)
ACTION_WORDS = (
    "нареж",
    "обжар",
    "вар",
    "туш",
    "запек",
    "смеш",
    "добав",
    "перемеш",
    "довед",
    "очист",
    "измельч",
    "сформ",
    "вылож",
    "промой",
    "залей",
)
IMPORTANT_SHORT_INGREDIENTS = {"рис", "лук", "сыр", "мед", "мак"}
INGREDIENT_ALIAS_MAP = {
    "курица": ["курица", "курицу", "куриное", "куриный", "куриным", "куриное мясо"],
    "баранина": ["баранина", "баранину", "мясо"],
    "сливки": ["сливки", "сливками", "сливок"],
    "рис": ["рис", "риса"],
    "лук": ["лук", "лука", "луком"],
    "морковь": ["морковь", "моркови", "морковью"],
    "сыр": ["сыр", "сыра", "сыром"],
}
COMMON_RUSSIAN_ENDINGS = (
    "ого",
    "ему",
    "ыми",
    "ими",
    "ами",
    "ями",
    "ую",
    "юю",
    "ая",
    "яя",
    "ое",
    "ее",
    "ий",
    "ый",
    "ой",
    "ом",
    "ем",
    "ах",
    "ях",
    "ов",
    "ев",
    "ей",
    "ам",
    "ям",
    "а",
    "я",
    "у",
    "ю",
    "ы",
    "и",
    "е",
)
ALLOWED_EXTRA_INGREDIENTS = {
    "вода",
    "соль",
    "перец",
    "масло",
    "растительное масло",
    "оливковое масло",
}


class EmptyOpenAIResponse(ValueError):
    """Raised when OpenAI returns no content."""


class OpenAIResponseParseError(ValueError):
    """Raised when OpenAI content cannot be parsed as JSON."""

    def __init__(self, message: str, raw_response: str) -> None:
        super().__init__(message)
        self.raw_response = raw_response


class ValidationErrorWithRawResponse(ValueError):
    """Raised when parsed OpenAI JSON fails validation."""

    def __init__(
        self,
        message: str,
        raw_response: str,
        validation_errors: list[str],
    ) -> None:
        super().__init__(message)
        self.raw_response = raw_response
        self.validation_errors = validation_errors


def is_retryable_response_error(exc: Exception) -> bool:
    return isinstance(exc, (EmptyOpenAIResponse, OpenAIResponseParseError))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run recipe steps enrichment")
    parser.add_argument(
        "--input",
        default=str(DEFAULT_INPUT_PATH),
        help="Path to placeholder recipe steps JSON array",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT_PATH),
        help="Path to enriched JSONL output",
    )
    parser.add_argument(
        "--failed-output",
        default=str(DEFAULT_FAILED_PATH),
        help="Path to failed JSONL output",
    )
    parser.add_argument(
        "--report",
        default=str(DEFAULT_REPORT_PATH),
        help="Path to Markdown enrichment report",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="OpenAI model. Defaults to OPENAI_MODEL or gpt-5-mini.",
    )
    parser.add_argument(
        "--fallback-model",
        default=DEFAULT_FALLBACK_MODEL,
        help="Fallback model after primary retry exhaustion. Use empty string to disable.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print prompt preview without calling OpenAI",
    )
    parser.add_argument(
        "--self-test-parser",
        action="store_true",
        help="Run parser self-checks without calling OpenAI",
    )
    parser.add_argument(
        "--self-test-validation",
        action="store_true",
        help="Run ingredient validation self-checks without calling OpenAI",
    )
    parser.add_argument(
        "--self-test-confidence",
        action="store_true",
        help="Run confidence normalization self-checks without calling OpenAI",
    )
    parser.add_argument(
        "--self-test-step-length",
        action="store_true",
        help="Run step length validation self-checks without calling OpenAI",
    )
    return parser.parse_args()


def effective_model(cli_model: str | None = None) -> str:
    return (cli_model or os.environ.get("OPENAI_MODEL") or "").strip() or DEFAULT_MODEL


def load_recipes(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        recipes = json.load(handle)
    if not isinstance(recipes, list) or not recipes:
        raise SystemExit("Input must be a non-empty JSON array")
    for index, recipe in enumerate(recipes, start=1):
        if not isinstance(recipe, dict):
            raise SystemExit(f"Input record {index} must be an object")
        if recipe.get("id") is None:
            raise SystemExit(f"Input record {index} is missing id")
        if not str(recipe.get("title") or "").strip():
            raise SystemExit(f"Input record {index} is missing title")
        if not isinstance(recipe.get("ingredients"), list) or not recipe["ingredients"]:
            raise SystemExit(f"Input record {index} must contain ingredients")
    return recipes


def normalize_text(value: Any) -> str:
    text_value = str(value or "").strip().lower().replace("ё", "е")
    text_value = re.sub(r"[^0-9a-zа-я]+", " ", text_value, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", text_value).strip()


def ingredient_name(ingredient: Any) -> str:
    if isinstance(ingredient, dict):
        return str(ingredient.get("name") or "").strip()
    return str(ingredient or "").strip()


def ingredient_amount(ingredient: Any) -> str:
    if not isinstance(ingredient, dict):
        return ""
    amount = str(ingredient.get("amount") or "").strip()
    if amount:
        return amount
    quantity = str(ingredient.get("quantity") or "").strip()
    unit = str(ingredient.get("unit") or "").strip()
    return f"{quantity} {unit}".strip()


def ingredient_lines(recipe: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    for ingredient in recipe.get("ingredients") or []:
        name = ingredient_name(ingredient)
        amount = ingredient_amount(ingredient)
        lines.append(f"{name}: {amount}" if amount else name)
    return lines


def build_system_prompt() -> str:
    return (
        "Ты создаешь качественные пошаговые инструкции приготовления для PlanAm. "
        "Верни строго один валидный JSON-объект без markdown. "
        "Не меняй id, title и ingredients. Не меняй КБЖУ. "
        "Используй только ингредиенты из input; можно добавить только воду, соль, перец или масло, "
        "если это кулинарно необходимо. Пиши конкретные действия на русском языке."
    )


def build_user_prompt(recipe: dict[str, Any]) -> str:
    payload = {
        "input_recipe": {
            "id": recipe.get("id"),
            "title": recipe.get("title"),
            "description": recipe.get("description") or "",
            "ingredients": recipe.get("ingredients") or [],
            "current_steps": recipe.get("current_steps") or [],
        },
        "required_output_schema": {
            "id": "number",
            "title": "string",
            "steps": ["string"],
            "confidence": ["low", "medium", "high"],
            "notes": "string",
        },
        "rules": [
            "Return exactly one JSON object.",
            "id must equal input_recipe.id.",
            "title must equal input_recipe.title.",
            "steps must contain 5-9 strings.",
            "Every step must be concrete and practical.",
            "Do not use phrases: приготовьте по классическому рецепту, подготовьте продукты, подавайте теплым as a generic standalone step.",
            "Use real ingredients from input_recipe.ingredients.",
            "Do not add ingredients except water, salt, pepper, oil if necessary.",
            "Do not change nutrition, ingredients, or title.",
            "notes must be short and practical.",
        ],
    }
    return (
        "Замени placeholder steps на качественные инструкции приготовления. "
        "Верни только JSON-объект по required_output_schema.\n\n"
        + json.dumps(payload, ensure_ascii=False, indent=2)
    )


def strip_json_fence(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return text.strip()


def extract_json_object(text: str) -> str:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise OpenAIResponseParseError("No JSON object found in OpenAI response", text)
    return text[start : end + 1].strip()


def parse_json_response(raw_response: str) -> Any:
    if not raw_response or not raw_response.strip():
        raise EmptyOpenAIResponse("OpenAI returned an empty response")

    stripped = strip_json_fence(raw_response)
    try:
        return json.loads(stripped)
    except json.JSONDecodeError as first_exc:
        try:
            extracted = extract_json_object(stripped)
            return json.loads(extracted)
        except Exception as second_exc:
            message = (
                "Could not parse OpenAI response as JSON: "
                f"{type(first_exc).__name__}: {first_exc}; "
                f"fallback {type(second_exc).__name__}: {second_exc}"
            )
            raise OpenAIResponseParseError(message, raw_response) from second_exc


def completion_token_param(model: str, tokens: int) -> dict[str, int]:
    normalized_model = model.strip().lower()
    if normalized_model == "gpt-5" or normalized_model.startswith("gpt-5"):
        return {"max_completion_tokens": tokens}
    return {"max_tokens": tokens}


def model_generation_params(model: str) -> dict[str, float]:
    normalized_model = model.strip().lower()
    if normalized_model == "gpt-5" or normalized_model.startswith("gpt-5"):
        return {}
    return {"temperature": 0.2}


def normalize_steps(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    steps: list[str] = []
    for item in value:
        text = str(item or "").strip()
        if text:
            steps.append(re.sub(r"\s+", " ", text))
    return steps


def normalize_confidence(value: Any) -> str:
    if isinstance(value, str):
        return value.strip().lower()
    if isinstance(value, list) and len(value) == 1 and isinstance(value[0], str):
        return value[0].strip().lower()
    return ""


def normalize_response(data: Any, recipe: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ValueError("response_is_not_object")
    return {
        "id": data.get("id"),
        "title": str(data.get("title") or "").strip(),
        "steps": normalize_steps(data.get("steps")),
        "confidence": normalize_confidence(data.get("confidence")),
        "notes": str(data.get("notes") or "").strip(),
        "_input_id": recipe.get("id"),
    }


def step_has_forbidden_phrase(step: str) -> bool:
    normalized = normalize_text(step)
    for phrase in FORBIDDEN_PHRASES:
        if normalize_text(phrase) in normalized:
            return True
    return False


def step_is_generic_warm_serving(step: str) -> bool:
    normalized = normalize_text(step)
    return normalized in {"подавайте теплым", "подавайте теплым к столу"}


def ingredient_tokens(recipe: dict[str, Any]) -> set[str]:
    tokens: set[str] = set()
    for ingredient in recipe.get("ingredients") or []:
        name = normalize_text(ingredient_name(ingredient))
        tokens.update(meaningful_ingredient_terms(name))
    return tokens


def strip_russian_ending(word: str) -> str:
    if len(word) <= 3:
        return word
    for ending in COMMON_RUSSIAN_ENDINGS:
        if word.endswith(ending) and len(word) - len(ending) >= 3:
            return word[: -len(ending)]
    return word


def meaningful_ingredient_terms(normalized_name: str) -> set[str]:
    terms: set[str] = set()
    if not normalized_name:
        return terms

    if normalized_name in INGREDIENT_ALIAS_MAP:
        terms.update(normalize_text(alias) for alias in INGREDIENT_ALIAS_MAP[normalized_name])

    for canonical, aliases in INGREDIENT_ALIAS_MAP.items():
        if normalized_name == canonical or normalized_name in {
            normalize_text(alias) for alias in aliases
        }:
            terms.update(normalize_text(alias) for alias in aliases)
            terms.add(canonical)

    for token in normalized_name.split():
        if len(token) >= 4 or token in IMPORTANT_SHORT_INGREDIENTS:
            terms.add(token)
            stem = strip_russian_ending(token)
            if len(stem) >= 3:
                terms.add(stem)

    return {term for term in terms if term}


def steps_mention_meaningful_ingredient(recipe: dict[str, Any], steps: list[str]) -> bool:
    normalized_steps = normalize_text(" ".join(steps))
    terms = ingredient_tokens(recipe)
    return bool(terms) and any(term in normalized_steps for term in terms)


def step_has_meaningful_ingredient(recipe: dict[str, Any], step: str) -> bool:
    normalized_step = normalize_text(step)
    terms = ingredient_tokens(recipe)
    return bool(terms) and any(term in normalized_step for term in terms)


def step_has_cooking_verb(step: str) -> bool:
    normalized_step = normalize_text(step)
    return any(action in normalized_step for action in ACTION_WORDS)


def step_length_is_acceptable(recipe: dict[str, Any], step: str) -> bool:
    if len(step) >= 20:
        return True
    if len(step) < 15:
        return False
    return step_has_cooking_verb(step) and step_has_meaningful_ingredient(recipe, step)


def validate_enriched(data: dict[str, Any], recipe: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    try:
        response_id = int(data.get("id"))
        input_id = int(recipe.get("id"))
    except (TypeError, ValueError):
        errors.append("invalid_id")
    else:
        if response_id != input_id:
            errors.append("id_mismatch")

    if data.get("title") != str(recipe.get("title") or "").strip():
        errors.append("title_mismatch")

    steps = data.get("steps")
    if not isinstance(steps, list):
        errors.append("steps_is_not_list")
        steps = []
    if not 5 <= len(steps) <= 9:
        errors.append("steps_count_not_5_to_9")

    for index, step in enumerate(steps, start=1):
        if not step_length_is_acceptable(recipe, step):
            errors.append(f"step_{index}_too_short")
        if step_has_forbidden_phrase(step):
            errors.append(f"step_{index}_forbidden_phrase")
        if step_is_generic_warm_serving(step):
            errors.append(f"step_{index}_generic_warm_serving")

    normalized_all_steps = normalize_text(" ".join(steps))
    if not any(action in normalized_all_steps for action in ACTION_WORDS):
        errors.append("no_concrete_action_words")

    if ingredient_tokens(recipe) and not steps_mention_meaningful_ingredient(recipe, steps):
        errors.append("no_input_ingredients_mentioned")

    confidence = data.get("confidence")
    if confidence not in ALLOWED_CONFIDENCE:
        errors.append("invalid_confidence")

    if not isinstance(data.get("notes"), str):
        errors.append("notes_is_not_string")

    return errors


def call_openai(client: Any, model: str, recipe: dict[str, Any]) -> dict[str, Any]:
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": build_system_prompt()},
            {"role": "user", "content": build_user_prompt(recipe)},
        ],
        response_format={"type": "json_object"},
        **model_generation_params(model),
        **completion_token_param(model, 1600),
    )
    raw = response.choices[0].message.content or ""
    parsed = parse_json_response(raw)
    enriched = normalize_response(parsed, recipe)
    errors = validate_enriched(enriched, recipe)
    if errors:
        raise ValidationErrorWithRawResponse(", ".join(errors), raw, errors)
    return {
        "id": int(enriched["id"]),
        "title": enriched["title"],
        "steps": enriched["steps"],
        "confidence": enriched["confidence"],
        "notes": enriched["notes"],
    }


def call_openai_with_retries(
    client: Any,
    model: str,
    fallback_model: str | None,
    recipe: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    recipe_id = str(recipe.get("id"))
    title = str(recipe.get("title") or "").strip()
    retries = 0
    fallback_used = False
    primary_retryable_exhausted = False
    last_exc: Exception | None = None

    for attempt in range(1, PRIMARY_MAX_ATTEMPTS + 1):
        try:
            result = call_openai(client, model, recipe)
            return result, {
                "model": model,
                "attempts": attempt,
                "retries": retries,
                "fallback_used": False,
            }
        except Exception as exc:
            last_exc = exc
            if not is_retryable_response_error(exc):
                break
            if attempt == PRIMARY_MAX_ATTEMPTS:
                primary_retryable_exhausted = True
                break
            retries += 1
            next_attempt = attempt + 1
            print(
                f"RETRY {recipe_id} {title} attempt {next_attempt}/{PRIMARY_MAX_ATTEMPTS} "
                f"reason={type(exc).__name__}: {exc}"
            )
            time.sleep(PRIMARY_RETRY_DELAYS[attempt - 1])

    fallback = (fallback_model or "").strip()
    if fallback and primary_retryable_exhausted:
        fallback_used = True
        for attempt in range(1, FALLBACK_MAX_ATTEMPTS + 1):
            try:
                result = call_openai(client, fallback, recipe)
                return result, {
                    "model": fallback,
                    "attempts": attempt,
                    "retries": retries,
                    "fallback_used": True,
                }
            except Exception as exc:
                last_exc = exc
                if not is_retryable_response_error(exc) or attempt == FALLBACK_MAX_ATTEMPTS:
                    break
                retries += 1
                next_attempt = attempt + 1
                print(
                    f"RETRY {recipe_id} {title} attempt {next_attempt}/{FALLBACK_MAX_ATTEMPTS} "
                    f"reason={type(exc).__name__}: {exc}"
                )
                time.sleep(PRIMARY_RETRY_DELAYS[attempt - 1])

    if last_exc is None:
        raise RuntimeError("OpenAI call failed without exception")
    setattr(last_exc, "retries", retries)
    setattr(last_exc, "fallback_used", fallback_used)
    raise last_exc


def self_test_parser() -> int:
    cases = [
        ('{"id":1,"steps":[]}', True),
        ('```json\n{"id":1,"steps":[]}\n```', True),
        ('Вот JSON:\n{"id":1,"steps":[]}', True),
        ('{"id":1,"steps":[]}\nГотово', True),
        ("", False),
    ]
    failed = 0
    for index, (raw, should_pass) in enumerate(cases, start=1):
        try:
            parsed = parse_json_response(raw)
            ok = isinstance(parsed, dict) and parsed.get("id") == 1 and parsed.get("steps") == []
            if not should_pass or not ok:
                failed += 1
                print(f"FAIL parser case {index}: unexpected success {parsed!r}")
            else:
                print(f"PASS parser case {index}")
        except EmptyOpenAIResponse:
            if should_pass:
                failed += 1
                print(f"FAIL parser case {index}: unexpected EmptyOpenAIResponse")
            else:
                print(f"PASS parser case {index}: EmptyOpenAIResponse")
        except Exception as exc:
            failed += 1
            print(f"FAIL parser case {index}: {type(exc).__name__}: {exc}")
    if failed:
        print(f"Parser self-test failed: {failed}")
        return 1
    print("Parser self-test passed")
    return 0


def self_test_validation() -> int:
    cases = [
        ("Рис", "Промойте рис под холодной водой."),
        ("Курица", "Нарежьте курицу небольшими кусочками."),
        ("Сливки", "Добавьте сливками соус и перемешайте."),
        ("Баранина", "Обжарьте мясо на среднем огне."),
        ("Картофель", "Очистите картофель и нарежьте кубиками."),
    ]
    failed = 0
    for index, (ingredient, step) in enumerate(cases, start=1):
        recipe = {
            "id": index,
            "title": f"Test {index}",
            "ingredients": [{"name": ingredient, "amount": "100 г"}],
        }
        ok = steps_mention_meaningful_ingredient(recipe, [step])
        if ok:
            print(f"PASS validation case {index}: {ingredient}")
        else:
            failed += 1
            print(f"FAIL validation case {index}: {ingredient}")
    if failed:
        print(f"Validation self-test failed: {failed}")
        return 1
    print("Validation self-test passed")
    return 0


def self_test_confidence() -> int:
    cases = [
        ("high", True, "high"),
        (" High ", True, "high"),
        (["high"], True, "high"),
        (["medium"], True, "medium"),
        ([], False, ""),
        (["high", "medium"], False, ""),
        ("very_high", False, "very_high"),
    ]
    failed = 0
    for index, (value, should_pass, expected) in enumerate(cases, start=1):
        normalized = normalize_confidence(value)
        passed = normalized in ALLOWED_CONFIDENCE
        if passed == should_pass and normalized == expected:
            print(f"PASS confidence case {index}: {value!r} -> {normalized!r}")
            continue
        failed += 1
        print(
            f"FAIL confidence case {index}: value={value!r} "
            f"normalized={normalized!r} expected={expected!r} pass={passed}"
        )
    if failed:
        print(f"Confidence self-test failed: {failed}")
        return 1
    print("Confidence self-test passed")
    return 0


def self_test_step_length() -> int:
    cases = [
        ("Мелко нарежьте лук.", [{"name": "Лук", "amount": "1 шт"}], True),
        ("Подавайте.", [{"name": "Лук", "amount": "1 шт"}], False),
        ("Нарежьте.", [{"name": "Лук", "amount": "1 шт"}], False),
        ("Лук.", [{"name": "Лук", "amount": "1 шт"}], False),
        (
            "Нарежьте лук мелкими кубиками и переложите в миску.",
            [{"name": "Лук", "amount": "1 шт"}],
            True,
        ),
    ]
    failed = 0
    for index, (step, ingredients, should_pass) in enumerate(cases, start=1):
        recipe = {"id": index, "title": f"Test {index}", "ingredients": ingredients}
        passed = step_length_is_acceptable(recipe, step)
        if passed == should_pass:
            print(f"PASS step length case {index}: {step!r}")
            continue
        failed += 1
        print(
            f"FAIL step length case {index}: step={step!r} "
            f"length={len(step)} pass={passed} expected={should_pass}"
        )
    if failed:
        print(f"Step length self-test failed: {failed}")
        return 1
    print("Step length self-test passed")
    return 0


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
    fallback_model: str | None,
    total: int,
    skipped_existing: int,
    succeeded: int,
    failed: int,
    retries_count: int,
    fallback_used_count: int,
    failures: list[dict[str, Any]],
    examples: list[dict[str, Any]],
) -> str:
    lines = [
        "# Placeholder Recipe Steps Enrichment Report",
        "",
        "Scope: AI enrichment output only. No database changes, recipe updates, nutrition changes, or ingredient changes were performed.",
        "",
        "## Source",
        "",
        f"- Input: `{input_path}`",
        f"- Output: `{output_path}`",
        f"- Failed output: `{failed_path}`",
        f"- Report: `{report_path}`",
        f"- Model: `{model}`",
        f"- Fallback model: `{fallback_model or 'disabled'}`",
        "",
        "## Summary",
        "",
        f"- Total recipes in input: `{total}`",
        f"- Skipped existing: `{skipped_existing}`",
        f"- Succeeded this run: `{succeeded}`",
        f"- Failed this run: `{failed}`",
        f"- Retries count: `{retries_count}`",
        f"- Fallback used count: `{fallback_used_count}`",
        f"- Final succeeded: `{succeeded}`",
        f"- Final failed: `{failed}`",
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
                lines.extend(["", "```text", str(item["traceback"]).rstrip(), "```", ""])
    else:
        lines.append("- `n/a`")

    lines.extend(["", "## Examples", ""])
    if examples:
        for index, example in enumerate(examples[:5], start=1):
            lines.extend(
                [
                    f"### Example {index}",
                    "",
                    "```json",
                    json.dumps(example, ensure_ascii=False, indent=2),
                    "```",
                    "",
                ]
            )
    else:
        lines.append("- `n/a`")

    return "\n".join(lines).rstrip() + "\n"


def print_dry_run(recipes: list[dict[str, Any]], model: str) -> None:
    print("DRY RUN: no OpenAI API call will be made")
    print(f"Model: {model}")
    print(f"Recipes: {len(recipes)}")
    print("\n=== SYSTEM PROMPT ===")
    print(build_system_prompt())
    print("\n=== USER PROMPT EXAMPLE ===")
    print(build_user_prompt(recipes[0]))


def run_enrichment(args: argparse.Namespace) -> tuple[int, int]:
    input_path = Path(args.input).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()
    failed_path = Path(args.failed_output).expanduser().resolve()
    report_path = Path(args.report).expanduser().resolve()
    if not input_path.exists():
        raise SystemExit(f"Input file not found: {input_path}")

    recipes = load_recipes(input_path)
    model = effective_model(args.model)
    fallback_model = (args.fallback_model or "").strip() or None
    if args.dry_run:
        print_dry_run(recipes, model)
        return 0, 0

    api_key = (os.environ.get("OPENAI_API_KEY") or "").strip()
    if not api_key:
        raise SystemExit("OPENAI_API_KEY is required unless --dry-run is used")

    try:
        from openai import OpenAI
    except ImportError as exc:
        raise SystemExit("openai package is required to run steps enrichment") from exc

    client = OpenAI(api_key=api_key)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    failed_path.parent.mkdir(parents=True, exist_ok=True)
    processed_ids = read_existing_ids(output_path)

    succeeded = 0
    failed = 0
    skipped_existing = 0
    retries_count = 0
    fallback_used_count = 0
    failures: list[dict[str, Any]] = []
    examples: list[dict[str, Any]] = []

    with output_path.open("a", encoding="utf-8", newline="\n") as ok_file, failed_path.open(
        "a", encoding="utf-8", newline="\n"
    ) as failed_file:
        for index, recipe in enumerate(recipes, start=1):
            recipe_id = str(recipe.get("id"))
            title = str(recipe.get("title") or "").strip()
            if recipe_id in processed_ids:
                skipped_existing += 1
                print(f"SKIP {recipe_id} {title}")
                print(f"Processed {index}/{len(recipes)}")
                continue

            print(f"PROCESS {recipe_id} {title}")
            try:
                result, call_meta = call_openai_with_retries(
                    client,
                    model,
                    fallback_model,
                    recipe,
                )
                ok_file.write(json.dumps(result, ensure_ascii=False) + "\n")
                ok_file.flush()
                processed_ids.add(recipe_id)
                succeeded += 1
                retries_count += int(call_meta.get("retries") or 0)
                if call_meta.get("fallback_used"):
                    fallback_used_count += 1
                if len(examples) < 5:
                    examples.append(result)
            except Exception as exc:
                retries_count += int(getattr(exc, "retries", 0) or 0)
                if getattr(exc, "fallback_used", False):
                    fallback_used_count += 1
                raw_response = getattr(exc, "raw_response", "")
                failed_record = {
                    "model": model,
                    "fallback_model": fallback_model,
                    "retries": int(getattr(exc, "retries", 0) or 0),
                    "fallback_used": bool(getattr(exc, "fallback_used", False)),
                    "validation_errors": getattr(exc, "validation_errors", []),
                    "recipe_id": recipe.get("id"),
                    "recipe_title": recipe.get("title"),
                    "raw_response": raw_response,
                    "raw_response_preview": raw_response[:2000],
                    "recipe": recipe,
                    "error": f"{type(exc).__name__}: {exc}",
                    "traceback": traceback.format_exc(),
                }
                failed_file.write(json.dumps(failed_record, ensure_ascii=False) + "\n")
                failed_file.flush()
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
        fallback_model=fallback_model,
        total=len(recipes),
        skipped_existing=skipped_existing,
        succeeded=succeeded,
        failed=failed,
        retries_count=retries_count,
        fallback_used_count=fallback_used_count,
        failures=failures,
        examples=examples,
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")
    return succeeded, failed


def main() -> int:
    args = parse_args()
    if args.self_test_parser:
        return self_test_parser()
    if args.self_test_validation:
        return self_test_validation()
    if args.self_test_confidence:
        return self_test_confidence()
    if args.self_test_step_length:
        return self_test_step_length()
    succeeded, failed = run_enrichment(args)
    if not args.dry_run:
        print(f"Succeeded: {succeeded}")
        print(f"Failed: {failed}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
