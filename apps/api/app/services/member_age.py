"""Age in months for virtual family members (menu + display)."""

from __future__ import annotations

MAX_AGE_MONTHS = 130 * 12


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
