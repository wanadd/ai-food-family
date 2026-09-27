"""Deterministic Wave 2 food matching and safety contracts.

This module deliberately accepts canonical identifiers and explicit relations;
display text is never a safety proof.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from enum import StrEnum
from typing import Iterable


class KnowledgeState(StrEnum):
    UNKNOWN = "UNKNOWN"
    NOT_PROVIDED = "NOT_PROVIDED"
    KNOWN_NONE = "KNOWN_NONE"
    KNOWN_PRESENT = "KNOWN_PRESENT"
    DECLINED = "DECLINED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class ConfirmationState(StrEnum):
    UNCONFIRMED = "UNCONFIRMED"
    CONFIRMED = "CONFIRMED"
    NEEDS_RECONFIRMATION = "NEEDS_RECONFIRMATION"
    SUPERSEDED = "SUPERSEDED"


class SafetyState(StrEnum):
    BLOCK = "BLOCK"
    ESCALATE = "ESCALATE"
    UNKNOWN = "UNKNOWN"
    WARN = "WARN"
    SAFE = "SAFE"


SAFETY_PRECEDENCE = {state.value: index for index, state in enumerate(SafetyState)}
_NORMALIZE_RE = re.compile(r"[^\w\s-]+", re.UNICODE)


def normalize_alias(value: str) -> str:
    """Normalize an alias for exact lookup, without fuzzy or substring matching."""
    text = _NORMALIZE_RE.sub(" ", value.casefold())
    return " ".join(text.split())


@dataclass(frozen=True)
class FoodMatch:
    status: str
    food_identity_id: str | None = None
    identity_key: str | None = None
    reason: str = ""


def match_food(query: str, identities: Iterable[dict], aliases: Iterable[dict] = ()) -> FoodMatch:
    normalized = normalize_alias(query)
    if not normalized:
        return FoodMatch("UNSUPPORTED", reason="empty_query")
    candidates: dict[str, dict] = {}
    for row in identities:
        if normalize_alias(str(row.get("identity_key", ""))) == normalized or normalize_alias(str(row.get("display_name", ""))) == normalized:
            candidates[str(row["food_identity_id"])] = row
    for row in aliases:
        if normalize_alias(str(row.get("alias_text", ""))) == normalized:
            candidates[str(row["food_identity_id"])] = row
    if len(candidates) == 1:
        row = next(iter(candidates.values()))
        return FoodMatch("CANONICAL_EXACT", str(row["food_identity_id"]), row.get("identity_key"), "exact_mapping")
    if len(candidates) > 1:
        return FoodMatch("AMBIGUOUS", reason="multiple_explicit_mappings")
    return FoodMatch("UNSUPPORTED", reason="no_explicit_mapping")


def aggregate_safety(states: Iterable[str | SafetyState]) -> SafetyState:
    values = [SafetyState(state) for state in states]
    return min(values, key=lambda state: SAFETY_PRECEDENCE[state.value]) if values else SafetyState.UNKNOWN


# Keep the mapping explicit. An unmapped key is intentionally not promoted to
# a V2 safety concept merely because its spelling looks familiar.
LEGACY_RESTRICTION_MAPPING: dict[str, str | None] = {
    "no_pork": "dietary.no_pork", "no_beef": "dietary.no_beef", "halal": "dietary.halal",
    "kosher": "dietary.kosher", "no_alcohol": "dietary.no_alcohol", "diabetes_friendly": "medical.diabetes",
    "low_salt": "nutrition.low_salt", "low_sugar": "nutrition.low_sugar", "lactose_free": "intolerance.lactose",
    "gluten_free": "celiac.gluten", "pregnancy_safe": "pregnancy.process", "child_safe": "age.child",
    "vegetarian": "dietary.vegetarian", "vegan": "dietary.vegan", "pescatarian": "dietary.pescatarian",
    "keto": "dietary.keto", "low_carb": "nutrition.low_carb", "high_protein": "nutrition.high_protein",
    "weight_loss": "nutrition.weight_loss", "mass_gain": "nutrition.mass_gain", "healthy_eating": None,
    "no_nuts": "allergen.tree_nut", "no_peanuts": "allergen.peanut", "no_eggs": "allergen.egg",
    "no_fish": "allergen.fish", "no_seafood": "allergen.shellfish", "no_soy": "allergen.soy",
    "no_milk": "allergen.milk",
}


def derive_age(birth_date: date | None, *, at: date | None = None) -> int | None:
    if birth_date is None:
        return None
    today = at or date.today()
    if birth_date > today:
        return None
    return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))


def evaluate_safety(*, profile_facts: Iterable[dict], food_relations: Iterable[dict], evidence_backed: bool, process_known: bool = True) -> tuple[SafetyState, list[str]]:
    """Evaluate explicit typed facts; missing context fails closed."""
    facts = list(profile_facts)
    relations = list(food_relations)
    reasons: list[str] = []
    if not evidence_backed or not process_known:
        return SafetyState.UNKNOWN, ["insufficient_evidence_or_process"]
    for fact in facts:
        state = fact.get("knowledge_state")
        if state in {KnowledgeState.UNKNOWN.value, KnowledgeState.NOT_PROVIDED.value, KnowledgeState.DECLINED.value}:
            reasons.append("profile_fact_unknown")
            continue
        if state != KnowledgeState.KNOWN_PRESENT.value:
            continue
        concept = str(fact.get("fact_key", ""))
        for relation in relations:
            if relation.get("concept") != concept:
                continue
            relation_state = relation.get("relation")
            if relation_state in {"CONTAINS", "MAY_CONTAIN", "CROSS_CONTACT"}:
                return SafetyState.BLOCK, [f"explicit_relation:{relation_state}"]
            if relation_state == "UNKNOWN":
                return SafetyState.UNKNOWN, ["unknown_explicit_relation"]
    if reasons:
        return SafetyState.UNKNOWN, reasons
    return SafetyState.SAFE, ["explicit_evidence_and_no_conflict"]
