from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class ReconciliationLevel(StrEnum):
    MATCH = "MATCH"
    EXPECTED_DIFFERENCE = "EXPECTED_DIFFERENCE"
    RECONFIRM_REQUIRED = "RECONFIRM_REQUIRED"
    MISSING_V2 = "MISSING_V2"
    UNEXPECTED_V2 = "UNEXPECTED_V2"
    CONFLICT = "CONFLICT"
    ERROR = "ERROR"


class IdentityResolutionStatus(StrEnum):
    RESOLVED = "RESOLVED"
    MISSING_MAPPING = "MISSING_MAPPING"
    AMBIGUOUS_MAPPING = "AMBIGUOUS_MAPPING"
    CONFLICTING_MAPPING = "CONFLICTING_MAPPING"
    INVALID_MAPPING = "INVALID_MAPPING"
    ERROR = "ERROR"


@dataclass(frozen=True)
class IdentityResolution:
    status: IdentityResolutionStatus
    canonical_id: str | None = None
    reason: str = ""


@dataclass(frozen=True)
class ReconciliationResult:
    source_id: str
    level: ReconciliationLevel
    reason: str = ""
    severity: str = "INFORMATIONAL"
    identity_resolution: IdentityResolutionStatus = IdentityResolutionStatus.RESOLVED


@dataclass
class ReconciliationReport:
    results: list[ReconciliationResult] = field(default_factory=list)

    def add(
        self,
        source_id: str,
        level: ReconciliationLevel,
        reason: str = "",
        severity: str = "INFORMATIONAL",
        identity_resolution: IdentityResolutionStatus = IdentityResolutionStatus.RESOLVED,
    ) -> None:
        self.results.append(ReconciliationResult(source_id, level, reason, severity, identity_resolution))

    def counts(self) -> dict[str, int]:
        return {level.value: sum(item.level is level for item in self.results) for level in ReconciliationLevel}

    @property
    def unresolved_p0(self) -> int:
        return sum(item.severity == "P0_BLOCKER" for item in self.results if item.level is ReconciliationLevel.CONFLICT)

    @property
    def unexplained_source_loss(self) -> int:
        return sum(item.level in {ReconciliationLevel.MISSING_V2, ReconciliationLevel.ERROR} for item in self.results)


def compare_logical(source_id: str, legacy: Any, v2: Any, *, expected_difference: bool = False, reason: str = "") -> ReconciliationResult:
    if legacy == v2:
        return ReconciliationResult(source_id, ReconciliationLevel.MATCH, reason)
    if expected_difference:
        return ReconciliationResult(source_id, ReconciliationLevel.EXPECTED_DIFFERENCE, reason or "known unsafe legacy semantics")
    if v2 is None:
        return ReconciliationResult(source_id, ReconciliationLevel.MISSING_V2, reason)
    return ReconciliationResult(source_id, ReconciliationLevel.CONFLICT, reason or "logical values differ", "P1_REVIEW")


def accounting(source_count: int, outcomes: dict[str, int]) -> bool:
    return source_count == sum(outcomes.get(key, 0) for key in ("MIGRATED", "RECOMPUTED", "RECONFIRM_REQUIRED", "ARCHIVED", "SKIPPED_BY_POLICY", "ERROR"))
