"""Deterministically repair gold_recipes_30.jsonl into a Gold V3 candidate JSONL.

No OpenAI calls, no DB writes, no import. The output remains a candidate batch.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
INPUT = ROOT / "data" / "recipe_v2" / "gold_recipes_30.jsonl"
OUTPUT = ROOT / "data" / "recipe_v2" / "gold_recipes_30_repaired_candidate.jsonl"
REPORTS = ROOT / "reports"
REPORT_JSON = REPORTS / "SPRINT_1_3C_GOLD_RECIPES_30_REPAIR.json"
REPORT_MD = REPORTS / "SPRINT_1_3C_GOLD_RECIPES_30_REPAIR.md"

PREFIX_PATTERNS = (
    (re.compile(r"^\s*high protein:\s*", re.I), "high_protein"),
    (re.compile(r"^\s*pro weight loss:\s*", re.I), "weight_loss"),
    (re.compile(r"^\s*pre-workout:\s*", re.I), "pre_workout"),
)
TITLE_SUFFIX_RE = re.compile(r"\s+#\d+\s*$")
PORK_WORDS = ("свинина", "бекон", "ветчина", "свиным", "свиная", "свиные")
SEAFOOD_WORDS = ("кревет", "морепродукт", "мидии", "кальмар")
MEAT_WORDS = ("куриц", "индейк", "говядин", "свинин", "бекон", "фарш", "рыб", "лосось", "кревет")


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_title(title: str, tags: list[str]) -> tuple[str, list[str]]:
    cleaned = TITLE_SUFFIX_RE.sub("", title or "").strip()
    for pattern, tag in PREFIX_PATTERNS:
        if pattern.search(cleaned):
            cleaned = pattern.sub("", cleaned).strip()
            tags.append(tag)
    cleaned = cleaned.replace(" bowl ", " боул ").replace("Bowl", "Боул").replace("bowl", "боул")
    cleaned = re.sub(r"\s+без\s+свинины\b", "", cleaned, flags=re.I).strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned[:1].upper() + cleaned[1:] if cleaned else cleaned, tags


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip()).lower()


def infer_meal_type(recipe: dict[str, Any]) -> str:
    meal_types = recipe.get("meal_types")
    if isinstance(meal_types, list) and meal_types:
        value = str(meal_types[0])
        if value in {"breakfast", "lunch", "dinner", "snack"}:
            return value
    text = " ".join(
        [
            str(recipe.get("title") or ""),
            str(recipe.get("category") or ""),
            " ".join(ingredient_name(item) for item in recipe.get("ingredients") or []),
        ]
    ).lower()
    if any(word in text for word in ("овсян", "омлет", "творог", "завтрак", "сырник")):
        return "breakfast"
    if any(word in text for word in ("салат", "перекус", "йогурт", "смузи")):
        return "snack"
    if any(word in text for word in ("суп", "борщ")):
        return "lunch"
    return "dinner"


def ingredient_name(item: dict[str, Any]) -> str:
    return str(item.get("display_name") or item.get("name") or item.get("canonical_name") or "").strip()


def repair_ingredient(item: dict[str, Any]) -> dict[str, Any]:
    name = ingredient_name(item)
    amount = item.get("amount")
    unit = item.get("unit")
    return {
        "name": name,
        "display_name": name,
        "canonical_name": item.get("canonical_name") or name.lower(),
        "canonical_slug": item.get("canonical_slug"),
        "amount": amount,
        "unit": unit,
        "display_amount": f"{amount} {unit}".strip() if amount is not None and unit else str(amount or ""),
        "shopping_category_slug": item.get("shopping_category_slug") or item.get("category") or "grocery",
        "pantry_category_slug": item.get("pantry_category_slug") or item.get("category") or "grocery",
        "allergens": item.get("allergens") or [],
        "diet_flags": item.get("diet_flags") or [],
        "is_optional": bool(item.get("is_optional", False)),
    }


def repair_step(item: dict[str, Any], index: int) -> dict[str, Any]:
    text = item.get("instruction") or item.get("text") or ""
    return {
        "step_number": int(item.get("step_number") or item.get("order") or index),
        "text": str(text).strip(),
        "title": item.get("title") or f"Шаг {index}",
        "duration_minutes": item.get("duration_minutes"),
    }


def nutrition_per_serving(recipe: dict[str, Any]) -> dict[str, Any]:
    raw = recipe.get("nutrition_per_serving") or recipe.get("nutrition_summary") or {}
    return {
        "kcal": raw.get("kcal") or raw.get("calories"),
        "protein_g": raw.get("protein_g"),
        "fat_g": raw.get("fat_g"),
        "carbs_g": raw.get("carbs_g"),
        "fiber_g": raw.get("fiber_g"),
        "sugar_g": raw.get("sugar_g"),
        "salt_g": raw.get("salt_g"),
    }


def derive_restriction_tags(recipe: dict[str, Any], ingredients: list[dict[str, Any]]) -> list[str]:
    tags = set(str(t) for t in recipe.get("tags") or [])
    tags.update(str(t) for t in recipe.get("diet_tags") or [])
    text = " ".join([recipe.get("title") or "", *(item["name"] for item in ingredients)]).lower()
    if not any(word in text for word in PORK_WORDS):
        tags.add("no_pork_possible")
    if not any(word in text for word in SEAFOOD_WORDS):
        tags.add("no_seafood_possible")
    if not any(word in text for word in MEAT_WORDS):
        tags.add("vegetarian")
    return sorted(tags)


def repair_record(recipe: dict[str, Any], index: int) -> tuple[dict[str, Any], list[str]]:
    warnings: list[str] = []
    tags = ["gold_v3_candidate", "status:candidate"]
    title, tags = normalize_title(str(recipe.get("title") or ""), tags)
    if "свинина" in title.lower() and "без свинины" in str(recipe.get("title") or "").lower():
        warnings.append("title had pork/no-pork contradiction and was normalized")
    ingredients = [repair_ingredient(item) for item in recipe.get("ingredients") or []]
    steps = [repair_step(item, i) for i, item in enumerate(recipe.get("steps") or [], start=1)]
    meal_type = infer_meal_type(recipe)
    tags.extend(derive_restriction_tags(recipe, ingredients))
    tags.append(f"meal:{meal_type}")
    repaired = {
        "schema_version": "recipe_gold_v3",
        "status": "candidate",
        "source_type": "gold_v3_candidate",
        "candidate_index": index,
        "title": title,
        "display_title": title,
        "normalized_title": normalize_text(title),
        "description": recipe.get("description") or "",
        "meal_type": meal_type,
        "category": recipe.get("category") or "main",
        "servings": recipe.get("servings") or 4,
        "prep_time_minutes": recipe.get("prep_time_minutes") or recipe.get("prep_time_min") or 10,
        "cook_time_minutes": recipe.get("cook_time_minutes") or recipe.get("cook_time_min") or 0,
        "difficulty": recipe.get("difficulty") or "easy",
        "tags": sorted(set(tag for tag in tags if tag)),
        "diet_tags": recipe.get("diet_tags") or [],
        "excludes": recipe.get("excludes") or [],
        "allergens": recipe.get("allergens") or [],
        "religious_tags": recipe.get("religious_tags") or [],
        "ingredients": ingredients,
        "steps": steps,
        "nutrition_per_serving": nutrition_per_serving(recipe),
        "shopping": {
            "aggregation_safe": bool(ingredients),
            "has_fractional_amounts": any(isinstance(item.get("amount"), float) for item in ingredients),
            "rounding_notes": "",
        },
        "image_prompt": (
            "Фото готового блюда ПланАм без текста, логотипов и рук; натуральный свет, "
            f"аккуратная подача: {title}."
        ),
        "image_url": None,
        "hero_image_url": None,
        "thumbnail_url": None,
    }
    return repaired, warnings


def load_records() -> list[dict[str, Any]]:
    records = []
    for line in INPUT.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def run() -> dict[str, Any]:
    REPORTS.mkdir(exist_ok=True)
    records = load_records()
    repaired = []
    warnings: list[str] = []
    for index, recipe in enumerate(records, start=1):
        item, item_warnings = repair_record(recipe, index)
        repaired.append(item)
        warnings.extend(f"{index}: {warning}" for warning in item_warnings)
    OUTPUT.write_text(
        "".join(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n" for item in repaired),
        encoding="utf-8",
    )
    titles = [item["normalized_title"] for item in repaired]
    duplicates = [title for title, count in Counter(titles).items() if count > 1]
    report = {
        "generated_at": now(),
        "input": str(INPUT.relative_to(ROOT)),
        "output": str(OUTPUT.relative_to(ROOT)),
        "input_count": len(records),
        "output_count": len(repaired),
        "duplicate_normalized_titles": duplicates,
        "warnings": warnings,
    }
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    REPORT_MD.write_text(render(report), encoding="utf-8")
    return report


def render(report: dict[str, Any]) -> str:
    lines = [
        "# Sprint 1.3C Gold Recipes 30 Repair",
        "",
        f"Generated: `{report['generated_at']}`",
        f"Input count: `{report['input_count']}`",
        f"Output count: `{report['output_count']}`",
        f"Output: `{report['output']}`",
        f"Duplicate normalized titles: `{report['duplicate_normalized_titles']}`",
        "",
        "No OpenAI, no DB import, no image generation.",
    ]
    if report["warnings"]:
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- {warning}" for warning in report["warnings"])
    return "\n".join(lines) + "\n"


def main() -> int:
    report = run()
    print(f"Wrote {OUTPUT}")
    return 0 if report["output_count"] == 30 else 1


if __name__ == "__main__":
    raise SystemExit(main())
