"""PLANAM Recipe Gold V3 validation (no DB writes, no generation)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Literal

from app.nutrition.restrictions_catalog import get_restriction_definition
from app.nutrition.restriction_safety import explain_recipe_restriction_conflicts
from app.recipes.recipe_gold_v3_schema import (
    ALLOWED_CATEGORIES,
    ALLOWED_DIFFICULTIES,
    ALLOWED_FAMILY_FIT,
    ALLOWED_INGREDIENT_CATEGORIES,
    ALLOWED_MEAL_TYPES,
    ALLOWED_SIMILARITY_RISK,
    ALLOWED_SOURCE_TYPES,
    ALLOWED_STATUSES,
    ALLOWED_UNITS,
    ENGLISH_TITLE_PREFIXES,
    FORBIDDEN_TECHNICAL_CATEGORIES,
    MAX_INGREDIENTS_DEFAULT,
    MAX_TITLE_LEN,
    MIN_INGREDIENTS,
    MIN_STEP_TEXT_LEN,
    MIN_STEPS,
    MIN_TITLE_LEN,
    PRODUCTION_READY_MIN_SCORE,
    SCHEMA_VERSION,
)

Severity = Literal["error", "warning"]

CYRILLIC_RE = re.compile(r"[А-Яа-яЁё]")
URL_RE = re.compile(r"https?://|www\.|povarenok\.ru", re.IGNORECASE)
BOWL_RE = re.compile(r"\bbowl\b", re.IGNORECASE)
VAGUE_STEP_RE = re.compile(
    r"смешать всё|готовить до готовности|варить до готовности",
    re.IGNORECASE,
)
UNSAFE_STEP_RE = re.compile(
    r"сыр(ой|ая|ое)\s+(мясо|рыб|куриц)|без термической обработки",
    re.IGNORECASE,
)
UGLY_DECIMAL_RE = re.compile(r"\.\d{3,}")
GENERIC_TITLE_RE = re.compile(
    r"^(салат|суп|каша|блюдо|ужин|обед|завтрак)$",
    re.IGNORECASE,
)
ADJECTIVE_HEAVY_RE = re.compile(
    r"(\w+\s+){4,}",
)

MEAT_MARKERS = (
    "мясо",
    "куриц",
    "курин",
    "говядин",
    "свинин",
    "баранин",
    "индейк",
    "бекон",
    "ветчин",
    "фарш",
    "рыб",
    "лосос",
    "тунец",
)
DAIRY_EGG_MARKERS = ("молок", "сливк", "сыр", "творог", "йогурт", "яйц", "желток")
ALCOHOL_MARKERS = (
    "алкогол",
    "вино",
    "пиво",
    "водк",
    "коньяк",
    "ром",
    "ликер",
    "ликёр",
    "настойк",
)
PORK_MARKERS = ("свинин", "свин", "бекон", "ветчин", "сало", "карбонат")


@dataclass
class ValidationIssue:
    code: str
    severity: Severity
    message: str
    path: str | None = None


@dataclass
class ValidationResult:
    ok: bool
    errors: list[ValidationIssue] = field(default_factory=list)
    warnings: list[ValidationIssue] = field(default_factory=list)
    score: int = 0

    @property
    def production_ready(self) -> bool:
        return self.ok and self.score >= PRODUCTION_READY_MIN_SCORE


def _issue(
    code: str,
    message: str,
    *,
    severity: Severity = "error",
    path: str | None = None,
) -> ValidationIssue:
    return ValidationIssue(code=code, severity=severity, message=message, path=path)


def _text_contains_any(text: str, markers: tuple[str, ...]) -> str | None:
    lower = text.lower()
    for marker in markers:
        if marker in lower:
            return marker
    return None


def _ingredient_blob(recipe: dict[str, Any]) -> str:
    parts: list[str] = []
    for ing in recipe.get("ingredients") or []:
        if isinstance(ing, dict):
            parts.append(str(ing.get("name", "")))
            parts.append(str(ing.get("shopping_name", "")))
    return " ".join(parts).lower()


def _fake_recipe_for_safety(recipe: dict[str, Any]) -> Any:
    class _Fake:
        title = recipe.get("title", "")
        description = recipe.get("description", "")
        ingredients = [
            {"name": i.get("name", "")}
            for i in (recipe.get("ingredients") or [])
            if isinstance(i, dict)
        ]
        diets = list(recipe.get("diet_tags") or [])
        tags = []
        allergens = list(recipe.get("allergen_keys") or [])
        is_alcoholic = bool(
            _text_contains_any(_ingredient_blob(recipe), ALCOHOL_MARKERS)
        )

    return _Fake()


def _fake_profile_from_restrictions(keys: list[str]) -> Any:
    class _Profile:
        restrictions = keys
        diets = []
        allergies = []
        banned_foods = ""
        medical_restrictions = ""

    return _Profile()


def validate_recipe_gold_v3(
    recipe: dict[str, Any],
    *,
    blocked_source_titles: list[str] | None = None,
    blocked_fragments: list[str] | None = None,
) -> ValidationResult:
    errors: list[ValidationIssue] = []
    warnings: list[ValidationIssue] = []

    def err(code: str, message: str, path: str | None = None) -> None:
        errors.append(_issue(code, message, path=path))

    def warn(code: str, message: str, path: str | None = None) -> None:
        warnings.append(_issue(code, message, severity="warning", path=path))

    # A. Required fields
    required_fields = (
        "schema_version",
        "status",
        "source_type",
        "originality",
        "title",
        "description",
        "meal_type",
        "category",
        "servings",
        "prep_time_min",
        "cook_time_min",
        "total_time_min",
        "difficulty",
        "ingredients",
        "steps",
        "nutrition_per_serving",
        "restriction_keys",
        "allergen_keys",
        "diet_tags",
    )
    for field_name in required_fields:
        if field_name not in recipe:
            err("missing_required_field", f"Missing required field: {field_name}", field_name)

    # B. Schema values
    if recipe.get("schema_version") != SCHEMA_VERSION:
        err("invalid_schema_version", "schema_version must be recipe_gold_v3", "schema_version")
    if recipe.get("status") not in ALLOWED_STATUSES:
        err("invalid_status", "status must be gold", "status")
    if recipe.get("source_type") not in ALLOWED_SOURCE_TYPES:
        err("invalid_source_type", f"source_type must be one of {sorted(ALLOWED_SOURCE_TYPES)}", "source_type")
    if recipe.get("meal_type") not in ALLOWED_MEAL_TYPES:
        err("invalid_meal_type", f"meal_type not allowed: {recipe.get('meal_type')}", "meal_type")
    if recipe.get("category") not in ALLOWED_CATEGORIES:
        err("invalid_category", f"category not allowed: {recipe.get('category')}", "category")
    if recipe.get("difficulty") not in ALLOWED_DIFFICULTIES:
        err("invalid_difficulty", f"difficulty not allowed: {recipe.get('difficulty')}", "difficulty")
    family_fit = recipe.get("family_fit", "high")
    if family_fit not in ALLOWED_FAMILY_FIT:
        err("invalid_family_fit", f"family_fit not allowed: {family_fit}", "family_fit")

    title = str(recipe.get("title") or "").strip()
    description = str(recipe.get("description") or "").strip()

    # C. Title quality
    if not title:
        err("empty_title", "title is empty", "title")
    else:
        if len(title) < MIN_TITLE_LEN or len(title) > MAX_TITLE_LEN:
            err("title_length", f"title length must be {MIN_TITLE_LEN}-{MAX_TITLE_LEN}", "title")
        lower_title = title.lower()
        for prefix in ENGLISH_TITLE_PREFIXES:
            if lower_title.startswith(prefix):
                err("english_title_prefix", f"title contains forbidden prefix: {prefix}", "title")
        if BOWL_RE.search(title):
            err("forbidden_bowl_in_title", "title contains forbidden 'bowl'", "title")
        if URL_RE.search(title):
            err("title_contains_url", "title contains URL/domain marker", "title")
        if not CYRILLIC_RE.search(title):
            err("title_not_russian", "title must contain Cyrillic characters", "title")
        if GENERIC_TITLE_RE.match(title):
            warn("generic_title", "title looks too generic", "title")
        if len(title.split()) >= 6:
            warn("title_too_many_words", "title contains many words/adjectives", "title")
        if re.search(r"[«\"“].+[»\"”]", title):
            warn("title_quoted_phrase", "title contains quoted phrase (source-like)", "title")

    # D. Originality
    originality = recipe.get("originality") or {}
    if not isinstance(originality, dict):
        err("invalid_originality", "originality must be an object", "originality")
        originality = {}
    for flag, code in (
        ("is_original_planam_recipe", "originality_not_original"),
        ("no_source_title_used", "originality_source_title"),
        ("no_source_steps_used", "originality_source_steps"),
        ("no_direct_copy", "originality_direct_copy"),
    ):
        if originality.get(flag) is not True:
            err(code, f"originality.{flag} must be true", f"originality.{flag}")
    risk = originality.get("source_similarity_risk", "low")
    if risk not in ALLOWED_SIMILARITY_RISK:
        err("invalid_similarity_risk", "invalid source_similarity_risk", "originality.source_similarity_risk")
    elif risk == "high":
        err("high_similarity_risk", "source_similarity_risk must not be high", "originality.source_similarity_risk")

    blocked_titles = [t.strip().lower() for t in (blocked_source_titles or []) if t]
    if title and blocked_titles:
        norm_title = title.lower()
        for blocked in blocked_titles:
            if norm_title == blocked or blocked in norm_title:
                err("blocked_source_title", f"title matches blocked source title", "title")
                break

    # E. Ingredients
    ingredients = recipe.get("ingredients") or []
    if not isinstance(ingredients, list):
        err("invalid_ingredients", "ingredients must be a list", "ingredients")
        ingredients = []
    if len(ingredients) < MIN_INGREDIENTS:
        err("too_few_ingredients", f"at least {MIN_INGREDIENTS} ingredients required", "ingredients")
    if len(ingredients) > MAX_INGREDIENTS_DEFAULT:
        warn("too_many_ingredients", f"more than {MAX_INGREDIENTS_DEFAULT} ingredients", "ingredients")

    seen_names: set[str] = set()
    optional_count = 0
    for idx, ing in enumerate(ingredients):
        path = f"ingredients[{idx}]"
        if not isinstance(ing, dict):
            err("invalid_ingredient", "ingredient must be object", path)
            continue
        name = str(ing.get("name") or "").strip()
        if not name:
            err("ingredient_missing_name", "ingredient name missing", f"{path}.name")
        elif len(name) > 120:
            err("ingredient_name_too_long", "ingredient name too long", f"{path}.name")
        else:
            key = name.lower()
            if key in seen_names:
                warn("duplicate_ingredient", f"duplicate ingredient: {name}", f"{path}.name")
            seen_names.add(key)

        unit = str(ing.get("unit") or "").strip()
        if not unit:
            err("ingredient_missing_unit", "ingredient unit missing", f"{path}.unit")
        elif unit not in ALLOWED_UNITS:
            warn("ingredient_unclear_unit", f"unit not in whitelist: {unit}", f"{path}.unit")

        amount = ing.get("amount")
        if amount is None or float(amount) <= 0:
            err("ingredient_invalid_amount", "amount must be > 0", f"{path}.amount")
        elif UGLY_DECIMAL_RE.search(str(amount)):
            warn("ugly_fractional_amount", f"amount has ugly decimals: {amount}", f"{path}.amount")

        display_amount = str(ing.get("display_amount") or "").strip()
        if not display_amount:
            err("missing_display_amount", "display_amount missing", f"{path}.display_amount")

        category = str(ing.get("category") or "").strip()
        if not category:
            err("ingredient_missing_category", "ingredient category missing", f"{path}.category")
        elif category in FORBIDDEN_TECHNICAL_CATEGORIES:
            err("technical_ingredient_category", f"technical English category: {category}", f"{path}.category")
        elif category not in ALLOWED_INGREDIENT_CATEGORIES:
            warn("unknown_ingredient_category", f"non-canonical category: {category}", f"{path}.category")

        shopping_name = str(ing.get("shopping_name") or "").strip()
        if not shopping_name:
            err("missing_shopping_name", "shopping_name missing", f"{path}.shopping_name")

        if ing.get("optional") is True:
            optional_count += 1

    if optional_count > 3:
        warn("too_many_optional_ingredients", "too many optional ingredients", "ingredients")

    # F. Steps
    steps = recipe.get("steps") or []
    if not isinstance(steps, list):
        err("invalid_steps", "steps must be a list", "steps")
        steps = []
    if len(steps) < MIN_STEPS:
        err("too_few_steps", f"at least {MIN_STEPS} steps required", "steps")
    if len(steps) > 10:
        warn("too_many_steps", "more than 10 steps", "steps")

    step_numbers: set[int] = set()
    for idx, step in enumerate(steps):
        path = f"steps[{idx}]"
        if not isinstance(step, dict):
            err("invalid_step", "step must be object", path)
            continue
        num = step.get("step_number")
        if num is None:
            err("step_missing_number", "step_number missing", f"{path}.step_number")
        else:
            n = int(num)
            if n in step_numbers:
                err("duplicate_step_number", f"duplicate step_number {n}", f"{path}.step_number")
            step_numbers.add(n)
        text = str(step.get("text") or "").strip()
        if not text:
            err("empty_step", "step text empty", f"{path}.text")
        elif len(text) < MIN_STEP_TEXT_LEN:
            err("step_too_short", f"step text must be >= {MIN_STEP_TEXT_LEN} chars", f"{path}.text")
        elif len(text) > 500:
            warn("step_too_long", "step text very long", f"{path}.text")
        if VAGUE_STEP_RE.search(text):
            warn("vague_step", "step text is vague", f"{path}.text")
        if UNSAFE_STEP_RE.search(text):
            err("unsafe_step", "step contains unsafe instruction", f"{path}.text")
        for fragment in blocked_fragments or []:
            frag = fragment.strip()
            if len(frag) >= 40 and frag.lower() in text.lower():
                err("copied_step_fragment", "step contains blocked source fragment", f"{path}.text")
                break

    # G. Nutrition
    nutrition = recipe.get("nutrition_per_serving") or {}
    if not isinstance(nutrition, dict):
        err("invalid_nutrition", "nutrition_per_serving must be object", "nutrition_per_serving")
        nutrition = {}
    kcal = nutrition.get("kcal")
    protein = nutrition.get("protein_g")
    fat = nutrition.get("fat_g")
    carbs = nutrition.get("carbs_g")
    if kcal is None or float(kcal) <= 0:
        err("missing_kcal", "nutrition_per_serving.kcal must be > 0", "nutrition_per_serving.kcal")
    for key, val in (("protein_g", protein), ("fat_g", fat), ("carbs_g", carbs)):
        if val is None or float(val) < 0:
            err("missing_macro", f"{key} missing or negative", f"nutrition_per_serving.{key}")
    if kcal and protein is not None and fat is not None and carbs is not None:
        est = float(protein) * 4 + float(fat) * 9 + float(carbs) * 4
        if float(kcal) > 0 and abs(float(kcal) - est) / float(kcal) > 0.35:
            err("kcal_macro_mismatch", "kcal inconsistent with macros (>35% diff)", "nutrition_per_serving")
    servings = recipe.get("servings")
    if servings is None or not (1 <= int(servings) <= 8):
        err("invalid_servings", "servings must be 1-8", "servings")
    if nutrition.get("fiber_g") is None:
        warn("missing_fiber", "fiber_g missing", "nutrition_per_serving.fiber_g")
    if nutrition.get("sugar_g") is None and nutrition.get("salt_g") is None:
        warn("missing_sugar_salt", "sugar_g/salt_g missing", "nutrition_per_serving")
    if kcal is not None:
        k = float(kcal)
        if k < 80 or k > 1200:
            warn("kcal_out_of_range", f"kcal looks unusual: {k}", "nutrition_per_serving.kcal")

    prep = int(recipe.get("prep_time_min") or 0)
    cook = int(recipe.get("cook_time_min") or 0)
    total = int(recipe.get("total_time_min") or 0)
    if total != prep + cook and total < prep + cook:
        warn("total_time_mismatch", "total_time_min less than prep+cook", "total_time_min")

    # H. Restrictions
    restriction_keys = list(recipe.get("restriction_keys") or [])
    diet_tags = [str(t).lower() for t in (recipe.get("diet_tags") or [])]
    blob = _ingredient_blob(recipe)

    for key in restriction_keys:
        if get_restriction_definition(key) is None:
            err("unknown_restriction_key", f"unknown restriction key: {key}", "restriction_keys")

    active_keys = list(restriction_keys)
    if "vegetarian" in diet_tags and "vegetarian" not in active_keys:
        active_keys.append("vegetarian")
    if "vegan" in diet_tags and "vegan" not in active_keys:
        active_keys.append("vegan")
    if "no_pork" in active_keys and _text_contains_any(blob, PORK_MARKERS):
        err("restriction_contradiction", "no_pork but pork ingredient present", "restriction_keys")
    if "no_alcohol" in active_keys and _text_contains_any(blob, ALCOHOL_MARKERS):
        err("restriction_contradiction", "no_alcohol but alcohol ingredient present", "restriction_keys")
    if "vegetarian" in active_keys and _text_contains_any(blob, MEAT_MARKERS):
        err("diet_contradiction", "vegetarian but meat/fish ingredient present", "diet_tags")
    if "vegan" in active_keys and (
        _text_contains_any(blob, MEAT_MARKERS) or _text_contains_any(blob, DAIRY_EGG_MARKERS)
    ):
        err("diet_contradiction", "vegan but animal product ingredient present", "diet_tags")

    if active_keys:
        profile = _fake_profile_from_restrictions(active_keys)
        fake = _fake_recipe_for_safety(recipe)
        conflicts = explain_recipe_restriction_conflicts(fake, profile)
        hard = [c for c in conflicts if c.severity == "hard"]
        if hard:
            err(
                "restriction_safety_conflict",
                f"restriction safety conflict: {hard[0].label_ru}",
                "restriction_keys",
            )

    # I. Shopping contract — covered in ingredients loop

    shopping = recipe.get("shopping") or {}
    if isinstance(shopping, dict) and shopping.get("aggregation_safe") is False:
        warn("shopping_not_aggregation_safe", "shopping.aggregation_safe is false", "shopping")

    # J. Image prompt data
    image = recipe.get("image_prompt_data") or {}
    if not isinstance(image, dict):
        err("invalid_image_prompt", "image_prompt_data must be object", "image_prompt_data")
        image = {}
    summary = str(image.get("dish_visual_summary") or "").strip()
    if not summary:
        err("missing_dish_visual_summary", "dish_visual_summary missing", "image_prompt_data.dish_visual_summary")
    avoid = image.get("avoid_visuals") or []
    if isinstance(avoid, list):
        joined = " ".join(str(x) for x in avoid).lower()
        if "логотип" not in joined and "текст" not in joined:
            warn("image_avoid_incomplete", "avoid_visuals should mention text/logos", "image_prompt_data.avoid_visuals")
    if summary and re.search(r"\b(логотип|надпись|текст на фото)\b", summary, re.I):
        err("image_prompt_text_instruction", "image prompt encourages text/logos", "image_prompt_data.dish_visual_summary")
    if summary and re.search(r"\b(руки|человек|люди)\b", summary, re.I):
        err("image_prompt_people", "image prompt emphasizes people/hands", "image_prompt_data.dish_visual_summary")

    # Score
    score = 100
    score -= 8 * len(errors)
    score -= 3 * len(warnings)
    score = max(0, min(100, score))

    return ValidationResult(ok=not errors, errors=errors, warnings=warnings, score=score)
