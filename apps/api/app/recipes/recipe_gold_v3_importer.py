"""Stage R: Gold V3 recipe importer — dry-run planning and safe apply import."""

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


def is_gold_v3_import_recipe(tags: Any, source_type: str | None) -> bool:
    """True when an existing DB row looks like a prior Gold V3 Stage R import."""
    tag_list = tags if isinstance(tags, list) else []
    return "gold_v3" in tag_list or str(source_type or "") == DB_SOURCE_TYPE

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
        "unit": unit or "\u0433",
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
        "display_title": str(recipe.get("display_title") or recipe.get("title") or "").strip()[
            :TITLE_MAX_LEN
        ],
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
    payload["nutrition_confidence"] = "estimated"
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
                select(
                    Recipe.id,
                    Recipe.title,
                    Recipe.normalized_title,
                    Recipe.tags,
                    Recipe.source_type,
                )
            ).all()
            db_available = True
            db_index: dict[str, list[dict[str, Any]]] = {}
            for row in rows:
                rid, title, norm, tags, source_type = row[0], row[1], row[2], row[3], row[4]
                gold_v3_import = is_gold_v3_import_recipe(tags, source_type)
                for key in {normalize_recipe_title(title or ""), normalize_recipe_title(norm or "")}:
                    if key:
                        db_index.setdefault(key, []).append(
                            {
                                "id": rid,
                                "title": title,
                                "normalized_title": norm,
                                "tags": tags,
                                "source_type": source_type,
                                "is_gold_v3_import": gold_v3_import,
                            }
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
                            "existing_source_type": hit.get("source_type"),
                            "is_gold_v3_import": hit.get("is_gold_v3_import", False),
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


def _is_idempotent_full_skip(
    *,
    record_count: int,
    per_recipe: list[dict[str, Any]],
    db_duplicates: list[dict[str, Any]],
    batch_duplicates: list[dict[str, Any]],
    errors_by_code: dict[str, int],
) -> bool:
    """All valid records already imported as gold_v3 — safe to re-run dry-run/apply."""
    if record_count <= 0 or batch_duplicates:
        return False
    if errors_by_code.get("duplicate_title_in_db_unrelated"):
        return False
    blocking = {
        code: count
        for code, count in errors_by_code.items()
        if code not in {"duplicate_title_in_db"}
    }
    if blocking:
        return False

    would_create = sum(1 for r in per_recipe if r.get("would_create"))
    would_skip = sum(1 for r in per_recipe if r.get("would_skip"))
    if would_create != 0 or would_skip != record_count:
        return False

    gold_db_hits = [
        hit
        for hit in db_duplicates
        if hit.get("code") == "duplicate_title_in_db" and hit.get("is_gold_v3_import")
    ]
    if not gold_db_hits:
        return False

    covered = {hit["index"] for hit in gold_db_hits}
    valid_indices = {idx for idx, row in enumerate(per_recipe) if row.get("valid")}
    if not valid_indices or not valid_indices.issubset(covered):
        return False
    for idx in valid_indices:
        if not per_recipe[idx].get("db_duplicate"):
            return False
        if not per_recipe[idx].get("db_duplicate_gold_v3_import"):
            return False
    return True


def collect_db_snapshot(session: Any) -> dict[str, Any]:
    """Lightweight counts for pre/post import reports."""
    from sqlalchemy import func, select

    from app.models.recipe import Recipe, RecipeIngredientRow

    recipes_total = session.scalar(select(func.count()).select_from(Recipe)) or 0
    ingredients_total = session.scalar(
        select(func.count()).select_from(RecipeIngredientRow)
    ) or 0
    max_id = session.scalar(select(func.max(Recipe.id))) or 0

    gold_v3_count = 0
    generated_original_count = 0
    rows = session.execute(select(Recipe.id, Recipe.tags, Recipe.source_type)).all()
    for _rid, tags, source_type in rows:
        tag_list = tags if isinstance(tags, list) else []
        if "gold_v3" in tag_list:
            gold_v3_count += 1
        if source_type == "generated_original":
            generated_original_count += 1

    return {
        "recipes_total": int(recipes_total),
        "recipe_ingredients_total": int(ingredients_total),
        "gold_v3_count": gold_v3_count,
        "generated_original_count": generated_original_count,
        "max_recipe_id": int(max_id),
    }


def _recipe_model_fields(payload: dict[str, Any]) -> dict[str, Any]:
    from app.services.recipes.title_normalize import display_title_from

    title = payload["title"]
    display = payload.get("display_title") or display_title_from(title)
    return {
        "title": title,
        "display_title": display,
        "normalized_title": payload["normalized_title"],
        "original_title": title,
        "description": payload.get("description") or "",
        "meal_type": payload["meal_type"],
        "category": payload["category"],
        "cuisine": payload.get("cuisine"),
        "difficulty": payload.get("difficulty") or "easy",
        "cooking_time_minutes": payload.get("cooking_time_minutes") or 30,
        "prep_time_minutes": payload.get("prep_time_minutes") or 0,
        "servings": payload.get("servings") or 4,
        "calories_per_serving": payload.get("calories_per_serving"),
        "protein_g": payload.get("protein_g"),
        "fat_g": payload.get("fat_g"),
        "carbs_g": payload.get("carbs_g"),
        "fiber_g": payload.get("fiber_g"),
        "sugar_g": payload.get("sugar_g"),
        "nutrition_kcal_per_serving": payload.get("nutrition_kcal_per_serving"),
        "nutrition_protein_per_serving": payload.get("nutrition_protein_per_serving"),
        "nutrition_fat_per_serving": payload.get("nutrition_fat_per_serving"),
        "nutrition_carbs_per_serving": payload.get("nutrition_carbs_per_serving"),
        "nutrition_servings": payload.get("nutrition_servings"),
        "nutrition_source": payload.get("nutrition_source"),
        "nutrition_confidence": payload.get("nutrition_confidence"),
        "nutrition_coverage_json": payload.get("nutrition_coverage_json"),
        "source_type": payload.get("source_type") or DB_SOURCE_TYPE,
        "source_url": payload.get("source_url"),
        "is_active": payload.get("is_active", True),
        "diets": payload.get("diets") or [],
        "tags": payload.get("tags") or [],
    }


def _ingredients_for_persist(payload: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "name": row["name"],
            "quantity": row["quantity"],
            "unit": row["unit"],
            "category": row["category"],
            "is_optional": row.get("is_optional", False),
        }
        for row in payload.get("ingredient_rows_plan") or []
    ]


def apply_import_gold_v3_batch(
    recipes: list[dict[str, Any]],
    *,
    session: Any,
    require_quality_pass: bool = False,
    quality_gate_ok: bool | None = None,
) -> dict[str, Any]:
    """Insert new Gold V3 recipes only — never update or delete existing rows."""
    from app.models.recipe import Recipe
    from app.services.recipe_storage import persist_recipe_structure

    plan = plan_import_gold_v3_batch(
        recipes,
        session=session,
        dry_run=True,
        require_quality_pass=require_quality_pass,
        quality_gate_ok=quality_gate_ok,
    )

    result: dict[str, Any] = {
        "ok": False,
        "dry_run": False,
        "plan_ok": plan.get("ok"),
        "records": plan.get("records", 0),
        "created_count": 0,
        "skipped_count": 0,
        "created": [],
        "skipped": [],
        "errors_by_code": dict(plan.get("errors_by_code") or {}),
        "warnings_by_code": dict(plan.get("warnings_by_code") or {}),
        "before_snapshot": collect_db_snapshot(session),
        "after_snapshot": None,
        "old_recipes_touched": 0,
    }

    if not plan.get("ok"):
        non_dupe_errors = {
            code: count
            for code, count in (plan.get("errors_by_code") or {}).items()
            if code not in {"duplicate_title_in_db"}
        }
        if non_dupe_errors or (require_quality_pass and quality_gate_ok is False):
            result["abort_reason"] = "import_plan_not_ok"
            return result
        result["abort_reason"] = "import_plan_not_ok"
        return result

    result["idempotent_full_skip"] = bool(plan.get("idempotent_full_skip"))

    db_dupes = plan.get("db_duplicate_findings") or []
    skip_indices = {
        hit["index"]
        for hit in db_dupes
        if hit.get("code") == "duplicate_title_in_db" and hit.get("is_gold_v3_import")
    }

    per_recipe = plan.get("per_recipe") or []
    payloads: list[tuple[int, dict[str, Any]]] = []
    for idx, recipe in enumerate(recipes):
        if idx in skip_indices:
            hit = next(h for h in db_dupes if h.get("index") == idx)
            result["skipped"].append(
                {
                    "index": idx,
                    "title": recipe.get("title"),
                    "reason": "duplicate_title_in_db",
                    "existing_id": hit.get("existing_id"),
                }
            )
            continue
        if idx >= len(per_recipe) or not per_recipe[idx].get("would_create"):
            continue
        payloads.append((idx, map_gold_v3_to_db_payload(recipe)))

    if not payloads and result["skipped"]:
        result["skipped_count"] = len(result["skipped"])
        result["ok"] = True
        result["after_snapshot"] = collect_db_snapshot(session)
        if plan.get("idempotent_full_skip"):
            result["warnings_by_code"]["idempotent_full_skip"] = result["skipped_count"]
        return result

    created: list[dict[str, Any]] = []
    try:
        for idx, payload in payloads:
            recipe = Recipe(**_recipe_model_fields(payload))
            session.add(recipe)
            session.flush()
            persist_recipe_structure(
                session,
                recipe,
                ingredients=_ingredients_for_persist(payload),
                steps=payload.get("steps_jsonb") or [],
                tags=payload.get("tags") or [],
                allergens=payload.get("allergens_plan") or [],
                restrictions=payload.get("restrictions_plan") or [],
            )
            created.append(
                {
                    "index": idx,
                    "id": recipe.id,
                    "title": recipe.title,
                    "normalized_title": recipe.normalized_title,
                }
            )
        session.commit()
    except Exception as exc:
        session.rollback()
        result["abort_reason"] = "db_write_failed"
        result["error"] = str(exc)
        return result

    result["created"] = created
    result["created_count"] = len(created)
    result["skipped_count"] = len(result["skipped"])
    result["after_snapshot"] = collect_db_snapshot(session)
    valid_count = sum(1 for r in per_recipe if r.get("valid"))
    result["ok"] = (len(created) + result["skipped_count"]) == valid_count and valid_count > 0
    if created and result["skipped_count"]:
        result["warnings_by_code"]["partial_idempotent_skip"] = result["skipped_count"]
    return result


def plan_import_gold_v3_batch(
    recipes: list[dict[str, Any]],
    *,
    session: Any | None = None,
    dry_run: bool = True,
    require_quality_pass: bool = False,
    quality_gate_ok: bool | None = None,
) -> dict[str, Any]:
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
        code = (
            "duplicate_title_in_db"
            if hit.get("is_gold_v3_import")
            else "duplicate_title_in_db_unrelated"
        )
        errors_by_code[code] += 1
        idx = hit["index"]
        if idx < len(per_recipe):
            per_recipe[idx]["errors"].append(code)
            per_recipe[idx]["db_duplicate"] = True
            per_recipe[idx]["db_duplicate_gold_v3_import"] = bool(hit.get("is_gold_v3_import"))
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

    idempotent_full_skip = _is_idempotent_full_skip(
        record_count=len(recipes),
        per_recipe=per_recipe,
        db_duplicates=dupes["db_duplicates"],
        batch_duplicates=dupes["batch_duplicates"],
        errors_by_code=dict(errors_by_code),
    )
    if idempotent_full_skip:
        dup_count = errors_by_code.pop("duplicate_title_in_db", 0)
        if dup_count:
            warnings_by_code["idempotent_duplicate_in_db"] = dup_count
        ok = True
    else:
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
        "idempotent_full_skip": idempotent_full_skip,
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
        "not_done": (
            [
                "DB import write",
                "safe reset",
                "old recipe updates",
                "old recipe deletes",
            ]
            if dry_run
            else [
                "safe reset",
                "old recipe updates",
                "old recipe deletes",
            ]
        ),
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
                    "unit": "\u0448\u0442",
                    "display_amount": "1 \u0448\u0442",
                    "category": "\u043e\u0432\u043e\u0449\u0438",
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
