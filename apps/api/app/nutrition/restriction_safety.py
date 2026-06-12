"""Backend restriction safety checks for recipes vs user nutrition profiles."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Iterable, Literal

from app.nutrition.restrictions_catalog import (
    RestrictionDefinition,
    get_restriction_definition,
    normalize_restriction_key,
    normalize_restrictions,
)

ConflictSource = Literal[
    "recipe_restrictions",
    "ingredients",
    "tags",
    "diets",
    "allergens",
    "profile",
    "unknown",
]

Severity = Literal["hard", "soft"]

# Onboarding allergy codes → canonical restriction keys (bridge).
_ALLERGY_TO_RESTRICTION_KEYS: dict[str, tuple[str, ...]] = {
    "nuts": ("no_nuts",),
    "dairy": ("no_milk", "lactose_free"),
    "gluten": ("gluten_free",),
    "eggs": ("no_eggs",),
    "seafood": ("no_seafood",),
    "fish": ("no_fish",),
    "soy": ("no_soy",),
}

# Ingredient markers for direct allergy explanation (source=profile).
_ALLERGY_INGREDIENT_MARKERS: dict[str, tuple[str, ...]] = {
    "nuts": ("орех", "орехи", "арахис", "миндаль", "фундук", "кешью", "грецкий орех"),
    "dairy": ("молоко", "сливки", "сыр", "творог", "йогурт", "кефир", "сметана"),
    "gluten": ("пшеница", "мука пшеничная", "хлеб", "глютен", "макароны", "паста"),
    "eggs": ("яйцо", "яйца", "белок", "желток"),
    "seafood": ("креветки", "мидии", "кальмар", "осьминог", "морепродукты"),
    "fish": ("рыба", "лосось", "тунец", "треска", "форель"),
    "soy": ("соя", "соевый соус", "тофу"),
    "honey": ("мед", "мёд"),
}

_ALLERGY_LABELS_RU: dict[str, str] = {
    "nuts": "орехи",
    "dairy": "молочные",
    "gluten": "глютен",
    "eggs": "яйца",
    "seafood": "морепродукты",
    "fish": "рыба",
    "soy": "соя",
    "honey": "мёд",
}


@dataclass(frozen=True)
class RestrictionConflict:
    restriction_key: str
    label_ru: str
    severity: Severity
    reason: str
    matched_ingredient: str | None = None
    source: ConflictSource = "unknown"


def normalize_profile_restrictions(profile: Any) -> list[str]:
    """Collect canonical restriction keys from profile restrictions, diets, and allergies."""
    raw_keys: list[str] = []

    restrictions = getattr(profile, "restrictions", None)
    if restrictions:
        raw_keys.extend(normalize_restrictions(restrictions))

    for diet in getattr(profile, "diets", None) or []:
        key = normalize_restriction_key(str(diet))
        if key:
            raw_keys.append(key)

    for allergy in getattr(profile, "allergies", None) or []:
        code = str(allergy).strip().lower()
        if not code or code == "none":
            continue
        bridged = _ALLERGY_TO_RESTRICTION_KEYS.get(code)
        if bridged:
            raw_keys.extend(bridged)
        else:
            key = normalize_restriction_key(code)
            if key:
                raw_keys.append(key)

    return normalize_restrictions(raw_keys)


def has_hard_conflicts(conflicts: list[RestrictionConflict]) -> bool:
    return any(c.severity == "hard" for c in conflicts)


def has_soft_conflicts(conflicts: list[RestrictionConflict]) -> bool:
    return any(c.severity == "soft" for c in conflicts)


def recipe_is_allowed_for_profile(recipe: Any, profile: Any) -> bool:
    """False when any hard restriction conflict exists."""
    conflicts = explain_recipe_restriction_conflicts(recipe, profile)
    return not has_hard_conflicts(conflicts)


def filter_recipes_for_profile(recipes: Iterable[Any], profile: Any) -> list[Any]:
    return [r for r in recipes if recipe_is_allowed_for_profile(r, profile)]


def explain_recipe_restriction_conflicts(recipe: Any, profile: Any) -> list[RestrictionConflict]:
    conflicts: list[RestrictionConflict] = []
    seen: set[tuple[str, str, str | None]] = set()

    ingredient_texts = _collect_ingredient_texts(recipe)
    full_text = _collect_recipe_full_text(recipe, ingredient_texts)
    recipe_allergens = {_norm_token(a) for a in _collect_recipe_allergens(recipe)}
    recipe_tags = {_norm_token(t) for t in _collect_recipe_tags(recipe)}
    recipe_diets = {_norm_token(d) for d in _collect_recipe_diets(recipe)}
    recipe_restrictions = {_norm_token(r) for r in _collect_recipe_restrictions(recipe)}

    active_keys = normalize_profile_restrictions(profile)

    for key in active_keys:
        definition = get_restriction_definition(key)
        if definition is None:
            continue
        conflicts.extend(
            _check_definition_markers(
                definition,
                ingredient_texts,
                full_text,
                source="ingredients",
                seen=seen,
                markers=definition.banned_ingredient_markers,
            )
        )
        conflicts.extend(
            _check_definition_markers(
                definition,
                ingredient_texts,
                full_text,
                source="ingredients",
                seen=seen,
                markers=definition.warning_ingredient_markers,
                force_soft=True,
            )
        )

    if normalize_restriction_key("no_alcohol") in active_keys or "no_alcohol" in active_keys:
        if bool(getattr(recipe, "is_alcoholic", False)):
            _append_conflict(
                conflicts,
                seen,
                RestrictionConflict(
                    restriction_key="no_alcohol",
                    label_ru="Без алкоголя",
                    severity="hard",
                    reason="Рецепт помечен как алкогольный",
                    source="tags",
                ),
            )

    for allergy in getattr(profile, "allergies", None) or []:
        code = str(allergy).strip().lower()
        if not code or code == "none":
            continue
        label = _ALLERGY_LABELS_RU.get(code, code)
        if code in recipe_allergens:
            _append_conflict(
                conflicts,
                seen,
                RestrictionConflict(
                    restriction_key=f"allergy:{code}",
                    label_ru=f"Аллергия: {label}",
                    severity="hard",
                    reason=f"В рецепте указан аллерген «{label}»",
                    source="allergens",
                ),
            )
        markers = _ALLERGY_INGREDIENT_MARKERS.get(code, ())
        matched_marker, matched_ingredient = _find_marker_match(markers, ingredient_texts, full_text)
        if matched_marker:
            _append_conflict(
                conflicts,
                seen,
                RestrictionConflict(
                    restriction_key=f"allergy:{code}",
                    label_ru=f"Аллергия: {label}",
                    severity="hard",
                    reason=f"Ингредиент может содержать {label} («{matched_marker}»)",
                    matched_ingredient=matched_ingredient,
                    source="profile",
                ),
            )

    for banned in _split_food_list(getattr(profile, "banned_foods", "") or ""):
        marker = banned.lower()
        matched_marker, matched_ingredient = _find_marker_match((marker,), ingredient_texts, full_text)
        if matched_marker:
            _append_conflict(
                conflicts,
                seen,
                RestrictionConflict(
                    restriction_key="banned_food",
                    label_ru="Запрещённый продукт",
                    severity="hard",
                    reason=f"Запрещённый продукт из профиля: «{banned}»",
                    matched_ingredient=matched_ingredient or banned,
                    source="profile",
                ),
            )

    # Stage C+: parse medical_restrictions free text with NLP — not on Stage B.
    _ = getattr(profile, "medical_restrictions", None)

    # Recipe-declared diets/restrictions that contradict profile hard rules (explicit tags).
    for key in active_keys:
        definition = get_restriction_definition(key)
        if definition is None or definition.severity != "hard":
            continue
        for token in recipe_diets | recipe_restrictions | recipe_tags:
            if token and _token_conflicts_with_restriction(token, definition):
                _append_conflict(
                    conflicts,
                    seen,
                    RestrictionConflict(
                        restriction_key=key,
                        label_ru=definition.label_ru,
                        severity="hard",
                        reason=f"Метка рецепта «{token}» не соответствует ограничению",
                        source="recipe_restrictions",
                    ),
                )

    return conflicts


def _norm_token(value: str) -> str:
    return str(value).strip().lower()


def _split_food_list(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"[,;\n]+", text) if part.strip()]


def _collect_ingredient_texts(recipe: Any) -> list[str]:
    texts: list[str] = []
    try:
        from app.models.recipe import Recipe
        from app.services.recipe_storage import get_structured_ingredients

        if isinstance(recipe, Recipe) or hasattr(recipe, "ingredient_rows"):
            for ing in get_structured_ingredients(recipe):  # type: ignore[arg-type]
                name = str(ing.get("name", "")).strip()
                if name:
                    texts.append(name)
            return texts
    except Exception:
        pass

    ingredients = getattr(recipe, "ingredients", None)
    if isinstance(ingredients, list):
        for raw in ingredients:
            if isinstance(raw, dict):
                name = str(raw.get("name", "")).strip()
                if name:
                    texts.append(name)
            elif isinstance(raw, str) and raw.strip():
                texts.append(raw.strip())
    return texts


def _collect_recipe_tags(recipe: Any) -> list[str]:
    try:
        from app.models.recipe import Recipe
        from app.services.recipe_storage import get_tags

        if isinstance(recipe, Recipe) or hasattr(recipe, "tag_rows"):
            return get_tags(recipe)  # type: ignore[arg-type]
    except Exception:
        pass
    return list(getattr(recipe, "tags", None) or [])


def _collect_recipe_allergens(recipe: Any) -> list[str]:
    try:
        from app.models.recipe import Recipe
        from app.services.recipe_storage import get_allergens

        if isinstance(recipe, Recipe) or hasattr(recipe, "allergen_rows"):
            return get_allergens(recipe)  # type: ignore[arg-type]
    except Exception:
        pass
    rows = getattr(recipe, "allergen_rows", None)
    if rows:
        return [getattr(row, "allergen", str(row)) for row in rows]
    return list(getattr(recipe, "allergens", None) or [])


def _collect_recipe_diets(recipe: Any) -> list[str]:
    return list(getattr(recipe, "diets", None) or [])


def _collect_recipe_restrictions(recipe: Any) -> list[str]:
    try:
        from app.models.recipe import Recipe
        from app.services.recipe_storage import get_restrictions

        if isinstance(recipe, Recipe) or hasattr(recipe, "restriction_rows"):
            return get_restrictions(recipe)  # type: ignore[arg-type]
    except Exception:
        pass
    rows = getattr(recipe, "restriction_rows", None)
    if rows:
        return [getattr(row, "restriction", str(row)) for row in rows]
    return list(getattr(recipe, "restrictions", None) or [])


def _collect_recipe_full_text(recipe: Any, ingredient_texts: list[str]) -> str:
    parts: list[str] = []
    for attr in ("title", "description"):
        value = getattr(recipe, attr, None)
        if value:
            parts.append(str(value))
    parts.extend(ingredient_texts)
    parts.extend(_collect_recipe_tags(recipe))
    parts.extend(_collect_recipe_diets(recipe))
    parts.extend(_collect_recipe_restrictions(recipe))
    parts.extend(_collect_recipe_allergens(recipe))
    return " ".join(parts).lower()


def _find_marker_match(
    markers: Iterable[str],
    ingredient_texts: list[str],
    full_text: str,
) -> tuple[str | None, str | None]:
    for ing in ingredient_texts:
        ing_lower = ing.lower()
        for marker in markers:
            m = marker.lower().strip()
            if m and m in ing_lower:
                return marker, ing
    for marker in markers:
        m = marker.lower().strip()
        if m and m in full_text:
            return marker, None
    return None, None


def _check_definition_markers(
    definition: RestrictionDefinition,
    ingredient_texts: list[str],
    full_text: str,
    *,
    source: ConflictSource,
    seen: set[tuple[str, str, str | None]],
    markers: tuple[str, ...],
    force_soft: bool = False,
) -> list[RestrictionConflict]:
    if not markers:
        return []
    matched_marker, matched_ingredient = _find_marker_match(markers, ingredient_texts, full_text)
    if not matched_marker:
        return []
    severity: Severity = "soft" if force_soft or definition.severity == "soft" else "hard"
    conflict = RestrictionConflict(
        restriction_key=definition.key,
        label_ru=definition.label_ru,
        severity=severity,
        reason=(
            f"Найден ингредиент «{matched_ingredient}» ({matched_marker})"
            if matched_ingredient
            else f"В рецепте есть «{matched_marker}»"
        ),
        matched_ingredient=matched_ingredient,
        source=source,
    )
    result: list[RestrictionConflict] = []
    _append_conflict(result, seen, conflict)
    return result


def _append_conflict(
    conflicts: list[RestrictionConflict],
    seen: set[tuple[str, str, str | None]],
    conflict: RestrictionConflict,
) -> None:
    key = (conflict.restriction_key, conflict.severity, conflict.matched_ingredient)
    if key in seen:
        return
    seen.add(key)
    conflicts.append(conflict)


def _token_conflicts_with_restriction(token: str, definition: RestrictionDefinition) -> bool:
    """True when a recipe tag/diet explicitly names a banned category."""
    token_l = token.lower()
    for marker in definition.banned_ingredient_markers:
        if marker.lower() in token_l or token_l in marker.lower():
            return True
    conflict_pairs = {
        "vegetarian": ("мясо", "мясной", "курица", "рыба"),
        "vegan": ("мясо", "сыр", "яйц", "молок"),
        "no_pork": ("свинин", "бекон", "ветчин"),
        "no_alcohol": ("алкогол", "вино", "пиво", "коктейл"),
    }
    for conflict_token in conflict_pairs.get(definition.key, ()):
        if conflict_token in token_l:
            return True
    return False
