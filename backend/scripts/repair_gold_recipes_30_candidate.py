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
    (re.compile(r"^\s*post-workout:\s*", re.I), "post_workout"),
    (re.compile(r"^\s*pro high protein:\s*", re.I), "high_protein"),
    (re.compile(r"^\s*pro small portion:\s*", re.I), "small_portion"),
)
TITLE_SUFFIX_RE = re.compile(r"\s+#\d+\s*$")
PORK_WORDS = ("свинина", "бекон", "ветчина", "свиным", "свиная", "свиные")
SEAFOOD_WORDS = ("кревет", "морепродукт", "мидии", "кальмар")
MEAT_WORDS = (
    "куриц",
    "курин",
    "индейк",
    "говядин",
    "свинин",
    "бекон",
    "ветчин",
    "фарш",
    "рыб",
    "треск",
    "тунц",
    "лосось",
    "кревет",
)


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


def supplemental_ingredient(
    name: str,
    amount: int | float,
    unit: str,
    category: str,
    slug: str | None = None,
) -> dict[str, Any]:
    return {
        "name": name,
        "display_name": name,
        "canonical_name": name.lower(),
        "canonical_slug": slug,
        "amount": amount,
        "unit": unit,
        "display_amount": f"{amount} {unit}",
        "shopping_category_slug": category,
        "pantry_category_slug": category,
        "allergens": [],
        "diet_flags": [],
        "is_optional": False,
    }


def has_ingredient(ingredients: list[dict[str, Any]], marker: str) -> bool:
    lowered = marker.lower()
    return any(lowered in str(item.get("name") or "").lower() for item in ingredients)


def supplement_pool(recipe: dict[str, Any], title: str, meal_type: str) -> list[dict[str, Any]]:
    category = str(recipe.get("category") or "").lower()
    text = " ".join([title, category, meal_type]).lower()
    if "кефир" in text:
        return [
            supplemental_ingredient("Яблоко", 1, "шт", "fruits_berries", "apple"),
            supplemental_ingredient("Семена льна", 1, "ч.л.", "grocery", "flax_seeds"),
        ]
    if "банан" in text and "арахис" in text:
        return [
            supplemental_ingredient("Овсяные хлопья", 20, "г", "grains_pasta", "oats"),
            supplemental_ingredient("Ягоды", 50, "г", "fruits_berries", "berries"),
        ]
    if "творог" in text:
        return [
            supplemental_ingredient("Семена льна", 1, "ч.л.", "grocery", "flax_seeds"),
            supplemental_ingredient("Мёд", 1, "ч.л.", "grocery", "honey"),
        ]
    if "салат" in text:
        return [
            supplemental_ingredient("Зелень", 20, "г", "vegetables_greens", "greens"),
            supplemental_ingredient("Лимонный сок", 1, "ч.л.", "grocery", "lemon_juice"),
        ]
    if "суп" in text:
        return [
            supplemental_ingredient("Вода", 1.5, "л", "drinks", "water"),
            supplemental_ingredient("Зелень", 20, "г", "vegetables_greens", "greens"),
        ]
    if meal_type == "snack":
        return [
            supplemental_ingredient("Ягоды", 50, "г", "fruits_berries", "berries"),
            supplemental_ingredient("Семена льна", 1, "ч.л.", "grocery", "flax_seeds"),
        ]
    return [
        supplemental_ingredient("Зелень", 20, "г", "vegetables_greens", "greens"),
        supplemental_ingredient("Оливковое масло", 1, "ч.л.", "grocery", "olive_oil"),
    ]


def ensure_min_ingredients(
    recipe: dict[str, Any],
    title: str,
    meal_type: str,
    ingredients: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    result = list(ingredients)
    for candidate in supplement_pool(recipe, title, meal_type):
        if len(result) >= 3:
            break
        if has_ingredient(result, str(candidate["name"])):
            continue
        result.append(candidate)
    return result


def repair_step(item: dict[str, Any], index: int) -> dict[str, Any]:
    text = item.get("instruction") or item.get("text") or ""
    return {
        "step_number": int(item.get("step_number") or item.get("order") or index),
        "text": str(text).strip(),
        "title": item.get("title") or f"Шаг {index}",
        "duration_minutes": item.get("duration_minutes"),
    }


def make_step(index: int, text: str, duration_minutes: int | None = None) -> dict[str, Any]:
    return {
        "step_number": index,
        "text": text,
        "title": f"Шаг {index}",
        "duration_minutes": duration_minutes,
    }


def ingredient_text(ingredients: list[dict[str, Any]], limit: int = 4) -> str:
    names = [str(item.get("name") or "").strip().lower() for item in ingredients if item.get("name")]
    if not names:
        return "ингредиенты"
    return ", ".join(names[:limit])


def generated_steps(
    recipe: dict[str, Any],
    title: str,
    meal_type: str,
    ingredients: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    category = str(recipe.get("category") or "").lower()
    text = " ".join([title, category, meal_type, ingredient_text(ingredients, 8)]).lower()
    names = ingredient_text(ingredients)

    if "салат" in text:
        return [
            make_step(1, "Овощи и зелень вымойте и обсушите, крупные ингредиенты нарежьте небольшими кусочками."),
            make_step(2, "Белковый ингредиент подготовьте отдельно: отварите, обжарьте или используйте уже готовым и нарежьте ломтиками."),
            make_step(3, "Смешайте ингредиенты в миске, добавьте заправку и аккуратно перемешайте перед подачей."),
        ]
    if "суп" in text:
        return [
            make_step(1, "Овощи нарежьте небольшими кубиками, бобовые или крупу при наличии промойте."),
            make_step(2, "В кастрюле доведите воду или бульон до кипения, добавьте плотные овощи и варите до мягкости.", 20),
            make_step(3, "Добавьте оставшиеся ингредиенты, доведите суп до вкуса и дайте настояться 5 минут.", 5),
        ]
    if any(marker in text for marker in ("каша", "овсян", "рисовая каша")):
        return [
            make_step(1, "Крупу промойте или отмерьте, подготовьте молоко, воду и добавки."),
            make_step(2, "Варите кашу на слабом огне, регулярно помешивая, пока крупа не станет мягкой.", 10),
            make_step(3, "Добавьте ягоды, мёд или масло по рецепту, перемешайте и подавайте тёплой."),
        ]
    if any(marker in text for marker in ("смузи", "боул")):
        return [
            make_step(1, "Подготовьте основу и добавки: фрукты нарежьте, орехи или семена отмерьте."),
            make_step(2, "Измельчите мягкие ингредиенты с молочной или растительной основой до густой однородной текстуры."),
            make_step(3, "Переложите в миску, добавьте оставшиеся топпинги и подавайте сразу."),
        ]
    if "тост" in text:
        return [
            make_step(1, "Подготовьте хлеб, овощи и яйцо; авокадо разомните с лимонным соком."),
            make_step(2, "Подсушите хлеб до лёгкой корочки, яйцо сварите или приготовьте до нужной степени готовности.", 6),
            make_step(3, "Намажьте авокадо на тост, выложите яйцо и подавайте сразу."),
        ]
    if any(marker in text for marker in ("омлет", "яйца", "яйцо")):
        return [
            make_step(1, "Яйца и овощи подготовьте: овощи нарежьте, яйца взбейте или отварите по рецепту."),
            make_step(2, "Приготовьте основу на слабом или среднем огне до плотной, но мягкой текстуры.", 6),
            make_step(3, "Добавьте овощи и зелень, дайте блюду постоять 1-2 минуты и подавайте тёплым."),
        ]
    if any(marker in text for marker in ("творог", "фрукт", "перекус", "орех", "банан")):
        return [
            make_step(1, f"Подготовьте {names}: фрукты вымойте, крупные ингредиенты нарежьте или отмерьте."),
            make_step(2, "Смешайте основу с добавками до удобной для подачи текстуры."),
            make_step(3, "Переложите в порционную миску или тарелку и подавайте сразу."),
        ]
    if any(marker in text for marker in ("запек", "лосось", "треск", "рыб", "куриц", "индейк", "говядин")):
        return [
            make_step(1, f"Подготовьте {names}: мясо, рыбу или овощи нарежьте порционными кусками."),
            make_step(2, "Выложите ингредиенты в форму или на сковороду, добавьте специи и немного масла."),
            make_step(3, "Готовьте до полной готовности, затем дайте блюду постоять 3-5 минут перед подачей.", 20),
        ]
    if any(marker in text for marker in ("паста", "гречка", "булгур", "рис", "нут")):
        return [
            make_step(1, "Крупу или пасту отварите до готовности, овощи и остальные ингредиенты подготовьте."),
            make_step(2, "Соедините основу с овощами и белковым ингредиентом, прогрейте на среднем огне.", 10),
            make_step(3, "Доведите блюдо до вкуса, перемешайте и подавайте тёплым."),
        ]
    return [
        make_step(1, f"Подготовьте {names}: промойте, очистите и нарежьте ингредиенты при необходимости."),
        make_step(2, "Приготовьте основные ингредиенты выбранным способом до мягкости и безопасной готовности."),
        make_step(3, "Перемешайте, доведите до вкуса и подавайте блюдо тёплым."),
    ]


def ensure_min_steps(
    recipe: dict[str, Any],
    title: str,
    meal_type: str,
    ingredients: list[dict[str, Any]],
    steps: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if len(steps) >= 3 and all(str(step.get("text") or "").strip() for step in steps):
        return steps
    return generated_steps(recipe, title, meal_type, ingredients)


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
    meal_type = infer_meal_type(recipe)
    ingredients = [repair_ingredient(item) for item in recipe.get("ingredients") or []]
    ingredients = ensure_min_ingredients(recipe, title, meal_type, ingredients)
    steps = [repair_step(item, i) for i, item in enumerate(recipe.get("steps") or [], start=1)]
    steps = ensure_min_steps(recipe, title, meal_type, ingredients, steps)
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
