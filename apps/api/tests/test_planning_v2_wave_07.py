from datetime import date

import pytest

from app.planning.v2_contracts import (
    PlanSlotV2,
    SlotParticipant,
    SlotPortion,
    clear_slot,
    enrich_slot_without_reanimation,
    per_person_portions,
)


def _slot(**kwargs):
    return PlanSlotV2("2026-09-24:dinner", date(2026, 9, 24), "dinner", **kwargs)


def test_explicit_empty_survives_read_and_enrichment():
    empty = clear_slot(_slot(slot_state="ASSIGNED", recipe_version_id="v1"))
    assert empty.slot_state == "EMPTY"
    assert empty.recipe_version_id is None
    assert enrich_slot_without_reanimation(empty, "v2") == empty


def test_assigned_slot_requires_recipe_version():
    with pytest.raises(ValueError):
        _slot(slot_state="ASSIGNED")


def test_replacement_is_explicit_and_does_not_mutate_previous_slot():
    old = _slot(slot_state="ASSIGNED", recipe_version_id="v1")
    replacement = _slot(slot_state="ASSIGNED", recipe_version_id="v2", manual_override=True)
    assert old.recipe_version_id == "v1"
    assert replacement.recipe_version_id == "v2"
    assert replacement.manual_override


def test_participants_and_portions_are_person_scoped():
    participants = [SlotParticipant("adult"), SlotParticipant("child")]
    portions = per_person_portions([SlotPortion("adult", 1, "portion", "EXPLICIT"), SlotPortion("child", 0.5, "portion", "CHILD_FALLBACK")])
    assert {item.person_id for item in participants} == {"adult", "child"}
    assert portions["child"].value == 0.5
    assert portions["adult"].source_kind == "EXPLICIT"


def test_missing_portion_is_unknown_not_zero():
    assert SlotPortion("child").value is None
