from __future__ import annotations

from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.recipes.v2_models import (
    CanonicalArchiveFallback,
    CanonicalLegacyMapping,
    CanonicalRecipe,
    CanonicalRecipeFavorite,
    CanonicalRecipeIngredient,
    CanonicalRecipeStep,
    CanonicalRecipeVersion,
)
from app.v2.uuid7 import uuid7_str


def _payload(version: CanonicalRecipeVersion) -> dict[str, Any]:
    payload = dict(version.gold_v3_payload_json or {})
    nutrition = dict(version.nutrition_projection_json or {})
    return {
        **payload,
        "recipe_id": version.recipe_id,
        "recipe_version_id": version.recipe_version_id,
        "version": version.version_number,
        "title": payload.get("title", version.title),
        "description": payload.get("description", version.description or ""),
        "servings": version.servings,
        "yield_amount": version.yield_amount,
        "yield_unit": version.yield_unit,
        "nutrition_per_serving": nutrition.get("nutrition_per_serving", nutrition),
        "lifecycle_status": version.lifecycle_status,
        "quality_score": version.quality_score,
        "media": payload.get("media", []),
    }


def _version_items(db: Session, version: CanonicalRecipeVersion) -> tuple[list[dict], list[dict]]:
    ingredients = db.scalars(
        select(CanonicalRecipeIngredient)
        .where(CanonicalRecipeIngredient.recipe_version_id == version.recipe_version_id)
        .order_by(CanonicalRecipeIngredient.sort_order)
    ).all()
    steps = db.scalars(
        select(CanonicalRecipeStep)
        .where(CanonicalRecipeStep.recipe_version_id == version.recipe_version_id)
        .order_by(CanonicalRecipeStep.step_number)
    ).all()
    ingredient_payload = [
        {
            "display_name": item.display_text,
            "shopping_name": item.shopping_name or item.display_text,
            "food_identity": item.food_identity_key,
            "mapping_status": item.mapping_status,
            "quantity": item.quantity,
            "unit": item.unit,
            "normalized_quantity": item.normalized_quantity,
            "normalized_unit": item.normalized_unit,
            "quantity_mode": item.quantity_mode,
            "optional": item.optional,
            "process_state": item.process_state or item.preparation_expectation,
            "mapping_provenance": item.mapping_provenance_json or {},
        }
        for item in ingredients
    ]
    step_payload = [
        {"step_number": step.step_number, "instruction": step.instruction, "process": step.expected_process_json or {}}
        for step in steps
    ]
    return ingredient_payload, step_payload


def published_version(db: Session, recipe_id: str) -> CanonicalRecipeVersion | None:
    return db.scalars(
        select(CanonicalRecipeVersion)
        .where(
            CanonicalRecipeVersion.recipe_id == recipe_id,
            CanonicalRecipeVersion.lifecycle_status == "PUBLISHED",
        )
        .order_by(CanonicalRecipeVersion.version_number.desc())
    ).first()


def recipe_detail(db: Session, recipe: CanonicalRecipe, version: CanonicalRecipeVersion) -> dict[str, Any]:
    payload = _payload(version)
    ingredients, steps = _version_items(db, version)
    return {
        **payload,
        "canonical_key": recipe.canonical_key,
        "ingredients": ingredients,
        "steps": steps,
        "provenance": version.source_provenance_json or {},
        "validation": {"score": version.quality_score, **(version.gold_v3_validation_json or {})},
        "safety_state": (version.safety_claims_json or {}).get("state", "UNKNOWN"),
    }


def resolve_identifier(db: Session, identifier: str) -> tuple[CanonicalRecipe | None, CanonicalRecipeVersion | None, dict | None]:
    try:
        recipe = db.get(CanonicalRecipe, identifier)
    except (TypeError, ValueError):
        recipe = None
    if recipe is not None:
        return recipe, published_version(db, recipe.recipe_id), None
    if not identifier.isdigit():
        return None, None, None
    mapping = db.scalar(select(CanonicalLegacyMapping).where(CanonicalLegacyMapping.legacy_recipe_id == int(identifier)))
    if mapping and mapping.canonical_recipe_id:
        recipe = db.get(CanonicalRecipe, mapping.canonical_recipe_id)
        version = db.get(CanonicalRecipeVersion, mapping.canonical_version_id) if mapping.canonical_version_id else (published_version(db, recipe.recipe_id) if recipe else None)
        return recipe, version, None
    archive = db.get(CanonicalArchiveFallback, int(identifier))
    return None, None, archive.archive_payload_json if archive else None


def list_published(db: Session, *, query: str | None, limit: int, offset: int) -> tuple[list[dict], int]:
    base = (
        select(CanonicalRecipe, CanonicalRecipeVersion)
        .join(CanonicalRecipeVersion, CanonicalRecipeVersion.recipe_id == CanonicalRecipe.recipe_id)
        .where(CanonicalRecipeVersion.lifecycle_status == "PUBLISHED")
    )
    if query:
        needle = f"%{query.strip()}%"
        base = base.where(or_(CanonicalRecipeVersion.title.ilike(needle), CanonicalRecipeVersion.description.ilike(needle)))
    rows = db.execute(base.order_by(CanonicalRecipe.updated_at.desc()).offset(offset).limit(limit)).all()
    count_query = select(func.count()).select_from(base.subquery())
    return [recipe_detail(db, recipe, version) for recipe, version in rows], int(db.scalar(count_query) or 0)


def favorite(db: Session, *, account_id: str, recipe: CanonicalRecipe, version: CanonicalRecipeVersion, idempotency_key: str) -> dict[str, Any]:
    existing = db.scalar(
        select(CanonicalRecipeFavorite).where(
            CanonicalRecipeFavorite.account_id == account_id,
            CanonicalRecipeFavorite.recipe_id == recipe.recipe_id,
        )
    )
    if existing is None:
        existing = CanonicalRecipeFavorite(
            favorite_id=uuid7_str(),
            account_id=account_id,
            recipe_id=recipe.recipe_id,
            version_id=version.recipe_version_id,
            idempotency_key=idempotency_key,
        )
        db.add(existing)
        db.flush()
    return {"recipe_id": recipe.recipe_id, "recipe_version_id": version.recipe_version_id, "is_favorited": True}
