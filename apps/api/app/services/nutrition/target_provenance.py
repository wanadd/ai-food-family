from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from app.models.progress import NutritionTarget

TargetOrigin = Literal["evidence_auto", "manual", "clinician", "legacy"]
ProvenanceStatus = Literal["unreviewed", "valid", "verified", "invalid", "needs_review"]

TARGET_ORIGINS: tuple[str, ...] = ("evidence_auto", "manual", "clinician", "legacy")
PROVENANCE_STATUSES: tuple[str, ...] = (
    "unreviewed",
    "valid",
    "verified",
    "invalid",
    "needs_review",
)
EVIDENCE_PROVENANCE_FIELDS: tuple[str, ...] = (
    "evidence_id",
    "source_id",
    "source_version",
    "calculation_method",
    "calculation_inputs_json",
    "calculated_at",
)


@dataclass(frozen=True)
class NutritionTargetValues:
    calories_target: int | None = None
    protein_target_g: int | None = None
    fat_target_g: int | None = None
    carbs_target_g: int | None = None
    fiber_target_g: int | None = None
    fiber_target_g_range: tuple[int, int] | None = None
    water_target_ml: int | None = None
    goal_type: str | None = None


@dataclass(frozen=True)
class NutritionTargetResolution:
    targets: NutritionTargetValues
    target_origin: TargetOrigin
    evidence_id: str | None = None
    source_id: str | None = None
    source_version: str | None = None
    calculation_method: str | None = None
    calculation_inputs: dict | None = None
    calculated_at: datetime | None = None
    provenance_status: ProvenanceStatus = "unreviewed"

    def __post_init__(self) -> None:
        if self.provenance_status not in PROVENANCE_STATUSES:
            raise ValueError(
                f"Unsupported nutrition provenance status: {self.provenance_status}"
            )
        validate_provenance(
            target_origin=self.target_origin,
            evidence_id=self.evidence_id,
            source_id=self.source_id,
            source_version=self.source_version,
            calculation_method=self.calculation_method,
            calculation_inputs=self.calculation_inputs,
            calculated_at=self.calculated_at,
        )


def validate_provenance(
    *,
    target_origin: str,
    evidence_id: str | None,
    source_id: str | None,
    source_version: str | None,
    calculation_method: str | None,
    calculation_inputs: dict | None,
    calculated_at: datetime | None,
) -> None:
    if target_origin not in TARGET_ORIGINS:
        raise ValueError(f"Unsupported nutrition target origin: {target_origin}")

    evidence_values = (
        evidence_id,
        source_id,
        source_version,
        calculation_method,
        calculation_inputs,
        calculated_at,
    )
    if target_origin == "evidence_auto":
        if any(value is None for value in evidence_values):
            raise ValueError("evidence_auto nutrition targets require full provenance")
        return

    if any(value is not None for value in evidence_values):
        raise ValueError(
            f"{target_origin} nutrition targets cannot include evidence provenance"
        )


def apply_resolution_to_row(
    row: NutritionTarget, resolution: NutritionTargetResolution
) -> None:
    for key, value in resolution.targets.__dict__.items():
        if key == "fiber_target_g_range":
            continue
        setattr(row, key, value)
    row.target_origin = resolution.target_origin
    row.provenance_status = resolution.provenance_status
    row.evidence_id = resolution.evidence_id
    row.source_id = resolution.source_id
    row.source_version = resolution.source_version
    row.calculation_method = resolution.calculation_method
    row.calculation_inputs_json = resolution.calculation_inputs
    row.calculated_at = resolution.calculated_at


def mark_manual_or_clinician(row: NutritionTarget, target_origin: str) -> None:
    validate_provenance(
        target_origin=target_origin,
        evidence_id=None,
        source_id=None,
        source_version=None,
        calculation_method=None,
        calculation_inputs=None,
        calculated_at=None,
    )
    row.target_origin = target_origin
    row.provenance_status = "needs_review" if target_origin == "clinician" else "valid"
    row.evidence_id = None
    row.source_id = None
    row.source_version = None
    row.calculation_method = None
    row.calculation_inputs_json = None
    row.calculated_at = None
