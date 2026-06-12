"""Profile / nutrition profile validation — PLANAM V1.

New, centralized validators for the profile write-path. Pure functions, no DB
access. The goal is that *every* profile save (user nutrition profile and
family member nutrition) passes the same cleaning rules:

* trim whitespace on free-text fields;
* drop empty strings from list fields;
* de-duplicate allergies / diets / restrictions case-insensitively while
  preserving the original order and original casing of the first occurrence;
* never drop unknown-but-non-empty values (we do not have a closed vocabulary
  for allergies/diets, so we only clean — we do not reject).

These helpers are intentionally schema-agnostic where possible so they can be
reused by the API layer, the family member nutrition service and the project
health audit.
"""

from __future__ import annotations

from typing import Any, TypeVar

from app.nutrition.restrictions_catalog import normalize_restrictions

_T = TypeVar("_T")


def clean_text(value: str | None) -> str:
    """Trim a free-text field. ``None`` becomes an empty string."""
    return (value or "").strip()


def normalize_string_list(values: Any) -> list[str]:
    """Clean a list of tags: trim, drop empties, dedupe case-insensitively.

    Order and original casing of the first occurrence are preserved.
    """
    if not values:
        return []
    if isinstance(values, str):
        values = [values]
    result: list[str] = []
    seen: set[str] = set()
    for raw in values:
        if raw is None:
            continue
        item = str(raw).strip()
        if not item:
            continue
        key = item.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def normalize_profile_dict(data: dict[str, Any]) -> dict[str, Any]:
    """Normalize a profile-shaped dict in place-safe manner (returns new dict).

    Recognized list fields are de-duplicated; recognized text fields trimmed.
    Unknown keys are passed through untouched.
    """
    cleaned = dict(data)
    for list_field in ("allergies", "diets", "goals"):
        if list_field in cleaned:
            cleaned[list_field] = normalize_string_list(cleaned.get(list_field))
    if "restrictions" in cleaned:
        cleaned["restrictions"] = normalize_restrictions(cleaned.get("restrictions"))
    for text_field in (
        "medical_restrictions",
        "banned_foods",
        "favorite_foods",
        "disliked_foods",
    ):
        if text_field in cleaned:
            cleaned[text_field] = clean_text(cleaned.get(text_field))
    return cleaned


def normalize_member_nutrition(data: dict[str, Any] | None) -> dict[str, Any]:
    """Normalize a virtual family member ``nutrition_profile`` JSONB dict."""
    if not data:
        return {}
    return normalize_profile_dict(data)


def normalize_profile_payload(payload: _T) -> _T:
    """Normalize a Pydantic ``NutritionProfileData``-like payload.

    Works on any object exposing the standard profile attributes; returns a
    ``model_copy`` with cleaned values when available, otherwise mutates and
    returns the same object. Safe to call on the API payload before persisting.
    """
    updates: dict[str, Any] = {}

    for list_field in ("allergies", "diets"):
        if hasattr(payload, list_field):
            updates[list_field] = normalize_string_list(getattr(payload, list_field))

    if hasattr(payload, "restrictions"):
        updates["restrictions"] = normalize_restrictions(getattr(payload, "restrictions"))

    for text_field in (
        "medical_restrictions",
        "banned_foods",
        "favorite_foods",
        "disliked_foods",
    ):
        if hasattr(payload, text_field):
            updates[text_field] = clean_text(getattr(payload, text_field))

    model_copy = getattr(payload, "model_copy", None)
    if callable(model_copy):
        return model_copy(update=updates)  # type: ignore[return-value]

    for key, value in updates.items():
        setattr(payload, key, value)
    return payload


__all__ = [
    "clean_text",
    "normalize_string_list",
    "normalize_profile_dict",
    "normalize_member_nutrition",
    "normalize_profile_payload",
]
