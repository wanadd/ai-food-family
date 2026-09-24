from datetime import date, datetime, timezone

from app.nutrition.target_contracts import (
    NutritionTargetInterval,
    NutritionTargetProvenance,
    age_at_evaluation,
    can_claim_authoritative,
    is_legacy_estimator,
)


def _dt(day: int) -> datetime:
    return datetime(2026, 1, day, tzinfo=timezone.utc)


def test_intervals_are_half_open_and_adjacent_intervals_do_not_overlap():
    first = NutritionTargetInterval(_dt(1), _dt(10))
    second = NutritionTargetInterval(_dt(10), _dt(20))
    assert first.contains(_dt(1))
    assert not first.contains(_dt(10))
    assert not first.overlaps(second)


def test_open_ended_interval_overlaps_a_later_interval():
    assert NutritionTargetInterval(_dt(1)).overlaps(NutritionTargetInterval(_dt(20), _dt(30)))


def test_different_scopes_are_independent_at_contract_layer():
    left = NutritionTargetInterval(_dt(1), _dt(20))
    right = NutritionTargetInterval(_dt(10), _dt(30))
    assert left.overlaps(right)
    assert ("person-a", "calories") != ("person-b", "calories")
    assert ("person-a", "calories") != ("person-a", "protein")


def test_age_is_derived_only_when_birth_date_is_known():
    assert age_at_evaluation(date(2010, 5, 20), date(2026, 5, 19)) == 15
    assert age_at_evaluation(None, date(2026, 5, 19)) is None


def test_legacy_estimator_remains_distinguishable_from_authoritative_evidence():
    legacy = NutritionTargetProvenance("LEGACY_ESTIMATOR", "UNREVIEWED")
    evidence = NutritionTargetProvenance("EVIDENCE_BACKED", "AUTHORITATIVE", "RULE-1", "CALC-1")
    assert is_legacy_estimator(legacy)
    assert not can_claim_authoritative(legacy)
    assert can_claim_authoritative(evidence)
