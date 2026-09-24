from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True)
class NutritionTargetInterval:
    """Half-open [effective_from, effective_to) interval; None means infinity."""

    effective_from: datetime
    effective_to: datetime | None = None

    def contains(self, instant: datetime) -> bool:
        return self.effective_from <= instant and (self.effective_to is None or instant < self.effective_to)

    def overlaps(self, other: "NutritionTargetInterval") -> bool:
        left_end = self.effective_to or datetime.max.replace(tzinfo=self.effective_from.tzinfo)
        right_end = other.effective_to or datetime.max.replace(tzinfo=other.effective_from.tzinfo)
        return self.effective_from < right_end and other.effective_from < left_end


@dataclass(frozen=True)
class NutritionTargetProvenance:
    origin: str
    provenance_status: str
    source_rule_version: str | None = None
    calculation_version: str | None = None
    evaluation_date: date | None = None


def age_at_evaluation(birth_date: date | None, evaluation_date: date) -> int | None:
    if birth_date is None:
        return None
    return evaluation_date.year - birth_date.year - ((evaluation_date.month, evaluation_date.day) < (birth_date.month, birth_date.day))


def is_legacy_estimator(provenance: NutritionTargetProvenance) -> bool:
    return provenance.origin == "LEGACY_ESTIMATOR"


def can_claim_authoritative(provenance: NutritionTargetProvenance) -> bool:
    return provenance.origin == "EVIDENCE_BACKED" and provenance.provenance_status == "AUTHORITATIVE"
