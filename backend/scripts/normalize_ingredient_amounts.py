#!/usr/bin/env python3
"""Preview ingredient amount normalization without changing the database.

Reads recipe ingredients, parses amount into quantity/unit, and writes audit
artifacts only. It does not update recipes or create migrations.

Run from the repository root:
    python backend/scripts/normalize_ingredient_amounts.py
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATABASE_URL = "postgresql://aifood:aifood@localhost:5432/aifood"
DEFAULT_REPORT_PATH = ROOT / "reports" / "ingredient_normalization_audit.md"
DEFAULT_FAILED_REPORT_PATH = ROOT / "reports" / "ingredient_normalization_failed_cases.md"
DEFAULT_PREVIEW_PATH = ROOT / "exports" / "ingredient_normalization_preview.json"
DEFAULT_PREVIEW_LIMIT = 200

NULL_AMOUNT_VALUES = {
    "",
    "по вкусу",
    "по желанию",
    "вкус",
    "щепотка",
    "щепотку",
    "горсть",
    "пучок",
}

UNIT_ALIASES = {
    "г": ("g", 1.0),
    "гр": ("g", 1.0),
    "гр.": ("g", 1.0),
    "грамм": ("g", 1.0),
    "грамма": ("g", 1.0),
    "граммов": ("g", 1.0),
    "kg": ("g", 1000.0),
    "кг": ("g", 1000.0),
    "килограмм": ("g", 1000.0),
    "килограмма": ("g", 1000.0),
    "килограммов": ("g", 1000.0),
    "мл": ("ml", 1.0),
    "ml": ("ml", 1.0),
    "миллилитр": ("ml", 1.0),
    "миллилитра": ("ml", 1.0),
    "миллилитров": ("ml", 1.0),
    "л": ("ml", 1000.0),
    "l": ("ml", 1000.0),
    "литр": ("ml", 1000.0),
    "литра": ("ml", 1000.0),
    "литров": ("ml", 1000.0),
    "шт": ("pcs", 1.0),
    "шт.": ("pcs", 1.0),
    "штук": ("pcs", 1.0),
    "штука": ("pcs", 1.0),
    "штуки": ("pcs", 1.0),
    "pcs": ("pcs", 1.0),
    "pc": ("pcs", 1.0),
    "зуб": ("pcs", 1.0),
    "зуб.": ("pcs", 1.0),
    "зубчик": ("pcs", 1.0),
    "зубчика": ("pcs", 1.0),
    "зубчиков": ("pcs", 1.0),
    "ст.л.": ("tbsp", 1.0),
    "ст. л.": ("tbsp", 1.0),
    "ст л": ("tbsp", 1.0),
    "столовая ложка": ("tbsp", 1.0),
    "столовые ложки": ("tbsp", 1.0),
    "столовых ложек": ("tbsp", 1.0),
    "ч.л.": ("tsp", 1.0),
    "ч. л.": ("tsp", 1.0),
    "ч л": ("tsp", 1.0),
    "чайная ложка": ("tsp", 1.0),
    "чайные ложки": ("tsp", 1.0),
    "чайных ложек": ("tsp", 1.0),
    "стак": ("cup", 1.0),
    "стак.": ("cup", 1.0),
    "стакан": ("cup", 1.0),
    "стакана": ("cup", 1.0),
    "стаканов": ("cup", 1.0),
    "пуч": ("bunch", 1.0),
    "пуч.": ("bunch", 1.0),
    "пучок": ("bunch", 1.0),
    "пучка": ("bunch", 1.0),
    "бан": ("can", 1.0),
    "бан.": ("can", 1.0),
    "банка": ("can", 1.0),
    "банки": ("can", 1.0),
    "щепот": ("pinch", 1.0),
    "щепот.": ("pinch", 1.0),
    "щепотка": ("pinch", 1.0),
    "щепотки": ("pinch", 1.0),
    "горст": ("handful", 1.0),
    "горст.": ("handful", 1.0),
    "горсть": ("handful", 1.0),
    "горсти": ("handful", 1.0),
    "веточ": ("sprig", 1.0),
    "веточ.": ("sprig", 1.0),
    "веточка": ("sprig", 1.0),
    "веточки": ("sprig", 1.0),
    "порция": ("serving", 1.0),
    "порции": ("serving", 1.0),
    "порций": ("serving", 1.0),
    "упак": ("package", 1.0),
    "упак.": ("package", 1.0),
    "упаковка": ("package", 1.0),
    "упаковки": ("package", 1.0),
    "пакет": ("package", 1.0),
    "пакет.": ("package", 1.0),
    "пакета": ("package", 1.0),
    "пакетов": ("package", 1.0),
    "вилок": ("head", 1.0),
    "кочан": ("head", 1.0),
    "кочана": ("head", 1.0),
    "ломт": ("slice", 1.0),
    "ломт.": ("slice", 1.0),
    "ломтик": ("slice", 1.0),
    "ломтика": ("slice", 1.0),
    "ломтиков": ("slice", 1.0),
}


@dataclass(frozen=True)
class RecipeRow:
    id: int
    title: str
    ingredients: list[Any]


@dataclass(frozen=True)
class NormalizedAmount:
    quantity: float | None
    unit: str | None
    success: bool
    reason: str
    amount_type: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Preview normalization of ingredient amount strings"
    )
    parser.add_argument(
        "--database-url",
        default=os.environ.get("DATABASE_URL") or DEFAULT_DATABASE_URL,
        help="Database URL. Defaults to DATABASE_URL or local docker PostgreSQL.",
    )
    parser.add_argument(
        "--report",
        default=str(DEFAULT_REPORT_PATH),
        help="Path to Markdown normalization audit",
    )
    parser.add_argument(
        "--failed-report",
        default=str(DEFAULT_FAILED_REPORT_PATH),
        help="Path to Markdown report with failed normalization cases",
    )
    parser.add_argument(
        "--preview",
        default=str(DEFAULT_PREVIEW_PATH),
        help="Path to JSON preview with first normalized results",
    )
    parser.add_argument(
        "--preview-limit",
        type=int,
        default=DEFAULT_PREVIEW_LIMIT,
        help="Number of normalization examples to include in preview JSON",
    )
    return parser.parse_args()


def readable_text(value: Any) -> str:
    text_value = str(value or "").strip()
    if not any(marker in text_value for marker in ("Р", "С", "Ð", "Ñ")):
        return text_value
    try:
        repaired = text_value.encode("cp1251").decode("utf-8")
    except UnicodeError:
        return text_value
    return repaired or text_value


def clean_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip())


def load_recipes(database_url: str) -> list[RecipeRow]:
    engine = create_engine(database_url)
    query = text(
        """
        SELECT id, title, ingredients
        FROM recipes
        ORDER BY id
        """
    )
    with engine.connect() as conn:
        rows = list(conn.execute(query).mappings())
    return rows_to_recipes(rows)


def load_recipes_via_docker() -> list[RecipeRow]:
    sql = """
        SELECT COALESCE(json_agg(row_to_json(t) ORDER BY id), '[]'::json)
        FROM (
            SELECT id, title, ingredients
            FROM recipes
            ORDER BY id
        ) AS t;
        """
    cmd = [
        "docker",
        "compose",
        "exec",
        "-T",
        "postgres",
        "psql",
        "-U",
        "aifood",
        "-d",
        "aifood",
        "-t",
        "-A",
        "-c",
        sql,
    ]
    result = subprocess.run(
        cmd,
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
    )
    return rows_to_recipes(json.loads(result.stdout.strip() or "[]"))


def rows_to_recipes(rows: Any) -> list[RecipeRow]:
    recipes: list[RecipeRow] = []
    for row in rows:
        ingredients = row.get("ingredients")
        recipes.append(
            RecipeRow(
                id=int(row["id"]),
                title=readable_text(row["title"]),
                ingredients=ingredients if isinstance(ingredients, list) else [],
            )
        )
    return recipes


def normalize_unit_text(value: str) -> str:
    text_value = value.lower().replace(",", ".").strip()
    text_value = re.sub(r"\s+", " ", text_value)
    text_value = text_value.replace("ст л", "ст.л.").replace("ч л", "ч.л.")
    return text_value


def parse_number(value: str) -> float | None:
    text_value = value.strip().replace(",", ".")
    if "/" in text_value:
        left, right = text_value.split("/", 1)
        try:
            denominator = float(right)
            if denominator == 0:
                return None
            return float(left) / denominator
        except ValueError:
            return None
    try:
        return float(text_value)
    except ValueError:
        return None


NUMBER_PATTERN = r"(?:\d+\s*/\s*\d+|\d+(?:[,.]\d+)?)"


def convert_unit(unit_text: str) -> tuple[str, float] | None:
    normalized = normalize_unit_text(unit_text)
    return UNIT_ALIASES.get(normalized)


def normalize_amount(amount: Any) -> NormalizedAmount:
    raw = clean_text(amount).lower().replace("ё", "е")
    raw = raw.replace("½", "1/2").replace("¼", "1/4").replace("¾", "3/4")
    if raw in NULL_AMOUNT_VALUES or raw.startswith("по вкусу") or raw.startswith("по желанию"):
        return NormalizedAmount(None, None, True, "to_taste", "to_taste")

    range_match = re.match(
        rf"^\s*(?P<left>{NUMBER_PATTERN})\s*(?:[-–—]|\.\.\.)\s*(?P<right>{NUMBER_PATTERN})\s*(?P<unit>.*)$",
        raw,
    )
    if range_match:
        left = parse_number(range_match.group("left").replace(" ", ""))
        right = parse_number(range_match.group("right").replace(" ", ""))
        if left is None or right is None:
            return NormalizedAmount(None, None, False, "invalid_range", "failed")
        unit_text = normalize_unit_text(range_match.group("unit"))
        if not unit_text:
            target_unit, multiplier = "pcs", 1.0
        else:
            converted = convert_unit(unit_text)
            if converted is None:
                return NormalizedAmount(None, None, False, f"unknown_unit:{unit_text}", "failed")
            target_unit, multiplier = converted
        return NormalizedAmount(
            ((left + right) / 2) * multiplier,
            target_unit,
            True,
            "range",
            "range",
        )

    match = re.match(rf"^\s*(?P<number>{NUMBER_PATTERN})\s*(?P<unit>.*)$", raw)
    if not match:
        return NormalizedAmount(None, None, False, "no_numeric_prefix", "failed")

    number = parse_number(match.group("number").replace(" ", ""))
    if number is None:
        return NormalizedAmount(None, None, False, "invalid_number", "failed")

    unit_text = normalize_unit_text(match.group("unit"))
    if not unit_text:
        return NormalizedAmount(number, "pcs", True, "default_pcs", "exact")

    converted = convert_unit(unit_text)
    if converted is not None:
        target_unit, multiplier = converted
        amount_type = (
            "approximate"
            if target_unit
            in {
                "bunch",
                "can",
                "pinch",
                "handful",
                "sprig",
                "serving",
                "package",
                "head",
                "slice",
            }
            else "exact"
        )
        return NormalizedAmount(number * multiplier, target_unit, True, "parsed", amount_type)

    return NormalizedAmount(None, None, False, f"unknown_unit:{unit_text}", "failed")


def failed_suffix(amount: Any) -> str:
    raw = clean_text(amount).lower().replace("ё", "е")
    raw = raw.replace("½", "1/2").replace("¼", "1/4").replace("¾", "3/4")
    match = re.match(
        rf"^\s*(?:{NUMBER_PATTERN})\s*(?P<unit>.*)$",
        raw,
    )
    if match:
        return normalize_unit_text(match.group("unit")) or "<empty>"
    return raw or "<empty>"


def suggested_rule(amount: Any, reason: str) -> str:
    raw = clean_text(amount).lower().replace("ё", "е")
    suffix = failed_suffix(raw)
    if raw.startswith("по вкусу"):
        return "Treat amount starting with `по вкусу` as quantity=null, unit=null."
    if "порция" in suffix:
        return "Add unit alias `порция` -> `serving` or keep unresolved until recipe-specific serving logic exists."
    if "стак" in suffix:
        return "Add unit alias `стак.` -> `cup` with configurable ml conversion, likely 200-250 ml."
    if "пуч" in suffix:
        return "Add unit alias `пуч.` -> `bunch` or map herbs bunch to ingredient-specific grams."
    if "бан" in suffix:
        return "Add unit alias `бан.` -> `can` with ingredient-specific grams/ml."
    if "упак" in suffix or "пакет" in suffix:
        return "Add package units only with ingredient-specific package weight."
    if "щепот" in suffix:
        return "Add unit alias `щепот.` -> `pinch`; keep out of nutrition math or map to tiny grams."
    if "горст" in suffix:
        return "Add unit alias `горст.` -> `handful` with ingredient-specific grams."
    if "вилок" in suffix:
        return "Add unit alias `вилок` -> `head`; map cabbage/lettuce heads to ingredient-specific grams."
    if "ломт" in suffix:
        return "Add unit alias `ломт.` -> `slice`; map by ingredient."
    if reason == "no_numeric_prefix":
        return "Manual review or null normalization; amount has no numeric prefix."
    return "Manual review; no obvious safe global conversion."


def fmt_number(value: float | None) -> int | float | None:
    if value is None:
        return None
    if abs(value - round(value)) < 1e-9:
        return int(round(value))
    return round(value, 4)


def audit_recipes(
    recipes: list[RecipeRow],
    preview_limit: int,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    total = 0
    normalized = 0
    failed = 0
    reason_counts: Counter[str] = Counter()
    unit_counts: Counter[str] = Counter()
    amount_type_counts: Counter[str] = Counter()
    failed_raw_counts: Counter[str] = Counter()
    failed_suffix_counts: Counter[str] = Counter()
    failed_by_reason: dict[str, list[dict[str, Any]]] = {}
    failed_examples: list[dict[str, Any]] = []
    failed_cases: list[dict[str, Any]] = []
    preview: list[dict[str, Any]] = []

    for recipe in recipes:
        for index, ingredient in enumerate(recipe.ingredients, start=1):
            if not isinstance(ingredient, dict):
                continue
            total += 1
            amount = ingredient.get("amount")
            result = normalize_amount(amount)
            if result.success:
                normalized += 1
                reason_counts[result.reason] += 1
                amount_type_counts[result.amount_type] += 1
                if result.unit:
                    unit_counts[result.unit] += 1
            else:
                failed += 1
                reason_counts[result.reason] += 1
                amount_type_counts["failed"] += 1
                raw_amount = clean_text(amount)
                suffix = failed_suffix(amount)
                failed_raw_counts[raw_amount] += 1
                failed_suffix_counts[suffix] += 1
                failed_case = {
                    "recipe_id": recipe.id,
                    "recipe_title": recipe.title,
                    "ingredient_index": index,
                    "name": ingredient.get("name"),
                    "amount": amount,
                    "reason": result.reason,
                    "suffix": suffix,
                    "suggested_rule": suggested_rule(amount, result.reason),
                }
                failed_cases.append(failed_case)
                failed_by_reason.setdefault(result.reason, [])
                if len(failed_examples) < 50:
                    failed_examples.append(failed_case)
                if len(failed_by_reason[result.reason]) < 12:
                    failed_by_reason[result.reason].append(failed_case)

            item = {
                "recipe_id": recipe.id,
                "recipe_title": recipe.title,
                "ingredient_index": index,
                "name": ingredient.get("name"),
                "amount": amount,
                "quantity": fmt_number(result.quantity),
                "unit": result.unit,
                "amount_type": result.amount_type,
                "success": result.success,
                "reason": result.reason,
            }
            if len(preview) < preview_limit:
                preview.append(item)

    summary = {
        "total_ingredients": total,
        "normalized_count": normalized,
        "failed_count": failed,
        "success_rate": (normalized / total * 100) if total else 0.0,
        "effective_success_rate": (
            (normalized - amount_type_counts["to_taste"])
            / (total - amount_type_counts["to_taste"])
            * 100
        )
        if total > amount_type_counts["to_taste"]
        else 0.0,
        "reason_counts": reason_counts,
        "unit_counts": unit_counts,
        "amount_type_counts": amount_type_counts,
        "failed_raw_counts": failed_raw_counts,
        "failed_suffix_counts": failed_suffix_counts,
        "failed_by_reason": failed_by_reason,
        "failed_examples": failed_examples,
        "failed_cases": failed_cases,
    }
    return summary, preview


def build_report(summary: dict[str, Any], preview_path: Path) -> str:
    total = summary["total_ingredients"]
    normalized = summary["normalized_count"]
    failed = summary["failed_count"]
    success_rate = summary["success_rate"]
    amount_type_counts: Counter[str] = summary["amount_type_counts"]
    lines = [
        "# Ingredient Normalization Audit",
        "",
        "Scope: read-only normalization preview from `amount` to `quantity`/`unit`. No database changes, recipe updates, imports, or migrations were performed.",
        "",
        "## Summary",
        "",
        f"- Total ingredients: `{total}`",
        f"- Normalized count: `{normalized}`",
        f"- Failed count: `{failed}`",
        f"- Success rate: `{success_rate:.1f}%`",
        f"- Exact count: `{amount_type_counts['exact']}`",
        f"- Range count: `{amount_type_counts['range']}`",
        f"- To taste count: `{amount_type_counts['to_taste']}`",
        f"- Approximate count: `{amount_type_counts['approximate']}`",
        f"- Real failed count: `{amount_type_counts['failed']}`",
        "- Effective success rate without to_taste: "
        f"`{summary['effective_success_rate']:.1f}%`",
        f"- Preview JSON: `{preview_path}`",
        "",
        "## Supported Output Units",
        "",
        "- `g` for grams, with `kg` converted to grams.",
        "- `ml` for milliliters, with `l` converted to milliliters.",
        "- `pcs` for pieces.",
        "- `tbsp` for tablespoons.",
        "- `tsp` for teaspoons.",
        "- `cup`, `bunch`, `can`, `pinch`, `handful`, `sprig`, `serving` for approximate units.",
        "- `null/null` for taste/free-form amounts such as `по вкусу`.",
        "",
        "## Amount Type Distribution",
        "",
    ]
    for amount_type in ("exact", "range", "to_taste", "approximate", "failed"):
        lines.append(f"- `{amount_type}`: `{amount_type_counts[amount_type]}`")

    lines.extend(
        [
            "",
            "## Unit Distribution",
            "",
        ]
    )
    unit_counts: Counter[str] = summary["unit_counts"]
    if unit_counts:
        for unit, count in unit_counts.most_common():
            lines.append(f"- `{unit}`: `{count}`")
    else:
        lines.append("- `n/a`")

    lines.extend(["", "## Parse Reasons", ""])
    reason_counts: Counter[str] = summary["reason_counts"]
    for reason, count in reason_counts.most_common():
        lines.append(f"- `{reason}`: `{count}`")

    lines.extend(["", "## Top Failed Raw Amount Values", ""])
    failed_raw_counts: Counter[str] = summary["failed_raw_counts"]
    if failed_raw_counts:
        for amount, count in failed_raw_counts.most_common(30):
            lines.append(f"- `{amount}`: `{count}`")
    else:
        lines.append("- `n/a`")

    lines.extend(["", "## Top Failed Unit-Like Suffixes", ""])
    failed_suffix_counts: Counter[str] = summary["failed_suffix_counts"]
    if failed_suffix_counts:
        for suffix, count in failed_suffix_counts.most_common(30):
            lines.append(f"- `{suffix}`: `{count}`")
    else:
        lines.append("- `n/a`")

    lines.extend(["", "## Examples Grouped By Reason", ""])
    failed_by_reason: dict[str, list[dict[str, Any]]] = summary["failed_by_reason"]
    if failed_by_reason:
        for reason, items in sorted(failed_by_reason.items()):
            lines.append(f"### {reason}")
            for item in items:
                lines.append(
                    f"- `#{item['recipe_id']}` {item['recipe_title']} / "
                    f"{item.get('name')}: `{item.get('amount')}` -> "
                    f"{item.get('suggested_rule')}"
                )
            lines.append("")
    else:
        lines.append("- `n/a`")

    lines.extend(["", "## Failed Examples", ""])
    failed_examples: list[dict[str, Any]] = summary["failed_examples"]
    if failed_examples:
        for item in failed_examples:
            lines.append(
                f"- `#{item['recipe_id']}` {item['recipe_title']} / "
                f"{item.get('name')}: `{item.get('amount')}` -> `{item['reason']}`"
            )
    else:
        lines.append("- `n/a`")

    return "\n".join(lines).rstrip() + "\n"


def build_failed_cases_report(summary: dict[str, Any]) -> str:
    lines = [
        "# Ingredient Normalization Failed Cases",
        "",
        "Scope: read-only review of failed `amount` parsing cases. No database changes, recipe updates, imports, or migrations were performed.",
        "",
        "## Summary",
        "",
        f"- Failed count: `{summary['failed_count']}`",
        "",
        "## Failed Cases",
        "",
    ]
    failed_cases: list[dict[str, Any]] = summary["failed_cases"]
    if not failed_cases:
        lines.append("- `n/a`")
        return "\n".join(lines).rstrip() + "\n"

    for item in failed_cases:
        lines.append(
            f"- amount=`{item.get('amount')}` | ingredient=`{item.get('name')}` | "
            f"recipe=`#{item['recipe_id']} {item['recipe_title']}` | "
            f"reason=`{item['reason']}` | suffix=`{item['suffix']}` | "
            f"suggested rule: {item['suggested_rule']}"
        )

    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    args = parse_args()
    report_path = Path(args.report).expanduser().resolve()
    failed_report_path = Path(args.failed_report).expanduser().resolve()
    preview_path = Path(args.preview).expanduser().resolve()
    if args.preview_limit < 1:
        raise SystemExit("--preview-limit must be at least 1")

    try:
        recipes = load_recipes(args.database_url)
        connection_note = "sqlalchemy"
    except SQLAlchemyError as exc:
        print(
            "SQLAlchemy connection failed, falling back to docker compose psql: "
            f"{exc.__class__.__name__}"
        )
        recipes = load_recipes_via_docker()
        connection_note = "docker compose psql"

    summary, preview = audit_recipes(recipes, args.preview_limit)

    preview_path.parent.mkdir(parents=True, exist_ok=True)
    preview_path.write_text(
        json.dumps(preview, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    report = build_report(summary, preview_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")
    failed_report = build_failed_cases_report(summary)
    failed_report_path.parent.mkdir(parents=True, exist_ok=True)
    failed_report_path.write_text(failed_report, encoding="utf-8")

    print(f"Read connection: {connection_note}")
    print(f"Total ingredients: {summary['total_ingredients']}")
    print(f"Normalized count: {summary['normalized_count']}")
    print(f"Failed count: {summary['failed_count']}")
    print(f"Success rate: {summary['success_rate']:.1f}%")
    print(f"Preview written to: {preview_path}")
    print(f"Report written to: {report_path}")
    print(f"Failed cases report written to: {failed_report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
