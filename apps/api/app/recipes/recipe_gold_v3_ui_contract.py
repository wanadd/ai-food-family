"""Stage Q4: UI text contract checks for Gold V3 recipes."""

from __future__ import annotations

import re
from typing import Any, Literal

from app.recipes.recipe_gold_v3_schema import ALLOWED_CATEGORIES, ALLOWED_MEAL_TYPES

Severity = Literal["error", "warning"]

ALLOWED_NUTRITION_CONFIDENCE = frozenset(
    {"exact", "estimated", "low_confidence", "unavailable"}
)
FORBIDDEN_NUTRITION_CONFIDENCE = frozenset(
    {"high", "medium", "low", "confident", "approximate"}
)

TITLE_MAX_LEN = 64
DISPLAY_TITLE_MIN_LEN = 18
DISPLAY_TITLE_MAX_LEN = 38
DESCRIPTION_MIN_LEN = 90
DESCRIPTION_MAX_LEN = 170

RAW_CATEGORY_SLUGS = frozenset(
    {"side", "main", "soup", "salad", "breakfast", "lunch", "dinner", "snack"}
)

TECHNICAL_TITLE_RE = re.compile(
    r"(#+\s*\d+|\bpro\b|\bhigh\s+protein\b|\bpre-workout\b|\bai\b|\bgold\b)",
    re.IGNORECASE,
)


def _issue(
    code: str,
    severity: Severity,
    message: str,
    *,
    path: str,
    recipe_index: int,
) -> dict[str, Any]:
    return {
        "code": code,
        "severity": severity,
        "message": message,
        "path": path,
        "recipe_index": recipe_index,
    }


def _contains_raw_slug(text: str) -> bool:
    lower = str(text or "").casefold()
    return any(re.search(rf"\b{re.escape(slug)}\b", lower) for slug in RAW_CATEGORY_SLUGS)


def check_ui_text_contract(recipe: dict[str, Any], *, recipe_index: int = 0) -> list[dict[str, Any]]:
    """Validate title/display_title/description/category/confidence for Telegram UI."""
    findings: list[dict[str, Any]] = []

    title = str(recipe.get("title") or "").strip()
    display_title = str(recipe.get("display_title") or "").strip()
    description = str(recipe.get("description") or "").strip()
    category = str(recipe.get("category") or "").strip()
    meal_type = str(recipe.get("meal_type") or "").strip()
    confidence = str(
        recipe.get("nutrition_confidence")
        or (recipe.get("nutrition_per_serving") or {}).get("confidence")
        or ""
    ).strip()

    if not title or len(title) > TITLE_MAX_LEN:
        findings.append(
            _issue(
                "title_length_ok",
                "error",
                f"title must be 1-{TITLE_MAX_LEN} characters",
                path="title",
                recipe_index=recipe_index,
            )
        )

    if not display_title:
        findings.append(
            _issue(
                "display_title_card_safe",
                "error",
                "display_title is required for catalog cards",
                path="display_title",
                recipe_index=recipe_index,
            )
        )
    elif len(display_title) < DISPLAY_TITLE_MIN_LEN or len(display_title) > DISPLAY_TITLE_MAX_LEN:
        findings.append(
            _issue(
                "display_title_card_safe",
                "error",
                f"display_title must be {DISPLAY_TITLE_MIN_LEN}-{DISPLAY_TITLE_MAX_LEN} characters",
                path="display_title",
                recipe_index=recipe_index,
            )
        )

    for field_name, value in (("title", title), ("display_title", display_title), ("description", description)):
        if TECHNICAL_TITLE_RE.search(value):
            findings.append(
                _issue(
                    "no_technical_title",
                    "error",
                    f"{field_name} contains technical/forbidden tokens",
                    path=field_name,
                    recipe_index=recipe_index,
                )
            )
        if _contains_raw_slug(value):
            findings.append(
                _issue(
                    "no_technical_title",
                    "error",
                    f"{field_name} contains raw category/meal slug",
                    path=field_name,
                    recipe_index=recipe_index,
                )
            )

    if description and (len(description) < DESCRIPTION_MIN_LEN or len(description) > DESCRIPTION_MAX_LEN):
        findings.append(
            _issue(
                "description_length_ok",
                "warning",
                f"description should be {DESCRIPTION_MIN_LEN}-{DESCRIPTION_MAX_LEN} characters",
                path="description",
                recipe_index=recipe_index,
            )
        )

    if category and category not in ALLOWED_CATEGORIES:
        findings.append(
            _issue(
                "category_allowed",
                "error",
                f"category must be one of {sorted(ALLOWED_CATEGORIES)}",
                path="category",
                recipe_index=recipe_index,
            )
        )

    if meal_type and meal_type not in ALLOWED_MEAL_TYPES:
        findings.append(
            _issue(
                "meal_type_allowed",
                "error",
                f"meal_type must be one of {sorted(ALLOWED_MEAL_TYPES)}",
                path="meal_type",
                recipe_index=recipe_index,
            )
        )

    if confidence:
        if confidence in FORBIDDEN_NUTRITION_CONFIDENCE or confidence not in ALLOWED_NUTRITION_CONFIDENCE:
            findings.append(
                _issue(
                    "nutrition_confidence_allowed",
                    "error",
                    f"nutrition_confidence must be one of {sorted(ALLOWED_NUTRITION_CONFIDENCE)}",
                    path="nutrition_confidence",
                    recipe_index=recipe_index,
                )
            )

    hero = recipe.get("hero_image_url")
    if not hero:
        findings.append(
            _issue(
                "catalog_ready_candidate",
                "warning",
                "recipe needs hero_image_url before default catalog visibility",
                path="hero_image_url",
                recipe_index=recipe_index,
            )
        )

    return findings
