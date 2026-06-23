"""Load/save recipes with normalized ingredient/step rows and JSONB fallback."""

from __future__ import annotations

import re
from typing import Any

from sqlalchemy.orm import Session

from app.models.recipe import (
    Recipe,
    RecipeAllergenRow,
    RecipeIngredientRow,
    RecipeRestrictionRow,
    RecipeStepRow,
    RecipeTagRow,
)
from app.services.amount_parser import parse_amount
from app.services.ingredient_format import (
    format_ingredient_amount,
    is_to_taste,
    normalize_unit_display,
    sanitize_amount_text,
)
from app.services.shopping_categories import infer_category
from app.recipes.product_taxonomy import SHOPPING_CATEGORIES_V2, legacy_shopping_slug


def _resolve_ingredient_category(name: str, category_hint: str | None) -> str:
    hint = (category_hint or "").strip()
    if hint in SHOPPING_CATEGORIES_V2:
        return legacy_shopping_slug(hint)
    return infer_category(name, hint or None)


def _parse_legacy_amount(amount_str: str) -> tuple[str, str]:
    val, unit = parse_amount(amount_str)
    if val is None:
        return amount_str.strip() or "1", "шт"
    qty = str(int(val)) if val == int(val) else str(val)
    return qty, unit or "шт"


def get_structured_ingredients(recipe: Recipe) -> list[dict[str, Any]]:
    if recipe.ingredient_rows:
        return [
            {
                "name": row.name,
                "quantity": row.quantity,
                "unit": normalize_unit_display(row.unit),
                "category": _resolve_ingredient_category(row.name, row.category),
                "is_optional": row.is_optional,
                "notes": row.notes,
                "is_to_taste": is_to_taste(
                    row.quantity,
                    quantity_mode=getattr(row, "quantity_mode", None),
                    is_to_taste_flag=bool(getattr(row, "is_to_taste", False)),
                ),
                "amount": format_ingredient_amount(
                    row.quantity,
                    row.unit,
                    quantity_mode=getattr(row, "quantity_mode", None),
                    is_to_taste_flag=bool(getattr(row, "is_to_taste", False)),
                    quantity_text=getattr(row, "quantity_text", None),
                ),
            }
            for row in recipe.ingredient_rows
        ]
    result: list[dict[str, Any]] = []
    for raw in recipe.ingredients or []:
        if isinstance(raw, dict):
            name = str(raw.get("name", "")).strip()
            # Legacy JSONB usually only has name + amount; use it as-is,
            # only sanitising wrongly-appended "шт" (e.g. "по вкусу шт").
            amount = sanitize_amount_text(str(raw.get("amount", "")))
            qty, unit = _parse_legacy_amount(amount or "1")
            category = _resolve_ingredient_category(name, raw.get("category"))
            result.append(
                {
                    "name": name,
                    "quantity": qty,
                    "unit": unit,
                    "category": category,
                    "is_optional": bool(raw.get("is_optional", False)),
                    "notes": raw.get("notes"),
                    "amount": amount,
                }
            )
    return result


def get_structured_steps(recipe: Recipe) -> list[str]:
    if recipe.step_rows:
        return [row.text for row in sorted(recipe.step_rows, key=lambda r: r.step_number)]
    steps = recipe.steps or []
    return [str(s) for s in steps]


def get_tags(recipe: Recipe) -> list[str]:
    tags: list[str] = []
    seen: set[str] = set()
    for row in getattr(recipe, "tag_rows", None) or []:
        tag = str(getattr(row, "tag", "")).strip()
        if tag and tag not in seen:
            seen.add(tag)
            tags.append(tag)
    for raw in getattr(recipe, "tags", None) or []:
        tag = str(raw).strip()
        if tag and tag not in seen:
            seen.add(tag)
            tags.append(tag)
    return tags


def get_allergens(recipe: Recipe) -> list[str]:
    if recipe.allergen_rows:
        return [row.allergen for row in recipe.allergen_rows]
    return []


def get_restrictions(recipe: Recipe) -> list[str]:
    if recipe.restriction_rows:
        return [row.restriction for row in recipe.restriction_rows]
    return list(recipe.diets or [])


def servings_base(recipe: Recipe) -> int:
    return max(1, recipe.servings or 4)


def scale_ingredients(
    recipe: Recipe, target_servings: int
) -> list[dict[str, Any]]:
    base = servings_base(recipe)
    factor = target_servings / base
    scaled: list[dict[str, Any]] = []
    for ing in get_structured_ingredients(recipe):
        if ing.get("is_to_taste"):
            # Don't scale or re-unit "по вкусу" — keep the honest amount.
            scaled.append({**ing})
            continue
        try:
            qty_val = float(str(ing["quantity"]).replace(",", "."))
            new_qty = qty_val * factor
            qty_str = (
                str(int(new_qty))
                if new_qty == int(new_qty)
                else f"{new_qty:.1f}".rstrip("0").rstrip(".")
            )
        except ValueError:
            qty_str = str(ing["quantity"])
        unit = ing["unit"]
        scaled.append(
            {
                **ing,
                "quantity": qty_str,
                "amount": format_ingredient_amount(qty_str, unit),
            }
        )
    return scaled


def sync_jsonb_from_rows(recipe: Recipe) -> None:
    """Keep legacy JSONB in sync for older clients."""
    recipe.ingredients = [
        {"name": i["name"], "amount": i["amount"]} for i in get_structured_ingredients(recipe)
    ]
    recipe.steps = get_structured_steps(recipe)
    recipe.tags = get_tags(recipe)


def persist_recipe_structure(
    db: Session,
    recipe: Recipe,
    *,
    ingredients: list[dict[str, Any]] | None = None,
    steps: list[str] | None = None,
    tags: list[str] | None = None,
    allergens: list[str] | None = None,
    restrictions: list[str] | None = None,
) -> None:
    if ingredients is not None:
        recipe.ingredient_rows.clear()
        for ing in ingredients:
            name = str(ing.get("name", "")).strip()
            if not name:
                continue
            qty = str(ing.get("quantity", "1"))
            unit = str(ing.get("unit", "шт"))
            if "amount" in ing and not ing.get("quantity"):
                qty, unit = _parse_legacy_amount(str(ing["amount"]))
            category = ing.get("category") or infer_category(name, None)
            recipe.ingredient_rows.append(
                RecipeIngredientRow(
                    name=name,
                    quantity=qty,
                    unit=unit,
                    category=category,
                    is_optional=bool(ing.get("is_optional", False)),
                    notes=ing.get("notes"),
                )
            )
        recipe.ingredients = [
            {
                "name": i.name,
                "amount": format_ingredient_amount(
                    i.quantity,
                    i.unit,
                    quantity_mode=getattr(i, "quantity_mode", None),
                    is_to_taste_flag=bool(getattr(i, "is_to_taste", False)),
                    quantity_text=getattr(i, "quantity_text", None),
                ),
            }
            for i in recipe.ingredient_rows
        ]

    if steps is not None:
        recipe.step_rows.clear()
        for num, text in enumerate(steps, start=1):
            recipe.step_rows.append(RecipeStepRow(step_number=num, text=text.strip()))
        recipe.steps = steps

    if tags is not None:
        recipe.tag_rows.clear()
        for tag in tags:
            t = str(tag).strip()
            if t:
                recipe.tag_rows.append(RecipeTagRow(tag=t))
        recipe.tags = tags

    if allergens is not None:
        recipe.allergen_rows.clear()
        for allergen in allergens:
            a = str(allergen).strip()
            if a:
                recipe.allergen_rows.append(RecipeAllergenRow(allergen=a))

    if restrictions is not None:
        recipe.restriction_rows.clear()
        for restriction in restrictions:
            r = str(restriction).strip()
            if r:
                recipe.restriction_rows.append(RecipeRestrictionRow(restriction=r))
        recipe.diets = restrictions


def normalize_name_key(name: str) -> str:
    return re.sub(r"\s+", " ", name.strip().lower())


def aggregate_ingredients_for_shopping(
    items: list[dict[str, Any]],
) -> list[dict[str, str]]:
    """Merge only identical name + unit + category."""
    merged: dict[tuple[str, str, str], dict[str, Any]] = {}
    for ing in items:
        name = str(ing.get("name", "")).strip()
        if not name:
            continue
        unit = str(ing.get("unit", "шт"))
        category = str(ing.get("category") or infer_category(name, None))
        key = (normalize_name_key(name), unit, category)
        try:
            qty = float(str(ing.get("quantity", "1")).replace(",", "."))
        except ValueError:
            qty = 1.0
        if key in merged:
            try:
                merged[key]["quantity"] = str(
                    float(merged[key]["quantity"].replace(",", ".")) + qty
                )
            except ValueError:
                pass
        else:
            merged[key] = {
                "name": name,
                "quantity": str(int(qty)) if qty == int(qty) else str(qty),
                "unit": unit,
                "category": category,
            }
    return [
        {
            "name": v["name"],
            "amount": f"{v['quantity']} {v['unit']}".strip(),
            "category": v["category"],
        }
        for v in merged.values()
    ]
