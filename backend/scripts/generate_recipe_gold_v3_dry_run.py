#!/usr/bin/env python3
"""Stage F: generate original Gold V3 recipes dry-run (no DB import, no photos)."""

from __future__ import annotations

import argparse
import asyncio
import json
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
API_ROOT = ROOT / "apps" / "api"
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.recipes.recipe_gold_v3_postprocess import postprocess_generated_recipe  # noqa: E402
from app.recipes.recipe_gold_v3_prompt_builder import (  # noqa: E402
    build_recipe_gold_v3_generation_messages,
    build_target_profile_from_signal,
    feedback_codes_for_retry,
    sanitize_signal_for_prompt,
)
from app.recipes.recipe_gold_v3_schema import PRODUCTION_READY_MIN_SCORE, SCHEMA_VERSION  # noqa: E402
from app.nutrition.restrictions_catalog import get_restriction_definition  # noqa: E402
from app.recipes.recipe_gold_v3_validation import (  # noqa: E402
    ValidationResult,
    validate_recipe_gold_v3,
)
from app.services import ai_client  # noqa: E402
from app.services.ai_errors import AiUnavailableError  # noqa: E402

DEFAULT_SIGNALS = ROOT / "exports" / "povarenok_culinary_signals_v3_100.jsonl"
DEFAULT_OUTPUT = ROOT / "exports" / "recipe_gold_v3_generated_10_dry_run.jsonl"
DEFAULT_REPORT = ROOT / "reports" / "recipe_gold_v3_stage_f_generation_report.md"

ESTIMATED_COST_PER_REQUEST_USD = 0.05
MODEL_ESTIMATED_COST_USD: dict[str, float] = {
    "gpt-4o-mini": 0.05,
    "gpt-4.1": 0.10,
    "gpt-4.1-mini": 0.08,
    "gpt-4o": 0.12,
}
FORBIDDEN_RECIPE_KEYS = frozenset(
    {
        "source_url",
        "original_title",
        "original_steps",
        "copied_source_text",
    }
)


@dataclass
class GenerationStats:
    attempted: int = 0
    valid: int = 0
    invalid: int = 0
    retries_used: int = 0
    api_calls: int = 0
    estimated_cost_usd: float = 0.0
    titles: list[str] = field(default_factory=list)
    scores: list[int] = field(default_factory=list)
    error_codes: Counter[str] = field(default_factory=Counter)
    warning_codes: Counter[str] = field(default_factory=Counter)
    meal_types: Counter[str] = field(default_factory=Counter)
    categories: Counter[str] = field(default_factory=Counter)
    restriction_keys: Counter[str] = field(default_factory=Counter)
    allergen_keys: Counter[str] = field(default_factory=Counter)
    failed: list[dict[str, Any]] = field(default_factory=list)
    valid_recipes: list[dict[str, Any]] = field(default_factory=list)
    originality_violations: list[str] = field(default_factory=list)
    mode: str = "api"
    model: str = ""
    low_score_retries: int = 0
    real_api_run: bool = False


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Gold V3 recipe generation dry-run")
    parser.add_argument("--signals", type=Path, default=DEFAULT_SIGNALS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--dry-run", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--max-cost-usd", type=float, default=1.0)
    parser.add_argument("--model", type=str, default=None, help="OpenAI model override (e.g. gpt-4o-mini, gpt-4.1)")
    parser.add_argument("--temperature", type=float, default=0.7)
    parser.add_argument("--sample-start", type=int, default=0)
    parser.add_argument("--retry-invalid", type=int, default=1)
    parser.add_argument(
        "--retry-below-score",
        type=int,
        default=PRODUCTION_READY_MIN_SCORE,
        help="Retry when valid but validation score is below this threshold",
    )
    parser.add_argument(
        "--no-api",
        action="store_true",
        help="Deterministic smoke recipes for tests (no OpenAI)",
    )
    return parser.parse_args()


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def _diversity_key(signal: dict[str, Any]) -> tuple:
    return (
        signal.get("dish_family", ""),
        tuple(signal.get("meal_type_hints") or []),
        tuple(signal.get("main_product_groups") or []),
    )


def select_diverse_signals(
    signals: list[dict[str, Any]],
    limit: int,
    *,
    sample_start: int = 0,
    prefer_non_avoid: bool = True,
) -> list[dict[str, Any]]:
    pool = list(signals)
    if prefer_non_avoid:
        good = [s for s in pool if not s.get("avoid_for_planam")]
        if len(good) >= limit:
            pool = good
    pool = pool[sample_start:]
    pool.sort(
        key=lambda s: (
            0 if s.get("family_fit") == "high" else 1 if s.get("family_fit") == "medium" else 2,
            bool(s.get("avoid_for_planam")),
        )
    )
    selected: list[dict[str, Any]] = []
    seen_keys: set[tuple] = set()
    for signal in pool:
        key = _diversity_key(signal)
        if key in seen_keys and len(selected) < limit:
            continue
        selected.append(signal)
        seen_keys.add(key)
        if len(selected) >= limit:
            break
    if len(selected) < limit:
        for signal in pool:
            if signal not in selected:
                selected.append(signal)
            if len(selected) >= limit:
                break
    return selected[:limit]


def estimated_cost_per_request(model: str | None) -> float:
    if model and model in MODEL_ESTIMATED_COST_USD:
        return MODEL_ESTIMATED_COST_USD[model]
    return ESTIMATED_COST_PER_REQUEST_USD


def check_cost_guard(
    limit: int,
    retry_invalid: int,
    max_cost_usd: float,
    *,
    model: str | None = None,
) -> tuple[bool, float]:
    estimated_requests = limit * (1 + retry_invalid)
    per_request = estimated_cost_per_request(model)
    estimated = estimated_requests * per_request
    return estimated <= max_cost_usd, estimated


def originality_post_check(recipe: dict[str, Any]) -> list[str]:
    violations: list[str] = []
    for key in FORBIDDEN_RECIPE_KEYS:
        if key in recipe:
            violations.append(f"forbidden_field:{key}")
    originality = recipe.get("originality") or {}
    for flag in (
        "is_original_planam_recipe",
        "no_source_title_used",
        "no_source_steps_used",
        "no_direct_copy",
    ):
        if originality.get(flag) is not True:
            violations.append(f"originality_flag_false:{flag}")
    if not recipe.get("source_signal_ids"):
        violations.append("missing_source_signal_ids")
    title = str(recipe.get("title") or "")
    if re_search_url(title):
        violations.append("title_contains_url")
    return violations


def re_search_url(text: str) -> bool:
    lower = text.lower()
    return "http" in lower or "povarenok" in lower


def enrich_recipe_metadata(recipe: dict[str, Any], signal: dict[str, Any]) -> dict[str, Any]:
    out = dict(recipe)
    out["schema_version"] = SCHEMA_VERSION
    out["status"] = "gold"
    out["source_type"] = "generated_original"
    out["source_signal_ids"] = [signal.get("signal_id", "unknown")]
    out.setdefault(
        "originality",
        {
            "is_original_planam_recipe": True,
            "no_source_title_used": True,
            "no_source_steps_used": True,
            "no_direct_copy": True,
            "source_similarity_risk": "low",
            "originality_notes": "PLANAM Stage F generated original",
        },
    )
    out["tags"] = sorted(
        set(out.get("tags") or []) | {"gold_v3", "recipe_schema_v3", "status:gold"}
    )
    quality = dict(out.get("quality") or {})
    quality.setdefault("flags", [])
    quality.setdefault("warnings", [])
    out["quality"] = quality
    return out


def _ing(name: str, *, category: str, amount: float = 100, unit: str = "г") -> dict:
    disp = f"{int(amount)} {unit}" if unit != "шт" else f"{int(amount)} шт"
    return {
        "name": name,
        "amount": amount,
        "unit": unit,
        "display_amount": disp,
        "category": category,
        "optional": False,
        "shopping_name": name,
    }


def _step(n: int, text: str) -> dict:
    return {"step_number": n, "text": text}


def _restriction_keys_from_signal(signal: dict[str, Any]) -> list[str]:
    hints = signal.get("restriction_hints") or []
    keys = [h for h in hints if get_restriction_definition(h)]
    if not keys:
        keys = ["no_pork", "no_alcohol"]
    return sorted(set(keys))


def _is_vegan_signal(signal: dict[str, Any]) -> bool:
    return "vegan" in (signal.get("restriction_hints") or [])


def _no_dairy_signal(signal: dict[str, Any]) -> bool:
    hints = signal.get("restriction_hints") or []
    return _is_vegan_signal(signal) or any(h in hints for h in ("no_milk", "lactose_free"))


def _ingredients_and_title_for_signal(
    signal: dict[str, Any], dish: str, seq: int
) -> tuple[list[dict[str, Any]], str]:
    groups = signal.get("main_product_groups") or ["овощи"]
    vegan = _is_vegan_signal(signal)
    no_dairy = _no_dairy_signal(signal)

    salad_ings = [
        _ing("огурец", category="овощи", amount=2, unit="шт"),
        _ing("помидор", category="овощи", amount=2, unit="шт"),
        _ing("перец болгарский", category="овощи", amount=1, unit="шт"),
        _ing("оливковое масло", category="масла/соусы", amount=30),
    ]

    if vegan:
        by_dish = {
            "котлеты": (
                [
                    _ing("чечевица", category="бобовые", amount=200),
                    _ing("овсяные хлопья", category="крупы", amount=80),
                    _ing("морковь", category="овощи", amount=1, unit="шт"),
                    _ing("лук репчатый", category="овощи", amount=1, unit="шт"),
                ],
                f"Котлеты из чечевицы #{seq}",
            ),
            "запеканка": (
                [
                    _ing("картофель", category="овощи", amount=4, unit="шт"),
                    _ing("кабачок", category="овощи", amount=1, unit="шт"),
                    _ing("морковь", category="овощи", amount=1, unit="шт"),
                    _ing("помидор", category="овощи", amount=2, unit="шт"),
                ],
                f"Овощная запеканка #{seq}",
            ),
            "суп": (
                [
                    _ing("картофель", category="овощи", amount=2, unit="шт"),
                    _ing("морковь", category="овощи", amount=1, unit="шт"),
                    _ing("цветная капуста", category="овощи", amount=200),
                    _ing("лук репчатый", category="овощи", amount=1, unit="шт"),
                ],
                f"Овощной суп #{seq}",
            ),
            "гарнир/крупа": (
                [
                    _ing("гречка", category="крупы", amount=200),
                    _ing("морковь", category="овощи", amount=1, unit="шт"),
                    _ing("лук репчатый", category="овощи", amount=1, unit="шт"),
                    _ing("оливковое масло", category="масла/соусы", amount=20),
                ],
                f"Гречка с овощами #{seq}",
            ),
            "салат": (salad_ings, f"Овощной салат #{seq}"),
        }
        return by_dish.get(dish, (salad_ings, f"Овощное блюдо #{seq}"))

    if dish == "котлеты" and "мясо_птица" in groups:
        return (
            [
                _ing("куриное филе", category="мясо_птица", amount=400),
                _ing("картофель", category="овощи", amount=3, unit="шт"),
                _ing("морковь", category="овощи", amount=1, unit="шт"),
                _ing("лук репчатый", category="овощи", amount=1, unit="шт"),
            ],
            f"Куриные котлеты #{seq}",
        )
    if dish == "суп":
        if "рыба" in groups:
            return (
                [
                    _ing("филе трески", category="рыба", amount=300),
                    _ing("картофель", category="овощи", amount=2, unit="шт"),
                    _ing("морковь", category="овощи", amount=1, unit="шт"),
                    _ing("лук репчатый", category="овощи", amount=1, unit="шт"),
                ],
                f"Рыбный суп #{seq}",
            )
        return (
            [
                _ing("куриное филе", category="мясо_птица", amount=250),
                _ing("картофель", category="овощи", amount=2, unit="шт"),
                _ing("морковь", category="овощи", amount=1, unit="шт"),
                _ing("лук репчатый", category="овощи", amount=1, unit="шт"),
            ],
            f"Куриный суп #{seq}",
        )
    if dish == "запеканка":
        if no_dairy:
            return (
                [
                    _ing("картофель", category="овощи", amount=4, unit="шт"),
                    _ing("кабачок", category="овощи", amount=1, unit="шт"),
                    _ing("морковь", category="овощи", amount=1, unit="шт"),
                    _ing("помидор", category="овощи", amount=2, unit="шт"),
                ],
                f"Овощная запеканка #{seq}",
            )
        return (
            [
                _ing("картофель", category="овощи", amount=4, unit="шт"),
                _ing("кабачок", category="овощи", amount=1, unit="шт"),
                _ing("сыр твёрдый", category="молочные продукты", amount=120),
                _ing("сметана", category="молочные продукты", amount=100),
            ],
            f"Запеканка с сыром #{seq}",
        )
    if dish == "гарнир/крупа":
        return (
            [
                _ing("гречка", category="крупы", amount=200),
                _ing("морковь", category="овощи", amount=1, unit="шт"),
                _ing("лук репчатый", category="овощи", amount=1, unit="шт"),
                _ing("сливочное масло", category="молочные продукты", amount=20),
            ],
            f"Гречка с овощами #{seq}",
        )
    return (salad_ings, f"Овощной салат #{seq}")


def build_no_api_recipe(signal: dict[str, Any], seq: int) -> dict[str, Any]:
    """Deterministic valid-ish recipe for smoke tests without OpenAI."""
    dish = signal.get("dish_family", "семейное горячее")
    meal_hints = signal.get("meal_type_hints") or ["lunch", "dinner"]
    meal = "breakfast" if "breakfast" in meal_hints else "lunch"
    cat_hints = signal.get("category_hints") or ["main"]
    category = cat_hints[0] if cat_hints[0] in {"main", "soup", "salad", "side", "breakfast", "snack", "dessert", "drink"} else "main"
    if dish == "суп":
        category = "soup"
        meal = "lunch"
    elif dish == "салат":
        category = "salad"

    ingredients, title = _ingredients_and_title_for_signal(signal, dish, seq)
    restriction_keys = _restriction_keys_from_signal(signal)
    allergen_keys: list[str] = []
    vegan = _is_vegan_signal(signal)
    diet_tags = ["vegan"] if vegan else ["balanced"]

    steps = [
        _step(1, "Подготовьте все ингредиенты: вымойте овощи и обсушите бумажным полотенцем."),
        _step(2, "Нарежьте продукты равномерными кусочками для одинакового времени приготовления."),
        _step(3, "Приготовьте блюдо выбранным способом, периодически помешивая на среднем огне."),
        _step(4, "Перед подачей попробуйте на соль и при необходимости доведите вкус до баланса."),
    ]

    recipe = {
        "schema_version": SCHEMA_VERSION,
        "status": "gold",
        "source_type": "generated_original",
        "source_signal_ids": [signal.get("signal_id", f"pov_sig_{seq:06d}")],
        "originality": {
            "is_original_planam_recipe": True,
            "no_source_title_used": True,
            "no_source_steps_used": True,
            "no_direct_copy": True,
            "source_similarity_risk": "low",
            "originality_notes": "no-api smoke recipe",
        },
        "title": title[:80],
        "subtitle": "Семейный рецепт PLANAM",
        "description": "Оригинальный семейный рецепт PLANAM, созданный для dry-run теста без внешнего источника.",
        "meal_type": meal,
        "category": category,
        "cuisine_style": "семейная",
        "servings": 4,
        "prep_time_min": 15,
        "cook_time_min": 25,
        "total_time_min": 40,
        "difficulty": signal.get("complexity", "easy"),
        "family_fit": "high",
        "ingredients": ingredients,
        "steps": steps,
        "nutrition_per_serving": {
            "kcal": 320 if vegan else 380,
            "protein_g": 14 if vegan else 28,
            "fat_g": 10 if vegan else 12,
            "carbs_g": 38 if vegan else 35,
            "fiber_g": 6 if vegan else 5,
            "salt_g": 1.2,
            "sugar_g": 2.0,
        },
        "restriction_keys": restriction_keys,
        "allergen_keys": allergen_keys,
        "diet_tags": diet_tags,
        "shopping": {
            "aggregation_safe": True,
            "has_fractional_amounts": False,
            "rounding_notes": "",
        },
        "image_prompt_data": {
            "dish_visual_summary": f"Домашнее блюдо ({dish}) на белой тарелке в стиле PLANAM",
            "serving_style": "единый сервиз PLANAM",
            "avoid_visuals": ["текст", "логотипы", "руки", "грязный фон"],
        },
        "quality": {"score": 0, "flags": [], "warnings": []},
        "tags": ["gold_v3", "recipe_schema_v3", "status:gold"],
    }
    return recipe


async def generate_recipe_via_api(
    signal: dict[str, Any],
    *,
    temperature: float,
    model: str | None = None,
    validator_feedback: list[dict[str, str]] | None = None,
    target_profile: dict[str, Any] | None = None,
) -> dict[str, Any]:
    messages = build_recipe_gold_v3_generation_messages(
        signal,
        target_profile,
        validator_feedback=validator_feedback,
    )
    data = await ai_client.chat_json(
        system=messages[0]["content"],
        user=messages[1]["content"],
        temperature=temperature,
        max_tokens=4096,
        retries=1,
        model=model,
    )
    if not isinstance(data, dict):
        raise ValueError("Model response is not a JSON object")
    return data


def needs_quality_retry(result: ValidationResult, retry_below_score: int) -> bool:
    return not result.ok or result.score < retry_below_score


def validator_feedback_from_result(
    result: ValidationResult,
    *,
    retry_below_score: int = PRODUCTION_READY_MIN_SCORE,
) -> list[dict[str, str]]:
    retry_codes = feedback_codes_for_retry()
    feedback: list[dict[str, str]] = [
        {
            "code": i.code,
            "message": i.message,
            "path": i.path or "",
            "severity": i.severity,
        }
        for i in result.errors[:8]
    ]
    for issue in result.warnings:
        if issue.code in retry_codes and len(feedback) < 12:
            feedback.append(
                {
                    "code": issue.code,
                    "message": issue.message,
                    "path": issue.path or "",
                    "severity": "warning",
                }
            )
    if result.ok and result.score < retry_below_score:
        feedback.append(
            {
                "code": "score_below_threshold",
                "message": f"validation score {result.score} < {retry_below_score}",
                "path": "quality.score",
                "severity": "warning",
            }
        )
    return feedback


async def generate_one(
    signal: dict[str, Any],
    *,
    seq: int,
    no_api: bool,
    temperature: float,
    model: str | None,
    retry_invalid: int,
    retry_below_score: int,
    stats: GenerationStats,
) -> dict[str, Any] | None:
    stats.attempted += 1
    feedback: list[dict[str, str]] | None = None
    target_profile = build_target_profile_from_signal(signal)

    for attempt in range(1 + retry_invalid):
        if no_api:
            raw = build_no_api_recipe(signal, seq)
        else:
            stats.api_calls += 1
            raw = await generate_recipe_via_api(
                signal,
                temperature=temperature,
                model=model,
                validator_feedback=feedback,
                target_profile=target_profile,
            )
        recipe = postprocess_generated_recipe(enrich_recipe_metadata(raw, signal))
        violations = originality_post_check(recipe)
        if violations:
            stats.originality_violations.extend(
                [f"{signal.get('signal_id')}: {v}" for v in violations]
            )
            stats.failed.append(
                {
                    "signal_id": signal.get("signal_id"),
                    "reason": "originality",
                    "violations": violations,
                }
            )
            stats.invalid += 1
            return None

        result = validate_recipe_gold_v3(recipe)
        for issue in result.errors:
            stats.error_codes[issue.code] += 1
        for issue in result.warnings:
            stats.warning_codes[issue.code] += 1

        if not needs_quality_retry(result, retry_below_score):
            recipe["quality"]["score"] = result.score
            stats.valid += 1
            stats.scores.append(result.score)
            stats.titles.append(recipe.get("title", ""))
            stats.meal_types[recipe.get("meal_type", "")] += 1
            stats.categories[recipe.get("category", "")] += 1
            for rk in recipe.get("restriction_keys") or []:
                stats.restriction_keys[rk] += 1
            for ak in recipe.get("allergen_keys") or []:
                stats.allergen_keys[ak] += 1
            return recipe

        if attempt < retry_invalid:
            stats.retries_used += 1
            if result.ok:
                stats.low_score_retries += 1
            feedback = validator_feedback_from_result(
                result, retry_below_score=retry_below_score
            )
        else:
            stats.invalid += 1
            stats.failed.append(
                {
                    "signal_id": signal.get("signal_id"),
                    "title": recipe.get("title"),
                    "errors": [e.code for e in result.errors],
                    "warnings": [w.code for w in result.warnings[:5]],
                    "score": result.score,
                    "reason": "low_score" if result.ok else "validation_errors",
                }
            )
    return None


async def run_generation(args: argparse.Namespace) -> GenerationStats:
    stats = GenerationStats(mode="no-api" if args.no_api else "api")
    stats.model = args.model or ai_client._effective_model()

    signals = load_jsonl(args.signals)
    selected = select_diverse_signals(
        signals, args.limit, sample_start=args.sample_start
    )

    if not args.no_api:
        ok_cost, estimated = check_cost_guard(
            args.limit,
            args.retry_invalid,
            args.max_cost_usd,
            model=args.model,
        )
        stats.estimated_cost_usd = estimated
        if not ok_cost:
            per = estimated_cost_per_request(args.model)
            raise SystemExit(
                f"Cost guard: estimated ${estimated:.2f} exceeds --max-cost-usd {args.max_cost_usd} "
                f"(~{args.limit * (1 + args.retry_invalid)} calls × ${per:.2f}/call, model={args.model or 'default'})"
            )
        if not ai_client.is_ai_configured():
            raise AiUnavailableError("OPENAI_API_KEY not configured")

    for idx, signal in enumerate(selected, start=1):
        recipe = await generate_one(
            signal,
            seq=idx,
            no_api=args.no_api,
            temperature=args.temperature,
            model=args.model,
            retry_invalid=args.retry_invalid,
            retry_below_score=args.retry_below_score,
            stats=stats,
        )
        if recipe:
            stats.valid_recipes.append(recipe)

    stats.real_api_run = not args.no_api and stats.api_calls > 0
    if stats.real_api_run:
        per = estimated_cost_per_request(args.model)
        stats.estimated_cost_usd = stats.api_calls * per
    return stats


def git_meta() -> tuple[str, str]:
    try:
        branch = subprocess.check_output(
            ["git", "branch", "--show-current"], cwd=ROOT, text=True
        ).strip()
        commit = subprocess.check_output(
            ["git", "log", "-1", "--oneline"], cwd=ROOT, text=True
        ).strip()
        return branch, commit
    except Exception:
        return "unknown", "unknown"


def build_report_md(
    args: argparse.Namespace,
    stats: GenerationStats,
    *,
    api_skipped_reason: str | None = None,
) -> str:
    branch, commit = git_meta()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    avg_score = round(sum(stats.scores) / len(stats.scores), 1) if stats.scores else 0
    originality_ok = not stats.originality_violations

    lines = [
        "# Recipe Gold V3 — Stage F Generation Report",
        "",
        f"**Generated:** {now}",
        f"**Branch:** `{branch}`",
        f"**Commit:** `{commit}`",
        f"**Mode:** `{stats.mode}`",
        f"**Real API run:** `{stats.real_api_run}`",
        "",
    ]
    if api_skipped_reason:
        lines.extend([f"**API note:** {api_skipped_reason}", ""])

    lines.extend(
        [
            "## Parameters",
            "",
            f"- Signals: `{args.signals}`",
            f"- Output: `{args.output}`",
            f"- Limit: `{args.limit}`",
            f"- Max cost USD: `{args.max_cost_usd}`",
            f"- Model: `{stats.model}`",
            f"- Model override CLI: `{args.model or '(default from settings)'}`",
            f"- Temperature: `{args.temperature}`",
            f"- Retry invalid: `{args.retry_invalid}`",
            f"- Retry below score: `{args.retry_below_score}`",
            "",
            "## Summary",
            "",
            f"- Attempted: `{stats.attempted}`",
            f"- Valid generated: `{stats.valid}`",
            f"- Invalid failed: `{stats.invalid}`",
            f"- Retries used: `{stats.retries_used}`",
            f"- Low-score retries: `{stats.low_score_retries}`",
            "",
            "## Quality gate",
            "",
            f"- Retry below score threshold: `{args.retry_below_score}`",
            f"- Output includes only recipes with validator ok=True and score >= {args.retry_below_score}",
            "",
            f"- API calls: `{stats.api_calls}`",
            f"- Estimated cost USD: `{stats.estimated_cost_usd:.2f}`",
            f"- Avg validation score: `{avg_score}`",
            f"- Originality safety: `{'PASS' if originality_ok else 'FAIL'}`",
            "",
            "## Generated titles",
            "",
        ]
    )
    for t in stats.titles:
        lines.append(f"- {t}")
    if not stats.titles:
        lines.append("- none")

    def _dist(title: str, counter: Counter[str]) -> None:
        lines.extend(["", f"## {title}", ""])
        if counter:
            for k, v in counter.most_common():
                lines.append(f"- {k}: `{v}`")
        else:
            lines.append("- none")

    _dist("Meal types", stats.meal_types)
    _dist("Categories", stats.categories)
    _dist("Restriction keys", stats.restriction_keys)
    _dist("Allergen keys", stats.allergen_keys)
    _dist("Validation errors", stats.error_codes)
    _dist("Validation warnings", stats.warning_codes)

    if stats.failed:
        lines.extend(["", "## Failed", ""])
        for item in stats.failed[:15]:
            lines.append(f"- `{json.dumps(item, ensure_ascii=False)}`")

    if stats.valid_recipes:
        lines.extend(["", "## Sample recipes (2)", ""])
        for recipe in stats.valid_recipes[:2]:
            summary = {
                "title": recipe.get("title"),
                "meal_type": recipe.get("meal_type"),
                "category": recipe.get("category"),
                "servings": recipe.get("servings"),
                "ingredients_count": len(recipe.get("ingredients") or []),
                "steps_count": len(recipe.get("steps") or []),
                "score": (recipe.get("quality") or {}).get("score"),
            }
            lines.append(f"- `{json.dumps(summary, ensure_ascii=False)}`")

    lines.extend(
        [
            "",
            "## Not done",
            "",
            "- DB import",
            "- Image generation",
            "- Safe reset",
            "- Production DB changes",
            "",
            "## Next stage",
            "",
            "Stage G/H — originality + quality gate; Stage R importer after approval.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    api_skipped: str | None = None

    if not args.no_api and not ai_client.is_ai_configured():
        api_skipped = "OPENAI_API_KEY not configured; real generation skipped"
        args.no_api = True

    try:
        stats = asyncio.run(run_generation(args))
    except AiUnavailableError:
        if args.no_api:
            raise
        api_skipped = "OPENAI_API_KEY not configured; real generation skipped"
        args.no_api = True
        stats = asyncio.run(run_generation(args))
    except SystemExit as exc:
        print(str(exc), file=sys.stderr)
        return 2

    if args.dry_run or stats.valid_recipes:
        write_jsonl(args.output, stats.valid_recipes)

    report_md = build_report_md(args, stats, api_skipped_reason=api_skipped)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(report_md, encoding="utf-8")

    print(
        f"attempted={stats.attempted} valid={stats.valid} invalid={stats.invalid} "
        f"api_calls={stats.api_calls} mode={stats.mode}"
    )
    return 0 if stats.valid > 0 or args.no_api else 1


if __name__ == "__main__":
    raise SystemExit(main())
