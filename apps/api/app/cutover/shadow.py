from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from app.cutover.reconciliation import ReconciliationLevel, ReconciliationResult, compare_logical


@dataclass(frozen=True)
class ShadowComparison:
    flow: str
    result: ReconciliationResult


def run_shadow_read(flow: str, legacy_reader: Callable[[], Any], v2_reader: Callable[[], Any], *, expected_difference: bool = False, reason: str = "") -> ShadowComparison:
    return ShadowComparison(flow, compare_logical(flow, legacy_reader(), v2_reader(), expected_difference=expected_difference, reason=reason))


def supported_shadow_flows() -> tuple[str, ...]:
    return ("identity", "profile", "recipe", "menu", "explicit_empty", "shopping", "pantry", "cooking_consumption", "health", "entitlements")
