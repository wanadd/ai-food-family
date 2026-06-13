"""Stage Q4.1: semantic consistency between recipe text and ingredients/steps."""

from __future__ import annotations

import re
from typing import Any, Literal

Severity = Literal["error", "warning"]

STEM_TOFU = "тофу"
STEM_SHRIMP = "кревет"
STEM_SQUID = "кальмар"
STEM_PORK = "свин"
STEM_CHICKEN = ("куриц", "курин", "кур")
STEM_MINCE = ("фарш", "фрикадел")
MEAT_STEMS = ("свин", "говядин", "куриц", "курин", "кур", "индейк", "баран", "телят", "бекон", "ветчин")

_MINCE_STEP_RE = re.compile(
    r"(измельч\w*|пропуст\w*\s+.{0,30}мясоруб|мясоруб|"
    r"мясо\s+.{0,30}фарш|фарш\s+.{0,30}мяс|"
    r".{0,20}в\s+фарш)",
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


def _normalize_blob(text: str) -> str:
    return str(text or "").casefold().replace("ё", "е")


def _user_facing_text(recipe: dict[str, Any]) -> str:
    parts = [
        str(recipe.get("title") or ""),
        str(recipe.get("display_title") or ""),
        str(recipe.get("description") or ""),
    ]
    return _normalize_blob(" ".join(parts))


def _ingredient_text_parts(recipe: dict[str, Any]) -> list[str]:
    parts: list[str] = []
    for ing in recipe.get("ingredients") or []:
        if isinstance(ing, str):
            val = ing.strip()
            if val:
                parts.append(val)
            continue
        if not isinstance(ing, dict):
            continue
        for key in ("shopping_name", "name", "title", "product"):
            val = str(ing.get(key) or "").strip()
            if val:
                parts.append(val)
                break
    return parts


def _step_text_parts(recipe: dict[str, Any]) -> list[str]:
    parts: list[str] = []
    for step in recipe.get("steps") or []:
        if isinstance(step, dict):
            parts.append(str(step.get("text") or step.get("description") or ""))
        else:
            parts.append(str(step))
    return parts


def _ingredient_step_text(recipe: dict[str, Any]) -> str:
    return _normalize_blob(" ".join([*_ingredient_text_parts(recipe), *_step_text_parts(recipe)]))


def _steps_text(recipe: dict[str, Any]) -> str:
    return _normalize_blob(" ".join(_step_text_parts(recipe)))


def _contains_stem(blob: str, stem: str | tuple[str, ...]) -> bool:
    if isinstance(stem, str):
        return stem in blob
    return any(part in blob for part in stem)


def _has_mince_evidence(recipe: dict[str, Any], ingredient_step_text: str) -> bool:
    if _contains_stem(ingredient_step_text, STEM_MINCE):
        return True
    steps = _steps_text(recipe)
    if _has_mince_preparation(steps):
        return True
    if _contains_stem(ingredient_step_text, MEAT_STEMS) and _has_mince_preparation(steps):
        return True
    return bool(
        _contains_stem(ingredient_step_text, MEAT_STEMS)
        and re.search(r"(измельч|мясоруб|в\s+фарш)", steps)
    )


def _has_mince_preparation(steps_blob: str) -> bool:
    return bool(_MINCE_STEP_RE.search(steps_blob))


def check_semantic_consistency(
    recipe: dict[str, Any],
    *,
    recipe_index: int = 0,
) -> list[dict[str, Any]]:
    """Ensure title/display_title/description align with ingredients and steps."""
    findings: list[dict[str, Any]] = []
    user_text = _user_facing_text(recipe)
    ingredient_step_text = _ingredient_step_text(recipe)

    if not user_text.strip():
        return findings

    if _contains_stem(user_text, STEM_TOFU) and not _contains_stem(ingredient_step_text, STEM_TOFU):
        findings.append(
            _issue(
                "semantic_tofu_mismatch",
                "error",
                "text mentions tofu but ingredients/steps do not",
                path="title",
                recipe_index=recipe_index,
            )
        )

    if _contains_stem(user_text, STEM_SQUID):
        if not _contains_stem(ingredient_step_text, STEM_SQUID):
            findings.append(
                _issue(
                    "semantic_squid_mismatch",
                    "error",
                    "text mentions squid but ingredients/steps do not",
                    path="title",
                    recipe_index=recipe_index,
                )
            )
        if (
            _contains_stem(ingredient_step_text, STEM_SHRIMP)
            and not _contains_stem(ingredient_step_text, STEM_SQUID)
        ):
            findings.append(
                _issue(
                    "semantic_squid_vs_shrimp",
                    "error",
                    "text mentions squid but ingredients/steps contain shrimp",
                    path="ingredients",
                    recipe_index=recipe_index,
                )
            )

    if _contains_stem(user_text, STEM_SHRIMP):
        if not _contains_stem(ingredient_step_text, STEM_SHRIMP):
            findings.append(
                _issue(
                    "semantic_shrimp_mismatch",
                    "error",
                    "text mentions shrimp but ingredients/steps do not",
                    path="title",
                    recipe_index=recipe_index,
                )
            )
        if (
            _contains_stem(ingredient_step_text, STEM_SQUID)
            and not _contains_stem(ingredient_step_text, STEM_SHRIMP)
        ):
            findings.append(
                _issue(
                    "semantic_shrimp_vs_squid",
                    "error",
                    "text mentions shrimp but ingredients/steps contain squid",
                    path="ingredients",
                    recipe_index=recipe_index,
                )
            )

    if _contains_stem(user_text, STEM_CHICKEN) and not _contains_stem(ingredient_step_text, STEM_CHICKEN):
        findings.append(
            _issue(
                "semantic_chicken_mismatch",
                "error",
                "text mentions chicken but ingredients/steps do not",
                path="title",
                recipe_index=recipe_index,
            )
        )

    if _contains_stem(user_text, STEM_PORK) and not _contains_stem(ingredient_step_text, STEM_PORK):
        findings.append(
            _issue(
                "semantic_pork_mismatch",
                "error",
                "text mentions pork but ingredients/steps do not",
                path="title",
                recipe_index=recipe_index,
            )
        )

    if _contains_stem(user_text, STEM_MINCE) and not _has_mince_evidence(recipe, ingredient_step_text):
        findings.append(
            _issue(
                "semantic_mince_mismatch",
                "error",
                "text mentions mince but ingredients/steps lack mince or grinding step",
                path="title",
                recipe_index=recipe_index,
            )
        )

    return findings
