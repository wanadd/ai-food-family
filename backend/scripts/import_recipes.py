#!/usr/bin/env python3
"""Safe idempotent recipe importer for PlanAm.

Run from the repository root:
    python backend/scripts/import_recipes.py --input sample_recipes.json --dry-run
    python backend/scripts/import_recipes.py --input sample_recipes.json --commit
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
API_ROOT = ROOT / "apps" / "api"
sys.path.insert(0, str(API_ROOT))

os.environ.setdefault("DATABASE_URL", os.environ.get("DATABASE_URL", ""))


ALLOWED_MEAL_TYPES = {
    "breakfast",
    "lunch",
    "dinner",
    "snack",
    "dessert",
    "drink",
    "cocktail",
    "smoothie",
    "protein_shake",
    "tea",
    "coffee",
}
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
ALLOWED_SOURCE_TYPES = {"manual", "import", "seed", "v1_import"}
MENU_MEAL_TYPES = {"breakfast", "lunch", "dinner", "snack"}
MENU_SNACK_RECIPE_MEAL_TYPES = {
    "drink",
    "dessert",
    "smoothie",
    "cocktail",
    "protein_shake",
    "tea",
    "coffee",
}
MEAL_TYPE_TO_CATALOG = {
    "breakfast": "breakfast",
    "lunch": "lunch",
    "dinner": "dinner",
    "snack": "snack",
    "dessert": "snack",
    "drink": "snack",
    "cocktail": "snack",
    "smoothie": "snack",
    "protein_shake": "snack",
    "tea": "snack",
    "coffee": "snack",
}


def catalog_meal_type(meal_type: str | None) -> str:
    raw = (meal_type or "lunch").strip().lower()
    return MEAL_TYPE_TO_CATALOG.get(raw, "lunch")


class RecipeImportError(ValueError):
    pass


def normalize_title(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


def as_list(value: Any, field: str) -> list[Any]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise RecipeImportError(f"{field} must be a list")
    return value


def as_int(value: Any, field: str, default: int, *, min_value: int = 0) -> int:
    if value is None:
        return default
    try:
        result = int(value)
    except (TypeError, ValueError) as exc:
        raise RecipeImportError(f"{field} must be an integer") from exc
    if result < min_value:
        raise RecipeImportError(f"{field} must be >= {min_value}")
    return result


def as_optional_float(value: Any, field: str) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise RecipeImportError(f"{field} must be a number") from exc


def clean_text(
    value: Any,
    field: str,
    *,
    max_length: int,
    required: bool = False,
    default: str | None = None,
) -> str | None:
    if value is None:
        text = default
    else:
        text = str(value).strip()
    if required and not text:
        raise RecipeImportError(f"{field} is required")
    if not text:
        return None
    if len(text) > max_length:
        raise RecipeImportError(
            f"{field} must be <= {max_length} characters "
            f"(got {len(text)})"
        )
    return text


def clean_string_list(value: Any, field: str, *, item_max_length: int) -> list[str]:
    items = as_list(value, field)
    result: list[str] = []
    for index, item in enumerate(items, start=1):
        text = str(item).strip()
        if text:
            if len(text) > item_max_length:
                raise RecipeImportError(
                    f"{field}[{index}] must be <= {item_max_length} characters "
                    f"(got {len(text)})"
                )
            result.append(text)
    return result


def normalize_menu_meal_type(recipe_meal_type: str) -> str:
    if recipe_meal_type in MENU_MEAL_TYPES:
        return recipe_meal_type
    if recipe_meal_type in MENU_SNACK_RECIPE_MEAL_TYPES:
        return "snack"
    raise RecipeImportError(
        f"recipe meal_type cannot be mapped to menu meal type: {recipe_meal_type!r}"
    )


def validate_ingredients(value: Any) -> list[dict[str, Any]]:
    items = as_list(value, "ingredients")
    if not items:
        raise RecipeImportError("ingredients must contain at least one item")

    result: list[dict[str, Any]] = []
    for index, raw in enumerate(items, start=1):
        if not isinstance(raw, dict):
            raise RecipeImportError(f"ingredients[{index}] must be an object")
        prefix = f"ingredients[{index}]"
        name = clean_text(
            raw.get("name"),
            f"{prefix}.name",
            max_length=120,
            required=True,
        )

        amount = str(raw.get("amount", "")).strip()
        quantity = clean_text(
            raw.get("quantity"),
            f"{prefix}.quantity",
            max_length=32,
        ) or ""
        unit = clean_text(raw.get("unit"), f"{prefix}.unit", max_length=32) or ""
        if not amount and not quantity:
            raise RecipeImportError(
                f"ingredients[{index}] requires amount or quantity"
            )
        if not quantity and amount:
            quantity = amount
        if not unit:
            unit = "шт"
        if len(quantity) > 32:
            raise RecipeImportError(
                f"{prefix}.quantity must be <= 32 characters "
                f"(got {len(quantity)})"
            )
        if not amount:
            amount = f"{quantity} {unit}".strip()

        result.append(
            {
                "name": name,
                "amount": amount,
                "quantity": quantity,
                "unit": unit,
                "category": clean_text(
                    raw.get("category"),
                    f"{prefix}.category",
                    max_length=32,
                ),
                "is_optional": bool(raw.get("is_optional", False)),
                "notes": clean_text(
                    raw.get("notes"),
                    f"{prefix}.notes",
                    max_length=200,
                ),
            }
        )
    return result


def validate_recipe(raw: Any, index: int) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise RecipeImportError(f"recipe[{index}] must be an object")

    title = clean_text(raw.get("title"), "title", max_length=200, required=True)

    meal_type = clean_text(
        raw.get("meal_type"),
        "meal_type",
        max_length=32,
        required=True,
    )
    if meal_type not in ALLOWED_MEAL_TYPES:
        raise RecipeImportError(f"meal_type is invalid: {meal_type!r}")

    meal_type = catalog_meal_type(meal_type)
    menu_meal_type = normalize_menu_meal_type(meal_type)

    category = clean_text(
        raw.get("category"),
        "category",
        max_length=32,
        default="main",
    )
    if category not in ALLOWED_CATEGORIES:
        raise RecipeImportError(f"category is invalid: {category!r}")

    difficulty = clean_text(
        raw.get("difficulty"),
        "difficulty",
        max_length=16,
        default="easy",
    )
    if difficulty not in ALLOWED_DIFFICULTIES:
        raise RecipeImportError(f"difficulty is invalid: {difficulty!r}")

    source_type = clean_text(
        raw.get("source_type"),
        "source_type",
        max_length=16,
        default="import",
    )
    if source_type not in ALLOWED_SOURCE_TYPES:
        raise RecipeImportError(f"source_type is invalid: {source_type!r}")

    steps = [str(step).strip() for step in as_list(raw.get("steps"), "steps")]
    steps = [step for step in steps if step]
    if not steps:
        raise RecipeImportError("steps must contain at least one non-empty item")

    cooking_time = as_int(
        raw.get("cooking_time_minutes"),
        "cooking_time_minutes",
        30,
        min_value=0,
    )
    prep_time = as_int(
        raw.get("prep_time_minutes"),
        "prep_time_minutes",
        cooking_time or 30,
        min_value=0,
    )

    return {
        "title": title,
        "description": str(raw.get("description") or "").strip(),
        "meal_type": meal_type,
        "menu_meal_type": menu_meal_type,
        "category": category,
        "cuisine": clean_text(raw.get("cuisine"), "cuisine", max_length=64),
        "difficulty": difficulty,
        "cooking_time_minutes": cooking_time,
        "prep_time_minutes": prep_time,
        "servings": as_int(raw.get("servings"), "servings", 4, min_value=1),
        "calories_per_serving": as_optional_float(
            raw.get("calories_per_serving"), "calories_per_serving"
        ),
        "protein_g": as_optional_float(raw.get("protein_g"), "protein_g"),
        "fat_g": as_optional_float(raw.get("fat_g"), "fat_g"),
        "carbs_g": as_optional_float(raw.get("carbs_g"), "carbs_g"),
        "fiber_g": as_optional_float(raw.get("fiber_g"), "fiber_g"),
        "sugar_g": as_optional_float(raw.get("sugar_g"), "sugar_g"),
        "source_type": source_type,
        "source_url": clean_text(raw.get("source_url"), "source_url", max_length=512),
        "image_url": clean_text(raw.get("image_url"), "image_url", max_length=512),
        "hero_image_url": clean_text(
            raw.get("hero_image_url"), "hero_image_url", max_length=512
        ),
        "thumbnail_url": clean_text(
            raw.get("thumbnail_url"), "thumbnail_url", max_length=512
        ),
        "is_drink": bool(raw.get("is_drink", meal_type in {"drink", "cocktail", "smoothie", "protein_shake", "tea", "coffee"})),
        "is_alcoholic": bool(raw.get("is_alcoholic", False)),
        "alcohol_percent": as_optional_float(
            raw.get("alcohol_percent"), "alcohol_percent"
        ),
        "caffeine_mg": as_optional_float(raw.get("caffeine_mg"), "caffeine_mg"),
        "suitable_for_children": bool(raw.get("suitable_for_children", True)),
        "suitable_for_sport": bool(raw.get("suitable_for_sport", False)),
        "suitable_for_event": bool(raw.get("suitable_for_event", False)),
        "diets": clean_string_list(raw.get("diets"), "diets", item_max_length=64),
        "tags": clean_string_list(raw.get("tags"), "tags", item_max_length=64),
        "allergens": clean_string_list(
            raw.get("allergens"),
            "allergens",
            item_max_length=64,
        ),
        "restrictions": clean_string_list(
            raw.get("restrictions"),
            "restrictions",
            item_max_length=64,
        ),
        "ingredients": validate_ingredients(raw.get("ingredients")),
        "steps": steps,
    }


def load_recipes(path: Path) -> list[Any]:
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, list):
        raise RecipeImportError("Input JSON must be a list of recipes")
    return data


def load_db_dependencies():
    from app.database import SessionLocal
    from app.models.recipe import Recipe
    from app.services.recipe_storage import persist_recipe_structure

    return SessionLocal, Recipe, persist_recipe_structure


def find_existing_by_title(db, recipe_model, normalized: str):
    rows = db.query(recipe_model).all()
    for recipe in rows:
        if normalize_title(recipe.title) == normalized:
            return recipe
    return None


def apply_recipe(
    db,
    recipe_model,
    persist_structure,
    data: dict[str, Any],
    existing,
):
    title = data["title"]
    fields = {
        key: data[key]
        for key in (
            "title",
            "description",
            "meal_type",
            "category",
            "cuisine",
            "difficulty",
            "cooking_time_minutes",
            "prep_time_minutes",
            "servings",
            "calories_per_serving",
            "protein_g",
            "fat_g",
            "carbs_g",
            "fiber_g",
            "sugar_g",
            "source_type",
            "source_url",
            "image_url",
            "hero_image_url",
            "thumbnail_url",
            "is_drink",
            "is_alcoholic",
            "alcohol_percent",
            "caffeine_mg",
            "suitable_for_children",
            "suitable_for_sport",
            "suitable_for_event",
            "diets",
            "tags",
        )
    }
    fields["original_title"] = data.get("original_title") or title
    fields["normalized_title"] = data.get("normalized_title") or normalize_title(title)
    display = data.get("display_title")
    if display is None:
        from app.services.recipes.title_normalize import display_title_from

        display = display_title_from(title)
    fields["display_title"] = display

    recipe = existing or recipe_model(**fields)
    if existing is not None:
        for key, value in fields.items():
            if key == "original_title" and recipe.original_title:
                continue
            setattr(recipe, key, value)
    else:
        db.add(recipe)
        db.flush()

    persist_structure(
        db,
        recipe,
        ingredients=data["ingredients"],
        steps=data["steps"],
        tags=data["tags"],
        allergens=data["allergens"],
        restrictions=data["restrictions"],
    )
    return recipe


def import_recipes(path: Path, *, dry_run: bool, update: bool) -> int:
    raw_items = load_recipes(path)
    db = None
    recipe_model = None
    persist_structure = None
    if not dry_run:
        SessionLocal, recipe_model, persist_structure = load_db_dependencies()
        db = SessionLocal()
    created = 0
    updated = 0
    skipped = 0
    failed = 0
    seen_titles: set[str] = set()

    try:
        for index, raw in enumerate(raw_items, start=1):
            try:
                data = validate_recipe(raw, index)
                title_key = normalize_title(data["title"])
                if title_key in seen_titles:
                    skipped += 1
                    print(f"SKIP #{index}: duplicate title inside file: {data['title']}")
                    continue
                seen_titles.add(title_key)

                if dry_run:
                    print(f"DRY-RUN VALID #{index}: {data['title']}")
                    created += 1
                    continue

                existing = find_existing_by_title(db, recipe_model, title_key)
                if existing is not None and not update:
                    skipped += 1
                    print(f"SKIP #{index}: already exists: {data['title']}")
                    continue

                action = "UPDATE" if existing is not None else "CREATE"
                apply_recipe(db, recipe_model, persist_structure, data, existing)
                db.commit()
                if existing is not None:
                    updated += 1
                else:
                    created += 1
                print(f"{action} #{index}: {data['title']}")
            except Exception as exc:
                if db is not None:
                    db.rollback()
                failed += 1
                title = raw.get("title") if isinstance(raw, dict) else None
                label = f" {title!r}" if title else ""
                print(f"FAIL #{index}{label}: {exc}", file=sys.stderr)

        print(
            "Summary: "
            f"created={created}, updated={updated}, skipped={skipped}, failed={failed}"
        )
        return 1 if failed else 0
    finally:
        if db is not None:
            db.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import PlanAm recipes from JSON")
    parser.add_argument(
        "--input",
        default=str(ROOT / "sample_recipes.json"),
        help="Path to recipes JSON file",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and show actions without writing to DB",
    )
    mode.add_argument(
        "--commit",
        action="store_true",
        help="Write valid recipes to DB",
    )
    parser.add_argument(
        "--update",
        action="store_true",
        help="Update existing recipes matched by normalized title",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_path = Path(args.input)
    if not input_path.is_absolute():
        input_path = ROOT / input_path
    if not input_path.exists():
        print(f"Input file does not exist: {input_path}", file=sys.stderr)
        return 2

    dry_run = not args.commit
    return import_recipes(input_path, dry_run=dry_run, update=args.update)


if __name__ == "__main__":
    raise SystemExit(main())
