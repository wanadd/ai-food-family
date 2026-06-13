"""Stage G/H: originality + batch quality gate for Gold V3 recipes (no DB)."""

from __future__ import annotations

import re
import string
from collections import Counter
from typing import Any, Literal

from app.recipes.recipe_gold_v3_postprocess import postprocess_generated_recipe
from app.recipes.recipe_gold_v3_schema import ALLOWED_UNITS
from app.recipes.recipe_gold_v3_ui_contract import check_ui_text_contract
from app.recipes.recipe_gold_v3_validation import validate_recipe_gold_v3

Severity = Literal["error", "warning"]
Recommendation = Literal["PASS", "FAIL"]

TITLE_CLOSE_TO_SIGNAL = 0.72
TITLE_CLOSE_TO_RECIPE = 0.80
INGREDIENT_DUPLICATE_HARD = 0.85
INGREDIENT_OVERLAP_WARN = 0.65
STEPS_CLOSE_HARD = 0.75
TITLE_MODERATE_WARN = 0.55
CATEGORY_OVERCONCENTRATION = 0.60
MEAL_TYPE_WARN = 0.80
MAIN_INGREDIENT_HARD = 0.60

RECIPE_LEAK_FIELDS = frozenset(
    {
        "source_url",
        "original_title",
        "original_steps",
        "source_title",
        "source_steps",
        "copied_source_text",
    }
)
SIGNAL_LEAK_FIELDS = frozenset(
    {"source_url", "original_steps", "source_steps", "steps", "copied_source_text"}
)
SIGNAL_SOURCE_TITLE_FIELDS = ("original_title", "source_title", "raw_title", "title")

# Russian stop words via Unicode escapes (ASCII-safe source file).
STOP_WORDS = frozenset(
    {
        "\u0441",
        "\u0441\u043e",
        "\u0438\u0437",
        "\u043d\u0430",
        "\u0438",
        "\u0432",
        "\u0432\u043e",
        "\u043f\u043e",
        "\u0434\u043b\u044f",
        "\u043f\u043e\u0434",
        "\u0431\u0435\u0437",
        "\u043d\u0430\u0434",
        "\u043f\u0440\u0438",
        "\u043a\u0430\u043a",
        "\u0438\u043b\u0438",
    }
)

# Ingredient family markers (Unicode escapes, longest match wins by order).
FAMILY_MARKERS: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "seafood",
        (
            "\u043a\u0430\u043b\u044c\u043c\u0430\u0440",
            "\u043c\u043e\u0440\u0435\u043f\u0440\u043e\u0434\u0443\u043a\u0442",
            "\u043a\u0440\u0435\u0432\u0435\u0442",
            "\u043c\u0438\u0434\u0438",
            "\u043a\u0440\u0435\u0432\u0435\u0442\u043a",
        ),
    ),
    (
        "fish",
        (
            "\u0440\u044b\u0431",
            "\u043b\u043e\u0441\u043e\u0441",
            "\u0442\u0443\u043d\u0435\u0446",
            "\u0442\u0440\u0435\u0441\u043a",
            "\u0441\u0435\u043c\u0433",
            "\u0433\u043e\u0440\u0431\u0443\u0448",
            "\u0437\u0443\u0431\u0430\u0442\u043a",
        ),
    ),
    (
        "chicken",
        (
            "\u043a\u0443\u0440\u0438\u0446",
            "\u043a\u0443\u0440\u0438\u043d",
            "\u0433\u0440\u0443\u0434\u043a",
            "\u0438\u043d\u0434\u0435\u0439\u043a",
        ),
    ),
    (
        "pork",
        (
            "\u0441\u0432\u0438\u043d\u0438\u043d",
            "\u0441\u0432\u0438\u043d",
            "\u0431\u0435\u043a\u043e\u043d",
            "\u0432\u0435\u0442\u0447\u0438\u043d",
            "\u0444\u0430\u0440\u0448",
        ),
    ),
    (
        "beef",
        (
            "\u0433\u043e\u0432\u044f\u0434\u0438\u043d",
            "\u0442\u0435\u043b\u044f\u0442\u0438\u043d",
            "\u0431\u0430\u0440\u0430\u043d\u0438\u043d",
        ),
    ),
    (
        "legumes_tofu",
        (
            "\u0442\u043e\u0444\u0443",
            "\u0444\u0430\u0441\u043e\u043b\u044c",
            "\u0431\u043e\u0431\u043e\u0432",
            "\u043d\u0443\u0442",
            "\u0447\u0435\u0447\u0435\u0432",
            "\u0433\u043e\u0440\u043e\u0445",
        ),
    ),
    (
        "grains",
        (
            "\u043a\u0440\u0443\u043f",
            "\u043f\u0435\u0440\u043b\u043e\u0432",
            "\u0440\u0438\u0441",
            "\u0433\u0440\u0435\u0447",
            "\u043f\u0430\u0441\u0442\u0430",
            "\u043e\u0432\u0441\u044f\u043d",
        ),
    ),
    (
        "vegetables",
        (
            "\u043e\u0432\u043e\u0449",
            "\u043a\u0430\u043f\u0443\u0441\u0442",
            "\u043c\u043e\u0440\u043a\u043e\u0432",
            "\u043a\u0430\u0440\u0442\u043e\u0444",
            "\u043f\u043e\u043c\u0438\u0434\u043e\u0440",
            "\u043e\u0433\u0443\u0440",
            "\u043a\u0430\u0431\u0430\u0447",
            "\u0431\u0440\u043e\u043a\u043a\u043e\u043b\u0438",
        ),
    ),
)

GENERIC_TITLES = frozenset(
    {
        "\u0441\u0430\u043b\u0430\u0442",
        "\u0441\u0443\u043f",
        "\u043a\u0430\u0448\u0430",
        "\u0431\u043b\u044e\u0434\u043e",
        "\u0443\u0436\u0438\u043d",
        "\u043e\u0431\u0435\u0434",
        "\u0437\u0430\u0432\u0442\u0440\u0430\u043a",
    }
)

NUTRITION_REQUIRED = ("kcal", "protein_g", "fat_g", "carbs_g", "fiber_g", "salt_g", "sugar_g")

_PUNCT_TABLE = str.maketrans("", "", string.punctuation + "\u00ab\u00bb\u201c\u201d\u201e\u2018\u2019")


def normalize_text_for_similarity(text: str) -> str:
    t = str(text or "").casefold().replace("\u0451", "\u0435")
    t = t.translate(_PUNCT_TABLE)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def token_set(text: str) -> set[str]:
    norm = normalize_text_for_similarity(text)
    tokens: set[str] = set()
    for raw in norm.split():
        tok = "".join(ch for ch in raw if ch.isalnum())
        if len(tok) >= 3 and tok not in STOP_WORDS:
            tokens.add(tok)
    return tokens


def jaccard_similarity(a: str, b: str) -> float:
    ta, tb = token_set(a), token_set(b)
    if not ta and not tb:
        return 1.0 if normalize_text_for_similarity(a) == normalize_text_for_similarity(b) else 0.0
    if not ta or not tb:
        return 0.0
    inter = len(ta & tb)
    union = len(ta | tb)
    return inter / union if union else 0.0


def title_similarity_score(title_a: str, title_b: str) -> float:
    base = jaccard_similarity(title_a, title_b)
    na, nb = normalize_text_for_similarity(title_a), normalize_text_for_similarity(title_b)
    if na and nb and (na in nb or nb in na):
        base = max(base, 0.85)
    return base


def _ingredient_names(recipe: dict[str, Any]) -> set[str]:
    names: set[str] = set()
    for ing in recipe.get("ingredients") or []:
        if not isinstance(ing, dict):
            continue
        for key in ("shopping_name", "name"):
            val = str(ing.get(key) or "").strip()
            if val:
                names.add(normalize_text_for_similarity(val))
    return names


def ingredient_overlap_score(recipe_a: dict[str, Any], recipe_b: dict[str, Any]) -> float:
    ia, ib = _ingredient_names(recipe_a), _ingredient_names(recipe_b)
    if not ia or not ib:
        return 0.0
    inter = len(ia & ib)
    union = len(ia | ib)
    return inter / union if union else 0.0


def step_similarity_score(recipe_a: dict[str, Any], recipe_b: dict[str, Any]) -> float:
    def _join_steps(recipe: dict[str, Any]) -> str:
        parts: list[str] = []
        for step in recipe.get("steps") or []:
            if isinstance(step, dict):
                parts.append(str(step.get("text") or ""))
            else:
                parts.append(str(step))
        return " ".join(parts)

    return jaccard_similarity(_join_steps(recipe_a), _join_steps(recipe_b))


def _issue_dict(
    code: str,
    severity: Severity,
    message: str,
    **extra: Any,
) -> dict[str, Any]:
    row: dict[str, Any] = {"code": code, "severity": severity, "message": message}
    row.update(extra)
    return row


def _signal_source_titles(signal: dict[str, Any] | None) -> list[str]:
    if not signal:
        return []
    titles: list[str] = []
    for key in SIGNAL_SOURCE_TITLE_FIELDS:
        val = signal.get(key)
        if isinstance(val, str) and val.strip():
            titles.append(val.strip())
    return titles


def _signal_abstract_phrases(signal: dict[str, Any] | None) -> list[str]:
    if not signal:
        return []
    phrases: list[str] = []
    for key in (
        "generation_prompt_hints",
        "title_hints",
        "title_hint",
        "culinary_notes",
        "dish_family",
        "dish_type",
        "phrase",
        "cooking_methods",
        "main_product_groups",
    ):
        val = signal.get(key)
        if isinstance(val, str) and val.strip():
            phrases.append(val.strip())
        elif isinstance(val, list):
            phrases.extend(str(x).strip() for x in val if str(x).strip())
    return phrases


def explain_originality_against_signal(
    recipe: dict[str, Any],
    signal: dict[str, Any] | None,
    *,
    recipe_index: int | None = None,
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    extra = {"recipe_index": recipe_index, "recipe_title": recipe.get("title")}

    for leak_field in RECIPE_LEAK_FIELDS:
        if recipe.get(leak_field):
            code = {
                "source_url": "source_url_leak",
                "original_title": "original_title_leak",
                "original_steps": "original_steps_leak",
                "source_title": "original_title_leak",
                "source_steps": "original_steps_leak",
                "copied_source_text": "source_url_leak",
            }.get(leak_field, "source_url_leak")
            findings.append(
                _issue_dict(
                    code,
                    "error",
                    f"forbidden field {leak_field!r} present in recipe",
                    path=leak_field,
                    **extra,
                )
            )

    if signal:
        for forbidden in SIGNAL_LEAK_FIELDS:
            if forbidden in signal and signal.get(forbidden):
                findings.append(
                    _issue_dict(
                        "source_leakage_in_signal",
                        "error",
                        f"forbidden field {forbidden!r} in signal {signal.get('signal_id')}",
                        signal_id=signal.get("signal_id"),
                        **extra,
                    )
                )
        for title_field in SIGNAL_SOURCE_TITLE_FIELDS:
            if title_field in signal and signal.get(title_field):
                findings.append(
                    _issue_dict(
                        "source_leakage_in_signal",
                        "error",
                        f"source title field {title_field!r} leaked in signal {signal.get('signal_id')}",
                        signal_id=signal.get("signal_id"),
                        **extra,
                    )
                )

    title = str(recipe.get("title") or "")
    norm_title = normalize_text_for_similarity(title)

    for source_title in _signal_source_titles(signal):
        sim = title_similarity_score(title, source_title)
        if sim >= TITLE_CLOSE_TO_SIGNAL:
            findings.append(
                _issue_dict(
                    "title_too_close_to_signal",
                    "error",
                    f"title similarity to source title {sim:.2f} >= {TITLE_CLOSE_TO_SIGNAL}",
                    signal_id=(signal or {}).get("signal_id"),
                    similarity=round(sim, 3),
                    **extra,
                )
            )
        norm_source = normalize_text_for_similarity(source_title)
        if len(norm_source) >= 8 and norm_source in norm_title:
            findings.append(
                _issue_dict(
                    "title_too_close_to_signal",
                    "error",
                    "generated title contains source title fragment",
                    signal_id=(signal or {}).get("signal_id"),
                    **extra,
                )
            )

    for phrase in _signal_abstract_phrases(signal):
        sim = title_similarity_score(title, phrase)
        if sim >= TITLE_CLOSE_TO_SIGNAL:
            findings.append(
                _issue_dict(
                    "title_moderately_similar",
                    "warning",
                    f"title shares abstract signal vocabulary {sim:.2f} (not a source title leak)",
                    signal_id=(signal or {}).get("signal_id"),
                    similarity=round(sim, 3),
                    **extra,
                )
            )
        elif sim >= TITLE_MODERATE_WARN:
            findings.append(
                _issue_dict(
                    "title_moderately_similar",
                    "warning",
                    f"title moderately similar to abstract signal phrase {sim:.2f}",
                    signal_id=(signal or {}).get("signal_id"),
                    similarity=round(sim, 3),
                    **extra,
                )
            )

    if norm_title in GENERIC_TITLES or len(token_set(title)) <= 1:
        findings.append(
            _issue_dict(
                "generic_title_warning",
                "warning",
                "title is too generic for production batch",
                **extra,
            )
        )

    return findings


def explain_recipe_pair_similarity(
    recipe_a: dict[str, Any],
    recipe_b: dict[str, Any],
    *,
    index_a: int | None = None,
    index_b: int | None = None,
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    title_a = str(recipe_a.get("title") or "")
    title_b = str(recipe_b.get("title") or "")
    pair = (index_a, index_b)

    title_sim = title_similarity_score(title_a, title_b)
    ing_sim = ingredient_overlap_score(recipe_a, recipe_b)
    step_sim = step_similarity_score(recipe_a, recipe_b)

    if title_sim >= TITLE_CLOSE_TO_RECIPE:
        findings.append(
            _issue_dict(
                "title_too_close_to_recipe",
                "error",
                f"title similarity {title_sim:.2f} between recipes {index_a} and {index_b}",
                pair=pair,
                similarity=round(title_sim, 3),
            )
        )
    elif title_sim >= TITLE_MODERATE_WARN:
        findings.append(
            _issue_dict(
                "title_moderately_similar",
                "warning",
                f"title similarity {title_sim:.2f} between recipes {index_a} and {index_b}",
                pair=pair,
                similarity=round(title_sim, 3),
            )
        )

    if ing_sim >= INGREDIENT_DUPLICATE_HARD:
        findings.append(
            _issue_dict(
                "ingredients_too_duplicate",
                "error",
                f"ingredient overlap {ing_sim:.2f} >= {INGREDIENT_DUPLICATE_HARD}",
                pair=pair,
                similarity=round(ing_sim, 3),
            )
        )
    elif ing_sim >= INGREDIENT_OVERLAP_WARN:
        findings.append(
            _issue_dict(
                "ingredient_overlap_moderate",
                "warning",
                f"ingredient overlap {ing_sim:.2f} >= {INGREDIENT_OVERLAP_WARN}",
                pair=pair,
                similarity=round(ing_sim, 3),
            )
        )

    if step_sim >= STEPS_CLOSE_HARD and (title_sim >= 0.45 or ing_sim >= 0.60):
        findings.append(
            _issue_dict(
                "steps_too_close_to_recipe",
                "error",
                f"step similarity {step_sim:.2f} with related title/ingredients",
                pair=pair,
                similarity=round(step_sim, 3),
            )
        )

    same_cat = recipe_a.get("category") == recipe_b.get("category")
    if same_cat and title_sim >= 0.55 and ing_sim >= INGREDIENT_OVERLAP_WARN:
        findings.append(
            _issue_dict(
                "ingredients_too_duplicate",
                "warning",
                "same category with similar title and ingredients",
                pair=pair,
            )
        )

    return findings


def _ingredient_text_blob(recipe: dict[str, Any]) -> str:
    parts: list[str] = []
    for ing in recipe.get("ingredients") or []:
        if isinstance(ing, dict):
            parts.append(str(ing.get("shopping_name") or ""))
            parts.append(str(ing.get("name") or ""))
    return normalize_text_for_similarity(" ".join(parts))


def _main_ingredient_family(recipe: dict[str, Any]) -> str:
    blob = _ingredient_text_blob(recipe)
    if not blob.strip():
        return "other"
    for family, markers in FAMILY_MARKERS:
        if any(marker in blob for marker in markers):
            return family
    return "other"


def _check_nutrition(recipe: dict[str, Any], recipe_index: int) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    nutrition = recipe.get("nutrition_per_serving") or {}
    missing = [k for k in NUTRITION_REQUIRED if nutrition.get(k) is None]
    if missing:
        findings.append(
            _issue_dict(
                "missing_nutrition",
                "error",
                f"missing nutrition fields: {', '.join(missing)}",
                recipe_index=recipe_index,
                recipe_title=recipe.get("title"),
                path="nutrition_per_serving",
            )
        )
    return findings


def _check_shopping(recipe: dict[str, Any], recipe_index: int) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    extra = {"recipe_index": recipe_index, "recipe_title": recipe.get("title")}
    for i, ing in enumerate(recipe.get("ingredients") or []):
        if not isinstance(ing, dict):
            continue
        path = f"ingredients[{i}]"
        if not str(ing.get("shopping_name") or "").strip():
            findings.append(
                _issue_dict(
                    "missing_shopping_name",
                    "error",
                    "ingredient missing shopping_name",
                    path=path,
                    **extra,
                )
            )
        unit = str(ing.get("unit") or "").strip()
        if unit and unit not in ALLOWED_UNITS:
            findings.append(
                _issue_dict(
                    "unclear_unit",
                    "error",
                    f"non-canonical unit {unit!r}",
                    path=f"{path}.unit",
                    **extra,
                )
            )
        if not str(ing.get("display_amount") or "").strip():
            findings.append(
                _issue_dict(
                    "missing_shopping_name",
                    "warning",
                    "ingredient missing display_amount",
                    path=f"{path}.display_amount",
                    **extra,
                )
            )
    return findings


def _map_validator_issue(issue: Any) -> str:
    mapping = {
        "restriction_safety_conflict": "restriction_contradiction",
        "restriction_contradiction": "restriction_contradiction",
        "diet_contradiction": "restriction_contradiction",
        "missing_shopping_name": "missing_shopping_name",
        "ingredient_unclear_unit": "unclear_unit",
        "unknown_ingredient_category": "unknown_category",
        "missing_fiber": "missing_nutrition",
        "missing_sugar_salt": "missing_nutrition",
        "generic_title": "generic_title_warning",
    }
    return mapping.get(issue.code, issue.code)


def evaluate_recipe_gold_v3_quality_gate(
    recipes: list[dict[str, Any]],
    signals: list[dict[str, Any]] | None = None,
    *,
    min_score: int = 85,
    avg_score: float = 90.0,
    fail_on_warning: bool = False,
) -> dict[str, Any]:
    signals = signals or []
    signal_by_id = {
        str(s.get("signal_id")): s for s in signals if s.get("signal_id") is not None
    }

    errors_by_code: Counter[str] = Counter()
    warnings_by_code: Counter[str] = Counter()
    per_recipe: list[dict[str, Any]] = []
    pairwise: list[dict[str, Any]] = []
    signal_findings: list[dict[str, Any]] = []

    scores: list[int] = []
    valid_count = 0
    invalid_count = 0

    processed: list[dict[str, Any]] = []
    for recipe in recipes:
        processed.append(postprocess_generated_recipe(recipe))

    for idx, recipe in enumerate(processed):
        recipe_errors: list[str] = []
        recipe_warnings: list[str] = []

        validation = validate_recipe_gold_v3(recipe)
        scores.append(validation.score)
        if validation.ok:
            valid_count += 1
        else:
            invalid_count += 1
            recipe_errors.append("invalid_recipe")
            errors_by_code["invalid_recipe"] += 1

        if validation.score < min_score:
            recipe_errors.append("low_score")
            errors_by_code["low_score"] += 1

        for issue in validation.errors:
            code = _map_validator_issue(issue)
            if issue.severity == "error":
                if code not in recipe_errors:
                    recipe_errors.append(code)
                errors_by_code[code] += 1
            else:
                if code not in recipe_warnings:
                    recipe_warnings.append(code)
                warnings_by_code[code] += 1

        for issue in validation.warnings:
            code = _map_validator_issue(issue)
            if code not in recipe_warnings:
                recipe_warnings.append(code)
            warnings_by_code[code] += 1

        for fn in (_check_nutrition, _check_shopping):
            for finding in fn(recipe, idx):
                code = finding["code"]
                if finding["severity"] == "error":
                    if code not in recipe_errors:
                        recipe_errors.append(code)
                    errors_by_code[code] += 1
                else:
                    if code not in recipe_warnings:
                        recipe_warnings.append(code)
                    warnings_by_code[code] += 1

        for finding in check_ui_text_contract(recipe, recipe_index=idx):
            code = finding["code"]
            if finding["severity"] == "error":
                if code not in recipe_errors:
                    recipe_errors.append(code)
                errors_by_code[code] += 1
            else:
                if code not in recipe_warnings:
                    recipe_warnings.append(code)
                warnings_by_code[code] += 1

        signal_ids = recipe.get("source_signal_ids") or []
        matched_signals = [
            signal_by_id[str(sid)] for sid in signal_ids if str(sid) in signal_by_id
        ]

        for signal in matched_signals:
            for finding in explain_originality_against_signal(recipe, signal, recipe_index=idx):
                code = finding["code"]
                signal_findings.append(
                    {
                        "recipe_index": idx,
                        "title": recipe.get("title"),
                        "signal_id": signal.get("signal_id"),
                        **finding,
                    }
                )
                if finding["severity"] == "error":
                    if code not in recipe_errors:
                        recipe_errors.append(code)
                    errors_by_code[code] += 1
                else:
                    if code not in recipe_warnings:
                        recipe_warnings.append(code)
                    warnings_by_code[code] += 1

        per_recipe.append(
            {
                "index": idx,
                "title": recipe.get("title"),
                "score": validation.score,
                "valid": validation.ok,
                "category": recipe.get("category"),
                "meal_type": recipe.get("meal_type"),
                "errors": recipe_errors,
                "warnings": recipe_warnings,
            }
        )

    for i in range(len(processed)):
        for j in range(i + 1, len(processed)):
            pair_issues = explain_recipe_pair_similarity(
                processed[i], processed[j], index_a=i, index_b=j
            )
            if not pair_issues:
                continue
            pairwise.append(
                {
                    "pair": [i, j],
                    "title_a": processed[i].get("title"),
                    "title_b": processed[j].get("title"),
                    "findings": pair_issues,
                }
            )
            for finding in pair_issues:
                code = finding["code"]
                if finding["severity"] == "error":
                    errors_by_code[code] += 1
                    if code not in per_recipe[i]["errors"]:
                        per_recipe[i]["errors"].append(code)
                    if code not in per_recipe[j]["errors"]:
                        per_recipe[j]["errors"].append(code)
                else:
                    warnings_by_code[code] += 1
                    if code not in per_recipe[i]["warnings"]:
                        per_recipe[i]["warnings"].append(code)
                    if code not in per_recipe[j]["warnings"]:
                        per_recipe[j]["warnings"].append(code)

    n = len(processed)
    cat_counts = Counter(str(r.get("category") or "unknown") for r in processed)
    meal_counts = Counter(str(r.get("meal_type") or "unknown") for r in processed)
    main_counts = Counter(_main_ingredient_family(r) for r in processed)

    category_over = n >= 10 and any(c / n > CATEGORY_OVERCONCENTRATION for c in cat_counts.values())
    meal_over = n >= 10 and any(c / n > MEAL_TYPE_WARN for c in meal_counts.values())

    non_other_main = {k: v for k, v in main_counts.items() if k != "other"}
    main_over = False
    if n >= 10 and non_other_main:
        main_over = any(c / n > MAIN_INGREDIENT_HARD for c in non_other_main.values())
    elif n >= 10 and main_counts.get("other", 0) == n:
        warnings_by_code["repeated_main_ingredient_warning"] += 1

    if category_over:
        top_cat, _ = cat_counts.most_common(1)[0]
        errors_by_code["batch_category_overconcentration"] += 1
        for row in per_recipe:
            if row["category"] == top_cat and "batch_category_overconcentration" not in row["errors"]:
                row["errors"].append("batch_category_overconcentration")

    if main_over:
        top_main = max(non_other_main, key=non_other_main.get)
        errors_by_code["batch_main_ingredient_overconcentration"] += 1
        warnings_by_code["repeated_main_ingredient_warning"] += 1
        for row in per_recipe:
            if _main_ingredient_family(processed[row["index"]]) == top_main:
                if "batch_main_ingredient_overconcentration" not in row["errors"]:
                    row["errors"].append("batch_main_ingredient_overconcentration")
                if "repeated_main_ingredient_warning" not in row["warnings"]:
                    row["warnings"].append("repeated_main_ingredient_warning")

    if meal_over:
        warnings_by_code["meal_type_concentration_warning"] += 1
        for row in per_recipe:
            if "meal_type_concentration_warning" not in row["warnings"]:
                row["warnings"].append("meal_type_concentration_warning")

    if n >= 10:
        for cat, count in cat_counts.items():
            if CATEGORY_OVERCONCENTRATION < count / n <= CATEGORY_OVERCONCENTRATION + 0.15:
                warnings_by_code["category_concentration_warning"] += 1

    avg = round(sum(scores) / len(scores), 1) if scores else 0.0
    if avg < avg_score:
        errors_by_code["low_score"] += 1

    originality_fail = any(
        errors_by_code.get(c, 0) > 0
        for c in (
            "source_url_leak",
            "original_title_leak",
            "original_steps_leak",
            "source_leakage_in_signal",
            "title_too_close_to_signal",
        )
    )
    duplicate_fail = any(
        errors_by_code.get(c, 0) > 0
        for c in (
            "title_too_close_to_recipe",
            "steps_too_close_to_recipe",
            "ingredients_too_duplicate",
        )
    )

    diversity_status = "FAIL" if category_over or main_over else ("WARN" if meal_over else "PASS")

    has_errors = bool(errors_by_code)
    has_warnings = bool(warnings_by_code)
    ok = not has_errors and avg >= avg_score
    if fail_on_warning and has_warnings:
        ok = False

    recommendation: Recommendation = "PASS" if ok else "FAIL"

    return {
        "ok": ok,
        "recommendation": recommendation,
        "summary": {
            "records": n,
            "valid": valid_count,
            "invalid": invalid_count,
            "avg_score": avg,
            "min_score_threshold": min_score,
            "avg_score_threshold": avg_score,
            "originality": "FAIL" if originality_fail else "PASS",
            "duplicate_check": "FAIL" if duplicate_fail else "PASS",
            "diversity": diversity_status,
            "quality_gate": recommendation,
        },
        "errors_by_code": dict(errors_by_code),
        "warnings_by_code": dict(warnings_by_code),
        "per_recipe": per_recipe,
        "pairwise": pairwise,
        "signal_findings": signal_findings,
        "diversity": {
            "categories": dict(cat_counts),
            "meal_types": dict(meal_counts),
            "main_ingredient_families": dict(main_counts),
            "category_overconcentration": category_over,
            "meal_type_overconcentration": meal_over,
            "main_ingredient_overconcentration": main_over,
        },
    }
