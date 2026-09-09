from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Literal

from app.models.family import FamilyMember
from app.models.user_profile import UserProfile
from app.services.family_member_nutrition import virtual_nutrition_from_member
from app.services.nutrition.target_provenance import (
    NutritionTargetResolution,
    NutritionTargetValues,
)

DATASET_PATH = (
    Path(__file__).resolve().parent
    / "evidence_data"
    / "mr_2_3_1_0253_21_macro_targets_v1.json"
)
DATASET_ID = "PLANAM-MR-0253-21-MACRO-TARGETS-v1"
SOURCE_ID = "SRC-RU-MR-0253-21"
SOURCE_VERSION = "MR-2.3.1.0253-21@2021-07-22"
EVIDENCE_ID = "EV-NT-001"
CALCULATION_METHOD = "mr_2_3_1_0253_21_table_lookup_v1"

ResolutionStatus = Literal[
    "resolved", "insufficient_data", "unsupported_scope", "ambiguous_input"
]
Population = Literal["adult", "child"]

ADULT_ACTIVITY_GROUPS = {
    "kfa_1_4",
    "kfa_1_6",
    "kfa_1_9",
    "kfa_2_2",
    "kfa_1_7_desired",
}
LIFE_STAGES = {
    "none",
    "pregnancy_trimester_1",
    "pregnancy_trimester_2",
    "pregnancy_trimester_3",
    "lactation_months_1_6",
    "lactation_months_7_12",
}


@dataclass(frozen=True)
class TargetResolverFacts:
    age_years: int | None = None
    age_months: int | None = None
    sex: str | None = None
    physical_activity_group: str | None = None
    life_stage: str | None = None
    nutrition_goal: str | None = None


@dataclass(frozen=True)
class TargetResolverResult:
    status: ResolutionStatus
    reason: str | None = None
    resolution: NutritionTargetResolution | None = None

    @property
    def resolved(self) -> bool:
        return self.status == "resolved" and self.resolution is not None


def facts_from_user_profile(profile: UserProfile) -> TargetResolverFacts:
    return TargetResolverFacts(
        age_years=profile.age,
        sex=_normalize_sex(profile.gender),
        physical_activity_group=profile.physical_activity_group,
        life_stage=profile.life_stage,
        nutrition_goal=profile.nutrition_goal,
    )


def facts_from_family_member(member: FamilyMember) -> TargetResolverFacts:
    nutrition = virtual_nutrition_from_member(member)
    raw_sex = nutrition.sex or nutrition.gender
    return TargetResolverFacts(
        age_months=nutrition.age_months,
        sex=_normalize_sex(raw_sex),
        life_stage=nutrition.life_stage,
        nutrition_goal=nutrition.nutrition_goal,
    )


def resolve_evidence_targets(
    facts: TargetResolverFacts,
    *,
    calculated_at: datetime | None = None,
) -> TargetResolverResult:
    data = load_dataset()
    integrity_error = validate_dataset(data)
    if integrity_error is not None:
        return TargetResolverResult(status="ambiguous_input", reason=integrity_error)

    age = _resolve_age(facts)
    if age.status != "resolved":
        return TargetResolverResult(status=age.status, reason=age.reason)

    assert age.population is not None
    assert age.age_years is not None
    if age.population == "adult":
        row_result = _resolve_adult_row(data, age.age_years, facts)
    else:
        row_result = _resolve_child_row(data, age.age_years, facts)
    if row_result.status != "resolved":
        return TargetResolverResult(status=row_result.status, reason=row_result.reason)

    row = row_result.row
    assert row is not None
    targets = dict(row["targets"])
    applied_adjustments: list[dict] = []
    life_stage = facts.life_stage or "none"
    if life_stage not in LIFE_STAGES:
        return TargetResolverResult(
            status="ambiguous_input", reason="unknown_life_stage"
        )
    if life_stage != "none":
        if age.population != "adult" or facts.sex != "female":
            return TargetResolverResult(
                status="unsupported_scope", reason="life_stage_requires_adult_female"
            )
        adjustment = _find_life_stage_adjustment(data, life_stage)
        if adjustment is None:
            return TargetResolverResult(
                status="unsupported_scope", reason="life_stage_not_in_dataset"
            )
        targets["energy_kcal"] += adjustment["energy_kcal_add"]
        targets["protein_g"] += adjustment["protein_g_add"]
        targets["fat_g"] += adjustment["fat_g_add"]
        targets["carbs_g"] += adjustment["carbs_g_add"]
        applied_adjustments.append(
            {
                "life_stage": life_stage,
                "source_table": adjustment["source_table"],
                "energy_kcal_add": adjustment["energy_kcal_add"],
                "protein_g_add": adjustment["protein_g_add"],
                "fat_g_add": adjustment["fat_g_add"],
                "carbs_g_add": adjustment["carbs_g_add"],
            }
        )

    fiber_range = targets.get("fiber_g_range")
    selected_row_key = _row_key(row)
    calculation_inputs = {
        "dataset_id": data["dataset_id"],
        "age_source": age.age_source,
        "age_years": age.age_years,
        "age_months": facts.age_months,
        "population": age.population,
        "selected_age_band": row["age_band_years"],
        "sex": row["sex"],
        "physical_activity_group": row.get("physical_activity_group"),
        "life_stage": life_stage,
        "nutrition_goal": facts.nutrition_goal,
        "selected_dataset_row_key": selected_row_key,
        "source_table": row["source_table"],
        "fiber_g_range": fiber_range,
        "applied_adjustments": applied_adjustments,
    }
    return TargetResolverResult(
        status="resolved",
        resolution=NutritionTargetResolution(
            targets=NutritionTargetValues(
                calories_target=targets["energy_kcal"],
                protein_target_g=targets["protein_g"],
                fat_target_g=targets["fat_g"],
                carbs_target_g=targets["carbs_g"],
                fiber_target_g=None,
                fiber_target_g_range=tuple(fiber_range) if fiber_range else None,
                water_target_ml=None,
                goal_type=facts.nutrition_goal,
            ),
            target_origin="evidence_auto",
            provenance_status="verified",
            evidence_id=EVIDENCE_ID,
            source_id=SOURCE_ID,
            source_version=SOURCE_VERSION,
            calculation_method=CALCULATION_METHOD,
            calculation_inputs=calculation_inputs,
            calculated_at=calculated_at or datetime.now(timezone.utc),
        ),
    )


@dataclass(frozen=True)
class _AgeResult:
    status: ResolutionStatus
    reason: str | None = None
    age_years: int | None = None
    age_source: str | None = None
    population: Population | None = None


@dataclass(frozen=True)
class _RowResult:
    status: ResolutionStatus
    reason: str | None = None
    row: dict | None = None


def _resolve_age(facts: TargetResolverFacts) -> _AgeResult:
    if facts.age_months is not None:
        if facts.age_months < 0:
            return _AgeResult(status="ambiguous_input", reason="negative_age_months")
        if facts.age_months < 12:
            return _AgeResult(status="unsupported_scope", reason="infant_scope")
        age_years = facts.age_months // 12
        population: Population = "child" if facts.age_months < 18 * 12 else "adult"
        return _AgeResult(
            status="resolved",
            age_years=age_years,
            age_source="age_months",
            population=population,
        )
    if facts.age_years is None:
        return _AgeResult(status="insufficient_data", reason="missing_age")
    if facts.age_years < 0:
        return _AgeResult(status="ambiguous_input", reason="negative_age_years")
    if facts.age_years < 1:
        return _AgeResult(status="unsupported_scope", reason="infant_scope")
    return _AgeResult(
        status="resolved",
        age_years=facts.age_years,
        age_source="age_years",
        population="child" if facts.age_years < 18 else "adult",
    )


def _resolve_adult_row(
    data: dict, age_years: int, facts: TargetResolverFacts
) -> _RowResult:
    sex = _normalize_sex(facts.sex)
    if sex is None:
        return _RowResult(status="insufficient_data", reason="missing_sex")
    if sex not in {"male", "female"}:
        return _RowResult(status="ambiguous_input", reason="unsupported_sex")
    activity = facts.physical_activity_group
    if not activity:
        return _RowResult(
            status="insufficient_data", reason="missing_physical_activity_group"
        )
    if activity not in ADULT_ACTIVITY_GROUPS:
        return _RowResult(
            status="ambiguous_input", reason="unknown_physical_activity_group"
        )

    age_band = adult_age_band(age_years)
    if age_band is None:
        return _RowResult(status="unsupported_scope", reason="adult_age_out_of_scope")
    row = _find_row(
        data["adult_rows"],
        population="adult",
        sex=sex,
        age_band=age_band,
        physical_activity_group=activity,
    )
    if row is None:
        return _RowResult(status="unsupported_scope", reason="dataset_row_not_found")
    return _RowResult(status="resolved", row=row)


def _resolve_child_row(
    data: dict, age_years: int, facts: TargetResolverFacts
) -> _RowResult:
    age_band = child_age_band(age_years)
    if age_band is None:
        return _RowResult(status="unsupported_scope", reason="child_age_out_of_scope")
    required_sex = age_band in {"11-14", "15-17"}
    sex = _normalize_sex(facts.sex)
    if required_sex:
        if sex is None:
            return _RowResult(status="insufficient_data", reason="missing_child_sex")
        if sex not in {"male", "female"}:
            return _RowResult(status="ambiguous_input", reason="unsupported_child_sex")
    row = _find_row(
        data["child_rows"],
        population="child",
        sex=sex if required_sex else "any",
        age_band=age_band,
        physical_activity_group=None,
    )
    if row is None:
        return _RowResult(status="unsupported_scope", reason="dataset_row_not_found")
    return _RowResult(status="resolved", row=row)


def adult_age_band(age_years: int) -> str | None:
    if 18 <= age_years <= 29:
        return "18-29"
    if 30 <= age_years <= 44:
        return "30-44"
    if 45 <= age_years <= 64:
        return "45-64"
    if 65 <= age_years <= 74:
        return "65-74"
    if age_years >= 75:
        return "75+"
    return None


def child_age_band(age_years: int) -> str | None:
    if 1 <= age_years <= 2:
        return "1-2"
    if 3 <= age_years <= 6:
        return "3-6"
    if 7 <= age_years <= 10:
        return "7-10"
    if 11 <= age_years <= 14:
        return "11-14"
    if 15 <= age_years <= 17:
        return "15-17"
    return None


@lru_cache(maxsize=1)
def load_dataset() -> dict:
    with DATASET_PATH.open(encoding="utf-8") as fh:
        return json.load(fh)


def validate_dataset(data: dict) -> str | None:
    if data.get("dataset_id") != DATASET_ID:
        return "unexpected_dataset_id"
    if data.get("source_id") != SOURCE_ID:
        return "unexpected_source_id"
    if data.get("source_version") != SOURCE_VERSION:
        return "unexpected_source_version"

    keys: set[str] = set()
    for row in [*data.get("adult_rows", []), *data.get("child_rows", [])]:
        key = _row_key(row)
        if key in keys:
            return "duplicate_dataset_row_key"
        keys.add(key)

    for sex in ("male", "female"):
        for band in ("18-29", "30-44", "45-64"):
            for activity in ("kfa_1_4", "kfa_1_6", "kfa_1_9", "kfa_2_2"):
                if _find_row(data["adult_rows"], "adult", sex, band, activity) is None:
                    return "missing_adult_activity_row"
        for band in ("65-74", "75+"):
            if (
                _find_row(
                    data["adult_rows"], "adult", sex, band, "kfa_1_7_desired"
                )
                is None
            ):
                return "missing_older_adult_row"

    for band in ("1-2", "3-6", "7-10"):
        if _find_row(data["child_rows"], "child", "any", band, None) is None:
            return "missing_child_general_row"
    for sex in ("male", "female"):
        for band in ("11-14", "15-17"):
            if _find_row(data["child_rows"], "child", sex, band, None) is None:
                return "missing_child_sex_specific_row"
    return None


def _find_row(
    rows: list[dict],
    population: str,
    sex: str,
    age_band: str,
    physical_activity_group: str | None,
) -> dict | None:
    for row in rows:
        if (
            row["population"] == population
            and row["sex"] == sex
            and row["age_band_years"] == age_band
            and row.get("physical_activity_group") == physical_activity_group
        ):
            return row
    return None


def _find_life_stage_adjustment(data: dict, life_stage: str) -> dict | None:
    for adjustment in data.get("life_stage_adjustments", []):
        if adjustment["life_stage"] == life_stage:
            return adjustment
    return None


def _row_key(row: dict) -> str:
    return "|".join(
        [
            str(row["population"]),
            str(row["sex"]),
            str(row["age_band_years"]),
            str(row.get("physical_activity_group") or "none"),
        ]
    )


def _normalize_sex(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip().lower()
    if normalized == "gender_male":
        return "male"
    if normalized == "gender_female":
        return "female"
    return normalized or None
