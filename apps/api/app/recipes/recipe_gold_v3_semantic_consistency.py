"""Stage Q4.1: semantic consistency between recipe text and ingredients/steps."""

from __future__ import annotations

import re
from typing import Any, Literal

Severity = Literal["error", "warning"]

_CHICKEN_MARKERS = (
    "куриц",
    "куриное",
    "куриная",
    "куриный",
    "куриной",
    "куриную",
    "грудк",
    "индейк",
)
_MINCE_STEP_RE = re.compile(
    r"(измельч\w*\s+.{0,40}мяс|мясоруб|пропуст\w*\s+.{0,30}мясоруб|"
    r"мясо\s+.{0,30}фарш|фарш\s+.{0,30}мяс)",
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


def _recipe_text_blob(recipe: dict[str, Any]) -> str:
    parts = [
        str(recipe.get("title") or ""),
        str(recipe.get("display_title") or ""),
        str(recipe.get("description") or ""),
    ]
    return _normalize_blob(" ".join(parts))


def _ingredient_names(recipe: dict[str, Any]) -> list[str]:
    names: list[str] = []
    for ing in recipe.get("ingredients") or []:
        if not isinstance(ing, dict):
            continue
        for key in ("shopping_name", "name"):
            val = str(ing.get(key) or "").strip()
            if val:
                names.append(_normalize_blob(val))
    return names


def _steps_blob(recipe: dict[str, Any]) -> str:
    parts: list[str] = []
    for step in recipe.get("steps") or []:
        if isinstance(step, dict):
            parts.append(str(step.get("text") or ""))
        else:
            parts.append(str(step))
    return _normalize_blob(" ".join(parts))


def _content_blob(recipe: dict[str, Any]) -> str:
    return " ".join([*_ingredient_names(recipe), _steps_blob(recipe)])


def _contains_any(blob: str, markers: tuple[str, ...]) -> bool:
    return any(marker in blob for marker in markers)


def _has_mince_preparation(steps_blob: str) -> bool:
    return bool(_MINCE_STEP_RE.search(steps_blob))


def check_semantic_consistency(
    recipe: dict[str, Any],
    *,
    recipe_index: int = 0,
) -> list[dict[str, Any]]:
    """Ensure title/display_title/description align with ingredients and steps."""
    findings: list[dict[str, Any]] = []
    text = _recipe_text_blob(recipe)
    content = _content_blob(recipe)
    steps = _steps_blob(recipe)
    ing_blob = " ".join(_ingredient_names(recipe))

    if not text.strip():
        return findings

    if "тофу" in text and "тофу" not in content:
        findings.append(
            _issue(
                "semantic_tofu_mismatch",
                "error",
                "text mentions tofu but ingredients/steps do not",
                path="title",
                recipe_index=recipe_index,
            )
        )

    if "кальмар" in text:
        if "кальмар" not in content:
            findings.append(
                _issue(
                    "semantic_squid_mismatch",
                    "error",
                    "text mentions squid but ingredients/steps do not",
                    path="title",
                    recipe_index=recipe_index,
                )
            )
        if "кревет" in ing_blob and "кальмар" not in ing_blob:
            findings.append(
                _issue(
                    "semantic_squid_vs_shrimp",
                    "error",
                    "text mentions squid but ingredients contain shrimp",
                    path="ingredients",
                    recipe_index=recipe_index,
                )
            )

    if "кревет" in text and "кревет" not in content:
        findings.append(
            _issue(
                "semantic_shrimp_mismatch",
                "error",
                "text mentions shrimp but ingredients/steps do not",
                path="title",
                recipe_index=recipe_index,
            )
        )

    if "куриц" in text and not _contains_any(content, _CHICKEN_MARKERS):
        findings.append(
            _issue(
                "semantic_chicken_mismatch",
                "error",
                "text mentions chicken but ingredients/steps do not",
                path="title",
                recipe_index=recipe_index,
            )
        )

    if re.search(r"свини|свиной|свиным", text) and "свини" not in content:
        findings.append(
            _issue(
                "semantic_pork_mismatch",
                "error",
                "text mentions pork but ingredients/steps do not",
                path="title",
                recipe_index=recipe_index,
            )
        )

    if "фарш" in text and "фарш" not in content and not _has_mince_preparation(steps):
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
