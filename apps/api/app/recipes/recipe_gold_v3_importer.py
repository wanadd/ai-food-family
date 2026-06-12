"""Stage R: Gold V3 recipe importer тАФ dry-run planning only (no DB writes by default)."""

from __future__ import annotations

import json
import re
import string
from collections import Counter
from pathlib import Path
from typing import Any

from app.recipes.product_taxonomy import legacy_shopping_slug
from app.recipes.recipe_gold_v3_postprocess import postprocess_generated_recipe
from app.recipes.recipe_gold_v3_schema import (
    ALLOWED_UNITS,
    SCHEMA_VERSION,
)
from app.recipes.recipe_gold_v3_validation import validate_recipe_gold_v3

DB_SOURCE_TYPE = "import"
TITLE_MAX_LEN = 200

NUTRITION_GOLD_TO_LEGACY: tuple[tuple[str, str], ...] = (
    ("kcal", "calories_per_serving"),
    ("protein_g", "protein_g"),
    ("fat_g", "fat_g"),
    ("carbs_g", "carbs_g"),
    ("fiber_g", "fiber_g"),
    ("sugar_g", "sugar_g"),
)

NUTRITION_GOLD_TO_SUMMARY: tuple[tuple[str, str], ...] = (
    ("kcal", "nutrition_kcal_per_serving"),
    ("protein_g", "nutrition_protein_per_serving"),
    ("fat_g", "nutrition_fat_per_serving"),
    ("carbs_g", "nutrition_carbs_per_serving"),
)

_PUNCT_TABLE = str.maketrans("", "", string.punctuation + "\u00ab\u00bb\u201c\u201d\u201e\u2018\u2019")


def load_gold_v3_jsonl(path: str | Path) -> list[dict[str, Any]]:
    p = Path(path)
    rows: list[dict[str, Any]] = []
    with p.open(encoding="utf-8") as fh:
        for line_no, line in enumerate(fh, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                data = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid JSON at line {line_no}: {exc}") from exc
            if not isinstance(data, dict):
                raise ValueError(f"line {line_no}: expected JSON object")
            rows.append({"line": line_no, "recipe": data})
    return rows


def normalize_recipe_title(title: str) -> str:
    t = str(title or "").casefold().replace("\u0451", "\u0435")
    t = t.translate(_PUNCT_TABLE)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def _as_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _map_ingredient(ing: dict[str, Any], index: int) -> tuple[dict[str, Any] | None, list[dict[str, str]]]:
    issues: list[dict[str, str]] = []
    name = str(ing.get("name") or "").strip()
    shopping_name = str(ing.get("shopping_name") or "").strip()
    unit = str(ing.get("unit") or "").strip()
    display_amount = str(ing.get("display_amount") or "").strip()
    category = str(ing.get("category") or "").strip()
    amount = ing.get("amount")

    if not name:
        issues.append({"code": "missing_ingredient_mapping", "message": f"ingredients[{index}].name empty"})
    if not shopping_name:
        issues.append({"code": "missing_shopping_name", "message": f"ingredients[{index}].shopping_name empty"})
    if amount is None:
        issues.append({"code": "missing_ingredient_mapping", "message": f"ingredients[{index}].amount missing"})
    if not unit:
        issues.append({"code": "unknown_unit", "message": f"ingredients[{index}].unit empty"})
    elif unit not in ALLOWED_UNITS:
        issues.append({"code": "unknown_unit", "message": f"ingredients[{index}].unit {unit!r} not canonical"})
    if not display_amount:
        issues.append({"code": "missing_ingredient_mapping", "message": f"ingredients[{index}].display_amount empty"})
    if not category:
        issues.append({"code": "unknown_category", "message": f"ingredients[{index}].category empty"})

    list_name = shopping_name or name
    legacy_category = legacy_shopping_slug(category) if category else "other"
    qty = str(int(amount)) if isinstance(amount, float) and amount == int(amount) else str(amount)

    payload = {
        "name": list_name,
        "quantity": qty,
        "unit": unit or "╨│",
        "category": legacy_category,
        "is_optional": bool(ing.get("optional", False)),
        "amount": display_amount or f"{qty} {unit}".strip(),
        "shopping_name": shopping_name or name,
        "original_name": name,
        "gold_v3_category": category,
    }
    return payload, issues


def map_gold_v3_to_db_payload(recipe: dict[str, Any]) -> dict[str, Any]:
    """Map Gold V3 dict to PLANAM recipes table + JSONB structure (plan only)."""
    recipe = postprocess_generated_recipe(recipe)
    nutrition = recipe.get("nutrition_per_serving") or {}
    quality = recipe.get("quality") or {}

    payload: dict[str, Any] = {
        "title": str(recipe.get("title") or "").strip()[:TITLE_MAX_LEN],
        "display_title": str(recipe.get("title") or "").strip()[:TITLE_MAX_LEN],
        "normalized_title": normalize_recipe_title(str(recipe.get("title") or "")),
        "description": str(recipe.get("description") or "").strip(),
        "meal_type": str(recipe.get("meal_type") or "lunch"),
        "category": str(recipe.get("category") or "main"),
        "cuisine": str(recipe.get("cuisine_style") or "unknown")[:64],
        "servings": int(recipe.get("servings") or 4),
        "prep_time_minutes": int(recipe.get("prep_time_min") or 0),
        "cooking_time_minutes": int(recipe.get("cook_time_min") or recipe.get("total_time_min") or 30),
        "difficulty": str(recipe.get("difficulty") or "easy"),
        "source_type": DB_SOURCE_TYPE,
        "source_url": None,
        "is_active": True,
        "diets": list(recipe.get("diet_tags") or []),
        "tags": _build_tags(recipe),
        "ingredients_jsonb": [],
        "ingredient_rows_plan": [],
        "steps_jsonb": [],
        "step_rows_plan": [],
        "allergens_plan": list(recipe.get("allergen_keys") or []),
        "restrictions_plan": list(recipe.get("restriction_keys") or []),
        "schema_version": SCHEMA_VERSION,
        "gold_status": str(recipe.get("status") or "gold"),
        "quality_score": int(quality.get("score") or recipe.get("_validation_score") or 0),
        "image_prompt_data": recipe.get("image_prompt_data") or {},
        "shopping_meta": recipe.get("shopping") or {},
        "gold_v3_extras": {
            "family_fit": recipe.get("family_fit"),
            "total_time_min": recipe.get("total_time_min"),
            "source_signal_ids": recipe.get("source_signal_ids") or [],
            "originality": recipe.get("originality") or {},
            "salt_g": nutrition.get("salt_g"),
        },
    }

    nutrition_mapped: dict[str, float | None] = {}
    nutrition_aliases: dict[str, str | None] = {}
    missing_nutrition: list[str] = []

    for gold_key, legacy_key in NUTRITION_GOLD_TO_LEGACY:
        val = _as_float(nutrition.get(gold_key))
        nutrition_mapped[legacy_key] = val
        payload[legacy_key] = val
        if val is None:
            missing_nutrition.append(gold_key)

    for gold_key, summary_key in NUTRITION_GOLD_TO_SUMMARY:
        val = _as_float(nutrition.get(gold_key))
        nutrition_mapped[summary_key] = val
        payload[summary_key] = val

    payload["nutrition_servings"] = float(payload["servings"])
    payload["nutrition_source"] = "gold_v3_import"
    payload["nutrition_confidence"] = "high"
    payload["nutrition_coverage_json"] = {
        "fiber_g": _as_float(nutrition.get("fiber_g")),
        "salt_g": _as_float(nutrition.get("salt_g")),
        "sugar_g": _as_float(nutrition.get("sugar_g")),
    }

    if nutrition.get("salt_g") is not None and "salt_g" not in {k for k, _ in NUTRITION_GOLD_TO_LEGACY}:
        nutrition_aliases["salt_g"] = "nutrition_coverage_json.salt_g"

    payload["_nutrition_mapped"] = nutrition_mapped
    payload["_nutrition_aliases"] = nutrition_aliases
    payload["_missing_nutrition_keys"] = missing_nutrition

    ingredient_issues: list[dict[str, str]] = []
    for idx, raw in enumerate(recipe.get("ingredients") or []):
        if not isinstance(raw, dict):
            ingredient_issues.append(
                {"code": "missing_ingredient_mapping", "message": f"ingredients[{idx}] not object"}
            )
            continue
        mapped, issues = _map_ingredient(raw, idx)
        ingredient_issues.append(issues)
        if mapped:
            payload["ingredients_jsonb"].append(
                {
                    "name": mapped["name"],
                    "amount": mapped["amount"],
                    "is_optional": mapped["is_optional"],
                }
            )
            payload["ingredient_rows_plan"].append(mapped)

    payload["_ingredient_issues"] = [i for group in ingredient_issues for i in group]

    for step in recipe.get("steps") or []:
        if isinstance(step, dict):
            text = str(step.get("text") or "").strip()
            num = int(step.get("step_number") or len(payload["steps_jsonb"]) + 1)
        else:
            text = str(step).strip()
            num = len(payload["steps_jsonb"]) + 1
        if text:
            payload["steps_jsonb"].append(text)
            payload["step_rows_plan"].append({"step_number": num, "text": text})

    required = ("title", "meal_type", "category", "servings")
    payload["_missing_required"] = [f for f in required if not payload.get(f)]

    return payload


def _build_tags(recipe: dict[str, Any]) -> list[str]:
    tags = ["gold_v3", f"schema:{SCHEMA_VERSION}"]
    if recipe.get("family_fit"):
        tags.append(f"family_fit:{recipe['family_fit']}")
    for tag in recipe.get("diet_tags") or []:
        t = str(tag).strip()
        if t:
            tags.append(f"diet:{t}")
    return tags


def detect_existing_duplicates(
    session: Any | None,
    payloads: list[dict[str, Any]],
) -> dict[str, Any]:
    batch_dupes: list[dict[str, Any]] = []
    seen: dict[str, int] = {}
    for idx, payload in enumerate(payloads):
        norm = payload.get("normalized_title") or ""
        if not norm:
            continue
        if norm in seen:
            batch_dupes.append(
                {
                    "code": "duplicate_title_in_batch",
                    "index": idx,
                    "other_index": seen[norm],
                    "normalized_title": norm,
                    "title": payload.get("title"),
                }
            )
        else:
            seen[norm] = idx

    db_dupes: list[dict[str, Any]] = []
    db_available = False
    if session is not None:
        try:
            from sqlalchemy import select

            from app.models.recipe import Recipe

            rows = session.execute(
                select(Recipe.id, Recipe.title, Recipe.normalized_title)
            ).all()
            db_available = True
            db_index: dict[str, list[dict[str, Any]]] = {}
            for row in rows:
                rid, title, norm = row[0], row[1], row[2]
                for key in {normalize_recipe_title(title or ""), normalize_recipe_title(norm or "")}:
                    if key:
                        db_index.setdefault(key, []).append(
                            {"id": rid, "title": title, "normalized_title": norm}
                        )
            for idx, payload in enumerate(payloads):
                norm = payload.get("normalized_title") or ""
                hits = db_index.get(norm) or []
                for hit in hits:
                    db_dupes.append(
                        {
                            "code": "duplicate_title_in_db",
                            "index": idx,
                            "normalized_title": norm,
                            "existing_id": hit["id"],
                            "existing_title": hit["title"],
                        }
                    )
        except Exception as exc:
            db_dupes.append(
                {
                    "code": "db_duplicate_check_skipped",
                    "message": str(exc),
                }
            )

    return {
        "batch_duplicates": batch_dupes,
        "db_duplicates": db_dupes,
        "db_check_available": db_available,
    }


def plan_import_gold_v3_batch(
    recipes: list[dict[str, Any]],
    *,
    session: Any | None = None,
    dry_run: bool = True,
    require_quality_pass: bool = False,
    quality_gate_ok: bool | None = None,
) -> dict[str, Any]:
    if not dry_run:
        raise RuntimeError("db_write_attempted_in_dry_run: real import not implemented in Stage R")

    errors_by_code: Counter[str] = Counter()
    warnings_by_code: Counter[str] = Counter()
    per_recipe: list[dict[str, Any]] = []
    payloads: list[dict[str, Any]] = []

    if require_quality_pass and quality_gate_ok is False:
        errors_by_code["quality_gate_not_passed"] += 1

    for idx, recipe in enumerate(recipes):
        recipe_errors: list[str] = []
        recipe_warnings: list[str] = []

        if str(recipe.get("schema_version") or "") != SCHEMA_VERSION:
            recipe_errors.append("invalid_gold_v3_schema")
            errors_by_code["invalid_gold_v3_schema"] += 1

        validation = validate_recipe_gold_v3(recipe)
        if not validation.ok:
            recipe_errors.append("invalid_gold_v3_schema")
            errors_by_code["invalid_gold_v3_schema"] += 1
            for issue in validation.errors:
                errors_by_code[issue.code] += 1

        try:
            payload = map_gold_v3_to_db_payload(recipe)
        except Exception as exc:
            recipe_errors.append("missing_required_db_field")
            errors_by_code["missing_required_db_field"] += 1
            per_recipe.append(
                {
                    "index": idx,
                    "title": recipe.get("title"),
                    "errors": recipe_errors,
                    "would_create": False,
                    "would_skip": True,
                }
            )
            continue

        payloads.append(payload)

        for field in payload.get("_missing_required") or []:
            recipe_errors.append("missing_required_db_field")
            errors_by_code["missing_required_db_field"] += 1

        for key in payload.get("_missing_nutrition_keys") or []:
            recipe_errors.append("missing_nutrition_mapping")
            errors_by_code["missing_nutrition_mapping"] += 1

        for issue in payload.get("_ingredient_issues") or []:
            code = issue["code"]
            recipe_errors.append(code)
            errors_by_code[code] += 1

        if payload.get("_nutrition_aliases"):
            recipe_warnings.append("ui_nutrition_alias_warning")
            warnings_by_code["ui_nutrition_alias_warning"] += 1

        title = payload.get("title") or ""
        if len(title) > 80:
            recipe_warnings.append("long_title")
            warnings_by_code["long_title"] += 1

        optional_count = sum(1 for i in payload.get("ingredient_rows_plan") or [] if i.get("is_optional"))
        if optional_count > 2:
            recipe_warnings.append("optional_ingredient_warning")
            warnings_by_code["optional_ingredient_warning"] += 1

        nutrition_ok = not payload.get("_missing_nutrition_keys")
        ingredients_ok = not payload.get("_ingredient_issues")

        would_skip = bool(recipe_errors)
        would_create = not would_skip

        per_recipe.append(
            {
                "index": idx,
                "title": payload.get("title"),
                "normalized_title": payload.get("normalized_title"),
                "score": payload.get("quality_score"),
                "valid": validation.ok,
                "would_create": would_create,
                "would_skip": would_skip,
                "would_update": 0,
                "nutrition_mapped": nutrition_ok,
                "ingredients_count": len(payload.get("ingredient_rows_plan") or []),
                "errors": recipe_errors,
                "warnings": recipe_warnings,
            }
        )

    dupes = detect_existing_duplicates(session, payloads)
    for hit in dupes["batch_duplicates"]:
        errors_by_code[hit["code"]] += 1
        idx = hit["index"]
        if idx < len(per_recipe):
            per_recipe[idx]["errors"].append(hit["code"])
            per_recipe[idx]["would_create"] = False
            per_recipe[idx]["would_skip"] = True

    for hit in dupes["db_duplicates"]:
        if hit.get("code") == "db_duplicate_check_skipped":
            warnings_by_code["db_duplicate_check_skipped"] += 1
            continue
        errors_by_code[hit["code"]] += 1
        idx = hit["index"]
        if idx < len(per_recipe):
            per_recipe[idx]["errors"].append(hit["code"])
            per_recipe[idx]["db_duplicate"] = True
            per_recipe[idx]["would_create"] = False
            per_recipe[idx]["would_skip"] = True

    meal_counts = Counter(p.get("meal_type") for p in payloads)
    n = len(payloads)
    if n >= 10 and any(c / n > 0.8 for c in meal_counts.values()):
        warnings_by_code["meal_type_concentration"] += 1

    cat_counts = Counter(p.get("category") for p in payloads)
    if n >= 10 and any(c / n > 0.6 for c in cat_counts.values()):
        warnings_by_code["category_warning"] += 1

    would_create = sum(1 for r in per_recipe if r.get("would_create"))
    would_skip = sum(1 for r in per_recipe if r.get("would_skip"))
    valid = sum(1 for r in per_recipe if r.get("valid"))

    ok = not errors_by_code and would_create == len(recipes)

    mapping_summary = {
        "recipe_fields": [
            "title",
            "display_title",
            "normalized_title",
            "description",
            "meal_type",
            "category",
            "cuisine",
            "servings",
            "prep_time_minutes",
            "cooking_time_minutes",
            "difficulty",
            "source_type=import",
            "tags",
            "diets",
        ],
        "nutrition_fields": {
            "legacy_ui": [legacy for _, legacy in NUTRITION_GOLD_TO_LEGACY],
            "summary_columns": [summary for _, summary in NUTRITION_GOLD_TO_SUMMARY],
            "extras": ["nutrition_coverage_json.fiber_g", "nutrition_coverage_json.salt_g", "nutrition_coverage_json.sugar_g"],
            "ui_primary": "calories_per_serving/protein_g/fat_g/carbs_g (RecipeSummary + menu)",
            "ui_summary": "nutrition_*_per_serving when nutrition_confidence set",
        },
        "ingredient_fields": {
            "jsonb": "name (shopping_name), amount (display_amount)",
            "rows_plan": "name=shopping_name, quantity=amount, unit, category=legacy slug, is_optional",
            "shopping_list": "uses structured ingredient name + display amount",
        },
        "shopping_fields": ["shopping_name", "display_amount", "unit", "category"],
    }

    return {
        "ok": ok,
        "dry_run": dry_run,
        "records": len(recipes),
        "valid": valid,
        "would_create": would_create,
        "would_update": 0,
        "would_skip": would_skip,
        "errors_by_code": dict(errors_by_code),
        "warnings_by_code": dict(warnings_by_code),
        "per_recipe": per_recipe,
        "db_duplicate_findings": dupes["db_duplicates"],
        "batch_duplicate_findings": dupes["batch_duplicates"],
        "mapping_summary": mapping_summary,
        "not_done": [
            "DB import write",
            "image generation",
            "safe reset",
            "production DB changes",
        ],
    }


def get_mapping_summary() -> dict[str, Any]:
    """Public helper for reports/tests."""
    sample = map_gold_v3_to_db_payload(
        {
            "schema_version": SCHEMA_VERSION,
            "title": "Sample",
            "meal_type": "lunch",
            "category": "main",
            "servings": 4,
            "ingredients": [
                {
                    "name": "x",
                    "shopping_name": "x",
                    "amount": 1,
                    "unit": "╤И╤В",
                    "display_amount": "1 ╤И╤В",
                    "category": "╨╛╨▓╨╛╤Й╨╕",
                    "optional": False,
                }
            ]
            * 4,
            "steps": [{"step_number": 1, "text": "step " * 6}],
            "nutrition_per_serving": {
                "kcal": 1,
                "protein_g": 1,
                "fat_g": 1,
                "carbs_g": 1,
                "fiber_g": 1,
                "salt_g": 1,
                "sugar_g": 1,
            },
        }
    )
    return {
        "legacy_nutrition_keys": list(sample["_nutrition_mapped"].keys()),
        "nutrition_aliases": sample["_nutrition_aliases"],
    }
