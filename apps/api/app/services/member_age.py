"""Canonical age resolution for account and virtual family profiles."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

MAX_AGE_MONTHS = 130 * 12
AgeResolutionStatus = Literal[
    "resolved", "resolved_legacy_precision", "ambiguous_input", "unknown"
]
AgeSource = Literal["age_months", "legacy_years", "none"]
Population = Literal["infant", "child", "adult", "unknown"]


@dataclass(frozen=True)
class AgeResolution:
    age_source: AgeSource
    age_months: int | None
    age_years_floor: int | None
    population_scope: str
    age_band: str | None
    is_infant: bool
    is_child: bool
    is_adult: bool
    resolution_status: AgeResolutionStatus
    resolution_reason: str | None = None
    precision: Literal["months", "years", "none"] = "none"
    has_conflict: bool = False


def months_from_years(years: int) -> int:
    return max(0, years) * 12


def normalize_age_months(
    *,
    age_months: int | None = None,
    age_years: int | None = None,
    age: int | None = None,
) -> int | None:
    """Resolve canonical age_months from stored fields (backward compatible)."""
    if age_months is not None and age_months >= 0:
        return min(age_months, MAX_AGE_MONTHS)
    if age_years is not None and age_years >= 0:
        return min(months_from_years(age_years), MAX_AGE_MONTHS)
    if age is not None and age >= 0:
        return min(months_from_years(age), MAX_AGE_MONTHS)
    return None


def resolve_age(
    *,
    age_months: int | None = None,
    age: int | None = None,
    age_years: int | None = None,
) -> AgeResolution:
    legacy_years = age if age is not None else age_years
    if age_months is not None:
        if age_months < 0:
            return _unknown("negative_age_months", status="ambiguous_input")
        bounded_months = min(age_months, MAX_AGE_MONTHS)
        years_floor = bounded_months // 12
        conflict = (
            legacy_years is not None
            and legacy_years >= 0
            and legacy_years != years_floor
        )
        scope, band, population = _scope_for_months(bounded_months)
        return AgeResolution(
            age_source="age_months",
            age_months=bounded_months,
            age_years_floor=years_floor,
            population_scope=scope,
            age_band=band,
            is_infant=population == "infant",
            is_child=population == "child",
            is_adult=population == "adult",
            resolution_status="ambiguous_input" if conflict else "resolved",
            resolution_reason="age_months_age_conflict" if conflict else None,
            precision="months",
            has_conflict=conflict,
        )

    if legacy_years is None:
        return _unknown("missing_age")
    if legacy_years < 0:
        return _unknown("negative_age_years", status="ambiguous_input")
    if legacy_years == 0:
        return AgeResolution(
            age_source="legacy_years",
            age_months=None,
            age_years_floor=0,
            population_scope="infant_0_11_months",
            age_band="infant_0_11_months",
            is_infant=True,
            is_child=False,
            is_adult=False,
            resolution_status="resolved_legacy_precision",
            precision="years",
        )

    scope, band, population = _scope_for_legacy_years(legacy_years)
    return AgeResolution(
        age_source="legacy_years",
        age_months=None,
        age_years_floor=legacy_years,
        population_scope=scope,
        age_band=band,
        is_infant=population == "infant",
        is_child=population == "child",
        is_adult=population == "adult",
        resolution_status="resolved_legacy_precision",
        precision="years",
    )


def resolve_age_for_profile(profile) -> AgeResolution:
    return resolve_age(
        age_months=getattr(profile, "age_months", None),
        age=getattr(profile, "age", None),
    )


def age_resolution_to_dict(resolution: AgeResolution) -> dict:
    return {
        "age_source": resolution.age_source,
        "age_months": resolution.age_months,
        "age_years_floor": resolution.age_years_floor,
        "population_scope": resolution.population_scope,
        "age_band": resolution.age_band,
        "is_infant": resolution.is_infant,
        "is_child": resolution.is_child,
        "is_adult": resolution.is_adult,
        "resolution_status": resolution.resolution_status,
        "resolution_reason": resolution.resolution_reason,
        "precision": resolution.precision,
        "has_conflict": resolution.has_conflict,
    }


def nutrition_target_age_band(resolution: AgeResolution) -> str | None:
    """Return P0-A2 MR lookup band label for a resolved age."""
    if resolution.population_scope == "child_1_2":
        return "1-2"
    if resolution.population_scope == "child_3_6":
        return "3-6"
    if resolution.population_scope == "child_7_10":
        return "7-10"
    if resolution.population_scope == "child_11_14":
        return "11-14"
    if resolution.population_scope == "child_15_17":
        return "15-17"
    years = resolution.age_years_floor
    if years is None or not resolution.is_adult:
        return None
    if 18 <= years <= 29:
        return "18-29"
    if 30 <= years <= 44:
        return "30-44"
    if 45 <= years <= 64:
        return "45-64"
    if 65 <= years <= 74:
        return "65-74"
    if years >= 75:
        return "75+"
    return None


def format_age_resolution_ru(resolution: AgeResolution) -> str:
    if resolution.age_months is not None:
        return format_age_months_ru(resolution.age_months)
    if resolution.age_years_floor is not None:
        suffix = "точность: годы"
        return f"{_years_word(resolution.age_years_floor)} ({suffix})"
    return "возраст не указан"


def _scope_for_months(age_months: int) -> tuple[str, str, Population]:
    if 0 <= age_months <= 11:
        return "infant_0_11_months", "infant_0_11_months", "infant"
    if 12 <= age_months <= 35:
        return "child_1_2", "child_1_2", "child"
    if 36 <= age_months <= 83:
        return "child_3_6", "child_3_6", "child"
    if 84 <= age_months <= 131:
        return "child_7_10", "child_7_10", "child"
    if 132 <= age_months <= 179:
        return "child_11_14", "child_11_14", "child"
    if 180 <= age_months <= 215:
        return "child_15_17", "child_15_17", "child"
    return "adult_18_plus", "adult_18_plus", "adult"


def _scope_for_legacy_years(age_years: int) -> tuple[str, str, Population]:
    if age_years < 1:
        return "infant_0_11_months", "infant_0_11_months", "infant"
    if 1 <= age_years <= 2:
        return "child_1_2", "child_1_2", "child"
    if 3 <= age_years <= 6:
        return "child_3_6", "child_3_6", "child"
    if 7 <= age_years <= 10:
        return "child_7_10", "child_7_10", "child"
    if 11 <= age_years <= 14:
        return "child_11_14", "child_11_14", "child"
    if 15 <= age_years <= 17:
        return "child_15_17", "child_15_17", "child"
    return "adult_18_plus", "adult_18_plus", "adult"


def _unknown(
    reason: str,
    *,
    status: AgeResolutionStatus = "unknown",
) -> AgeResolution:
    return AgeResolution(
        age_source="none",
        age_months=None,
        age_years_floor=None,
        population_scope="unknown",
        age_band=None,
        is_infant=False,
        is_child=False,
        is_adult=False,
        resolution_status=status,
        resolution_reason=reason,
    )


def validate_age_months(age_months: int, *, is_child: bool = False) -> None:
    if age_months < 0:
        raise ValueError("Возраст не может быть отрицательным")
    if age_months > MAX_AGE_MONTHS:
        raise ValueError("Слишком большой возраст")
    if is_child and age_months > 18 * 12:
        raise ValueError("Для ребёнка укажите возраст до 18 лет")


def format_age_months_ru(age_months: int | None, *, kind: str | None = None) -> str:
    if age_months is None or age_months < 0:
        return "возраст не указан"

    years = age_months // 12
    months = age_months % 12

    if years == 0:
        text = _months_word(months)
    elif months == 0:
        text = _years_word(years)
    else:
        text = f"{_years_word(years)} {_months_word(months)}"

    if kind == "child":
        return f"Ребёнок, {text}"
    if kind == "elder":
        return f"Пожилой родственник, {text}"
    return text


def format_age_short_ru(age_months: int | None) -> str:
    if age_months is None:
        return "—"
    years = age_months // 12
    months = age_months % 12
    if years == 0:
        return _months_word(months)
    if months == 0:
        return _years_word(years)
    return f"{_years_word(years)} {_months_word(months)}"


def _years_word(n: int) -> str:
    n = abs(n)
    if n % 10 == 1 and n % 100 != 11:
        return f"{n} год"
    if 2 <= n % 10 <= 4 and (n % 100 < 10 or n % 100 >= 20):
        return f"{n} года"
    return f"{n} лет"


def _months_word(n: int) -> str:
    n = abs(n)
    if n % 10 == 1 and n % 100 != 11:
        return f"{n} месяц"
    if 2 <= n % 10 <= 4 and (n % 100 < 10 or n % 100 >= 20):
        return f"{n} месяца"
    return f"{n} месяцев"
