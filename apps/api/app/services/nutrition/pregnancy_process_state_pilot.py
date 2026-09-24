"""Pregnancy food/process-state dry-run foundation for P0-DATA-FOUNDATION-01B4.

This module creates non-persistent process-state facts for audit simulation. It
keeps food identity separate from process state and feeds only explicit,
accepted facts into the existing P0-E pregnancy decision contract.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from types import SimpleNamespace
import hashlib
import re
from typing import Any, Literal

from app.nutrition.medical_safety import evaluate_medical_safety
from app.services.nutrition.food_identity_foundation import (
    dry_run_food_match,
    normalize_ingredient_name,
)

ProcessState = Literal[
    "raw",
    "undercooked",
    "cooked",
    "pasteurized",
    "unpasteurized",
    "ready_to_eat",
    "reheated",
    "smoked",
    "cured",
    "washed",
    "unwashed",
    "unknown",
]
StateDimension = Literal[
    "raw_undercooked_status",
    "pasteurization_status",
    "process_state",
]
EvidenceOrigin = Literal[
    "EXPLICIT_RECIPE_INGREDIENT",
    "EXPLICIT_RECIPE_STEP",
    "EXPLICIT_RECIPE_METADATA",
    "PRODUCT_LABEL",
    "AUTHORITATIVE_FOOD_IDENTITY",
    "CURATED_PLANAM_FACT",
    "LEGACY_TEXT_SIGNAL",
    "AI_DERIVED",
    "UNKNOWN",
]
VerificationStatus = Literal[
    "accepted_for_dry_run",
    "review_required",
    "not_verified",
    "unknown",
]
LinkageStatus = Literal["DIRECT_LINK", "RECIPE_LEVEL_PROCESS", "AMBIGUOUS_LINK", "NO_LINK"]
FactScope = Literal[
    "RECIPE_STATIC_FACT",
    "PRODUCT_INSTANCE_FACT",
    "COOKING_EVENT_FACT",
    "USER_CONTEXT_FACT",
]

ACCEPTED_PROVENANCE = "curated_reviewed"
PREGNANCY_PROFILE = SimpleNamespace(
    typed_medical_context=[{"condition_id": "pregnancy", "origin": "user_declared"}]
)

PREGNANCY_RELEVANT_FOODS: dict[str, str] = {
    "chicken_egg": "egg",
    "chicken_fillet": "meat_poultry",
    "cod": "fish_seafood",
    "shrimp": "fish_seafood",
    "milk": "milk_dairy",
    "yogurt": "milk_dairy",
    "cottage_cheese": "milk_dairy",
    "sour_cream": "milk_dairy",
    "butter": "milk_dairy",
}
PREGNANCY_RELEVANT_NAME_MARKERS: tuple[tuple[str, str], ...] = (
    ("яйц", "egg"),
    ("желт", "egg"),
    ("куриц", "meat_poultry"),
    ("фарш", "meat_poultry"),
    ("голен", "meat_poultry"),
    ("бедр", "meat_poultry"),
    ("грудк", "meat_poultry"),
    ("рыб", "fish_seafood"),
    ("лосос", "fish_seafood"),
    ("треск", "fish_seafood"),
    ("кревет", "fish_seafood"),
    ("кальмар", "fish_seafood"),
    ("молок", "milk_dairy"),
    ("сыр", "milk_dairy"),
    ("творог", "milk_dairy"),
    ("сметан", "milk_dairy"),
    ("йогурт", "milk_dairy"),
    ("сливк", "milk_dairy"),
    ("бекон", "ready_to_eat_processed"),
    ("ветчин", "ready_to_eat_processed"),
    ("колбас", "ready_to_eat_processed"),
    ("сосиск", "ready_to_eat_processed"),
)
PRODUCT_INSTANCE_FOOD_CLASSES = {"milk_dairy", "ready_to_eat_processed"}
HEAT_TREATMENT_FOOD_CLASSES = {"egg", "meat_poultry", "fish_seafood"}

DIRECT_HEAT_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\bотвар\w*\b"), "cooked"),
    (re.compile(r"\bвар\w*\b"), "cooked"),
    (re.compile(r"\bобжар\w*\b"), "cooked"),
    (re.compile(r"\bжар\w*\b"), "cooked"),
    (re.compile(r"\bзапек\w*\b"), "cooked"),
    (re.compile(r"\bтуш\w*\b"), "cooked"),
    (re.compile(r"\bдовед\w*\s+до\s+кипен"), "cooked"),
    (re.compile(r"\bкипят\w*\b"), "cooked"),
)
DIRECT_RAW_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bсыр(ой|ая|ое|ые|ого|ую|ым|ыми)\b"),
    re.compile(r"без\s+термической\s+обработки"),
)
UNDERCOOKED_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bполусыр\w*\b"),
    re.compile(r"не\s+до\s+конца\s+готов"),
    re.compile(r"недостаточн\w+\s+термическ\w+\s+обработ"),
)
PASTEURIZED_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\bпастеризован\w*\b"), "pasteurized"),
    (re.compile(r"\bнепастеризован\w*\b"), "unpasteurized"),
)
GENERIC_COOKING_TEXT = re.compile(r"приготов\w+\s+по\s+классическ")


@dataclass(frozen=True)
class ProcessStateFact:
    recipe_id: int | None
    ingredient_row_id: int | None
    ingredient_name: str | None
    canonical_food_key: str | None
    food_category: str | None
    state_dimension: StateDimension
    process_state: ProcessState
    evidence_origin: EvidenceOrigin
    source_id: str
    source_role: str
    source_record_locator: str
    confidence: str
    verification_status: VerificationStatus
    provenance_status: str
    fact_scope: FactScope
    linkage_status: LinkageStatus
    step_number: int | None = None
    text_hash: str | None = None
    extraction_rule: str | None = None
    runtime_applicability: str = "pregnancy_p0_e"
    review_reason: str | None = None

    @property
    def accepted(self) -> bool:
        return (
            self.evidence_origin == "EXPLICIT_RECIPE_STEP"
            and self.verification_status == "accepted_for_dry_run"
            and self.provenance_status == ACCEPTED_PROVENANCE
            and self.linkage_status == "DIRECT_LINK"
        )

    def to_record(self) -> dict[str, Any]:
        return {
            "recipe_id": self.recipe_id,
            "ingredient_row_id": self.ingredient_row_id,
            "ingredient_name": self.ingredient_name,
            "canonical_food_key": self.canonical_food_key,
            "food_category": self.food_category,
            "state_dimension": self.state_dimension,
            "process_state": self.process_state,
            "evidence_origin": self.evidence_origin,
            "source_id": self.source_id,
            "source_role": self.source_role,
            "source_record_locator": self.source_record_locator,
            "confidence": self.confidence,
            "verification_status": self.verification_status,
            "provenance_status": self.provenance_status,
            "fact_scope": self.fact_scope,
            "linkage_status": self.linkage_status,
            "step_number": self.step_number,
            "text_hash": self.text_hash,
            "extraction_rule": self.extraction_rule,
            "runtime_applicability": self.runtime_applicability,
            "review_reason": self.review_reason,
            "accepted_for_p0_e_simulation": self.accepted,
        }


def _text_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _source_locator(recipe_id: int | None, step_number: int | None, text: str) -> str:
    return f"recipe_step:{recipe_id}:{step_number}:{_text_hash(text)}"


def pregnancy_food_category(name: str, canonical_food_key: str | None = None) -> str | None:
    if canonical_food_key in PREGNANCY_RELEVANT_FOODS:
        return PREGNANCY_RELEVANT_FOODS[canonical_food_key]
    normalized = normalize_ingredient_name(name)
    for marker, category in PREGNANCY_RELEVANT_NAME_MARKERS:
        if marker in normalized:
            return category
    return None


def ingredient_identity(row: dict[str, Any]) -> dict[str, Any]:
    name = str(row.get("name") or "")
    match = dry_run_food_match(name)
    canonical = match.canonical_food_key if match.status == "matched" else None
    category = pregnancy_food_category(name, canonical)
    return {
        "ingredient_row_id": int(row["id"]) if row.get("id") is not None else None,
        "recipe_id": int(row["recipe_id"]) if row.get("recipe_id") is not None else None,
        "ingredient_name": name,
        "normalized_ingredient": normalize_ingredient_name(name),
        "canonical_food_key": canonical,
        "food_category": category,
        "pregnancy_relevant": category is not None,
    }


def _state_dimension(state: str) -> StateDimension:
    if state in {"pasteurized", "unpasteurized"}:
        return "pasteurization_status"
    if state in {"raw", "undercooked", "cooked"}:
        return "raw_undercooked_status"
    return "process_state"


def _fact_scope(category: str | None, dimension: StateDimension) -> FactScope:
    if dimension == "pasteurization_status" or category in PRODUCT_INSTANCE_FOOD_CLASSES:
        return "PRODUCT_INSTANCE_FACT"
    if dimension == "raw_undercooked_status":
        return "COOKING_EVENT_FACT"
    return "RECIPE_STATIC_FACT"


def _accepted_fact(
    *,
    ingredient: dict[str, Any],
    state: ProcessState,
    step: dict[str, Any],
    rule: str,
) -> ProcessStateFact:
    text = str(step.get("text") or "")
    dimension = _state_dimension(state)
    return ProcessStateFact(
        recipe_id=ingredient["recipe_id"],
        ingredient_row_id=ingredient["ingredient_row_id"],
        ingredient_name=ingredient["ingredient_name"],
        canonical_food_key=ingredient["canonical_food_key"],
        food_category=ingredient["food_category"],
        state_dimension=dimension,
        process_state=state,
        evidence_origin="EXPLICIT_RECIPE_STEP",
        source_id="SRC-PLANAM-SAFETY-POLICY",
        source_role="PRIMARY",
        source_record_locator=_source_locator(ingredient["recipe_id"], step.get("step_number"), text),
        confidence="high",
        verification_status="accepted_for_dry_run",
        provenance_status=ACCEPTED_PROVENANCE,
        fact_scope=_fact_scope(ingredient["food_category"], dimension),
        linkage_status="DIRECT_LINK",
        step_number=int(step["step_number"]) if step.get("step_number") is not None else None,
        text_hash=_text_hash(text),
        extraction_rule=rule,
    )


def _review_fact(
    *,
    recipe_id: int | None,
    state: ProcessState,
    step: dict[str, Any],
    rule: str,
    reason: str,
    linkage_status: LinkageStatus,
    ingredient: dict[str, Any] | None = None,
    origin: EvidenceOrigin = "LEGACY_TEXT_SIGNAL",
) -> ProcessStateFact:
    text = str(step.get("text") or "")
    category = ingredient.get("food_category") if ingredient else None
    dimension = _state_dimension(state)
    return ProcessStateFact(
        recipe_id=recipe_id,
        ingredient_row_id=ingredient.get("ingredient_row_id") if ingredient else None,
        ingredient_name=ingredient.get("ingredient_name") if ingredient else None,
        canonical_food_key=ingredient.get("canonical_food_key") if ingredient else None,
        food_category=category,
        state_dimension=dimension,
        process_state=state,
        evidence_origin=origin,
        source_id="SRC-PLANAM-SAFETY-POLICY",
        source_role="PRIMARY",
        source_record_locator=_source_locator(recipe_id, step.get("step_number"), text),
        confidence="review_required",
        verification_status="review_required",
        provenance_status="needs_review",
        fact_scope=_fact_scope(category, dimension),
        linkage_status=linkage_status,
        step_number=int(step["step_number"]) if step.get("step_number") is not None else None,
        text_hash=_text_hash(text),
        extraction_rule=rule,
        review_reason=reason,
    )


def represent_explicit_process_state(
    *,
    process_state: ProcessState,
    ingredient_name: str = "яйцо",
    recipe_id: int = 1,
    ingredient_row_id: int = 1,
    step_text: str = "Отварите яйцо вкрутую.",
) -> ProcessStateFact:
    row = {"id": ingredient_row_id, "recipe_id": recipe_id, "name": ingredient_name}
    ingredient = ingredient_identity(row)
    return _accepted_fact(
        ingredient=ingredient,
        state=process_state,
        step={"recipe_id": recipe_id, "step_number": 1, "text": step_text},
        rule="explicit_test_fixture",
    )


def extract_process_state_facts(
    ingredient_rows: list[dict[str, Any]],
    steps: list[dict[str, Any]],
) -> dict[str, Any]:
    ingredients = [ingredient_identity(row) for row in ingredient_rows]
    by_recipe: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for ingredient in ingredients:
        if ingredient["recipe_id"] is not None:
            by_recipe[ingredient["recipe_id"]].append(ingredient)

    facts: list[ProcessStateFact] = []
    linkage_records: list[dict[str, Any]] = []
    step_evidence_recipe_ids: set[int] = set()

    for step in steps:
        recipe_id = int(step["recipe_id"]) if step.get("recipe_id") is not None else None
        text = str(step.get("text") or "")
        normalized_text = normalize_ingredient_name(text)
        recipe_ingredients = by_recipe.get(recipe_id or -1, [])
        accepted_for_step = 0
        matched_any_ingredient = False

        for ingredient in recipe_ingredients:
            name = ingredient["normalized_ingredient"]
            if not name or name not in normalized_text:
                continue
            matched_any_ingredient = True
            if any(pattern.search(normalized_text) for pattern in UNDERCOOKED_PATTERNS):
                facts.append(_accepted_fact(ingredient=ingredient, state="undercooked", step=step, rule="direct_under_cooked_phrase"))
                accepted_for_step += 1
                continue
            if any(pattern.search(normalized_text) for pattern in DIRECT_RAW_PATTERNS):
                facts.append(_accepted_fact(ingredient=ingredient, state="raw", step=step, rule="direct_raw_phrase"))
                accepted_for_step += 1
                continue
            for pattern, state in PASTEURIZED_PATTERNS:
                if pattern.search(normalized_text):
                    facts.append(_accepted_fact(ingredient=ingredient, state=state, step=step, rule="direct_pasteurization_phrase"))
                    accepted_for_step += 1
                    break
            else:
                for pattern, state in DIRECT_HEAT_PATTERNS:
                    if pattern.search(normalized_text):
                        facts.append(_accepted_fact(ingredient=ingredient, state=state, step=step, rule=f"direct_heat_link:{pattern.pattern}"))
                        accepted_for_step += 1
                        break

        if accepted_for_step:
            step_evidence_recipe_ids.add(recipe_id or -1)
            linkage = "DIRECT_LINK"
        elif GENERIC_COOKING_TEXT.search(normalized_text):
            facts.append(
                _review_fact(
                    recipe_id=recipe_id,
                    state="unknown",
                    step=step,
                    rule="generic_recipe_level_cooking_phrase",
                    reason="generic cooking phrase does not identify food or process completion",
                    linkage_status="RECIPE_LEVEL_PROCESS",
                )
            )
            linkage = "RECIPE_LEVEL_PROCESS"
            step_evidence_recipe_ids.add(recipe_id or -1)
        elif any(pattern.search(normalized_text) for pattern, _state in DIRECT_HEAT_PATTERNS):
            facts.append(
                _review_fact(
                    recipe_id=recipe_id,
                    state="unknown",
                    step=step,
                    rule="heat_verb_without_direct_ingredient_link",
                    reason="heat verb exists but no pregnancy-relevant ingredient was directly linked",
                    linkage_status="AMBIGUOUS_LINK" if recipe_ingredients else "NO_LINK",
                )
            )
            linkage = "AMBIGUOUS_LINK" if recipe_ingredients else "NO_LINK"
            step_evidence_recipe_ids.add(recipe_id or -1)
        else:
            linkage = "NO_LINK"

        if linkage != "NO_LINK" or matched_any_ingredient:
            linkage_records.append(
                {
                    "recipe_id": recipe_id,
                    "step_number": step.get("step_number"),
                    "text_hash": _text_hash(text),
                    "linkage_status": linkage,
                    "accepted_fact_count": accepted_for_step,
                    "matched_ingredient_text": matched_any_ingredient,
                }
            )

    return {
        "ingredients": ingredients,
        "facts": [fact.to_record() for fact in facts],
        "fact_objects": facts,
        "linkage_records": linkage_records,
        "recipes_with_any_explicit_process_state_evidence": len(step_evidence_recipe_ids),
    }


def _unknown_reason(ingredient: dict[str, Any], has_accepted_fact: bool) -> str:
    if not ingredient["pregnancy_relevant"]:
        return "OTHER"
    if not ingredient["canonical_food_key"] and ingredient["food_category"] is None:
        return "FOOD_IDENTITY_UNKNOWN"
    category = ingredient["food_category"]
    if category in PRODUCT_INSTANCE_FOOD_CLASSES:
        return "PRODUCT_LABEL_REQUIRED" if category == "ready_to_eat_processed" else "PASTEURIZATION_UNKNOWN"
    if category in HEAT_TREATMENT_FOOD_CLASSES and not has_accepted_fact:
        return "COOKING_COMPLETENESS_UNKNOWN"
    if not has_accepted_fact:
        return "PROCESS_STATE_UNKNOWN"
    return "OTHER"


def _decision_for_recipe(facts: list[ProcessStateFact]) -> dict[str, Any]:
    accepted = [fact for fact in facts if fact.accepted and fact.food_category is not None]
    if not accepted:
        return {
            "decision_class": "NO_RELEVANT_FACT",
            "reason": "No accepted pregnancy-relevant process-state fact was available for P0-E simulation.",
            "accepted_fact_count": 0,
        }

    recipe = SimpleNamespace(
        pasteurization_status="unknown",
        raw_undercooked_status="unknown",
        process_state="known",
        medical_safety_facts_json={"process_state_provenance_status": ACCEPTED_PROVENANCE},
    )
    if any(f.process_state == "unpasteurized" for f in accepted):
        recipe.pasteurization_status = "unpasteurized"
    elif any(f.process_state == "pasteurized" for f in accepted):
        recipe.pasteurization_status = "pasteurized"
    if any(f.process_state == "raw" for f in accepted):
        recipe.raw_undercooked_status = "raw"
    elif any(f.process_state == "undercooked" for f in accepted):
        recipe.raw_undercooked_status = "undercooked"
    elif any(f.process_state == "cooked" for f in accepted):
        recipe.raw_undercooked_status = "cooked"

    decision = evaluate_medical_safety(recipe, PREGNANCY_PROFILE)[0]
    return {
        "decision_class": decision.decision_class,
        "reason": decision.reason,
        "accepted_fact_count": len(accepted),
        "source_id": decision.source_id,
        "provenance_status": decision.provenance_status,
    }


def simulate_pregnancy_process_state(
    recipes: list[dict[str, Any]],
    ingredient_rows: list[dict[str, Any]],
    steps: list[dict[str, Any]],
) -> dict[str, Any]:
    extraction = extract_process_state_facts(ingredient_rows, steps)
    ingredients = extraction["ingredients"]
    facts = extraction["fact_objects"]
    facts_by_ingredient: dict[int, list[ProcessStateFact]] = defaultdict(list)
    facts_by_recipe: dict[int, list[ProcessStateFact]] = defaultdict(list)
    for fact in facts:
        if fact.ingredient_row_id is not None:
            facts_by_ingredient[fact.ingredient_row_id].append(fact)
        if fact.recipe_id is not None:
            facts_by_recipe[fact.recipe_id].append(fact)

    relevant_rows = []
    unknown_register = []
    for ingredient in ingredients:
        if not ingredient["pregnancy_relevant"]:
            continue
        row_facts = facts_by_ingredient.get(ingredient["ingredient_row_id"], [])
        accepted = [fact for fact in row_facts if fact.accepted]
        resolved = bool(accepted)
        unknown_reason = None if resolved else _unknown_reason(ingredient, False)
        record = {
            **ingredient,
            "sufficient_process_state": resolved,
            "accepted_fact_count": len(accepted),
            "unknown_reason": unknown_reason,
            "requires_product_instance_fact": ingredient["food_category"] in PRODUCT_INSTANCE_FOOD_CLASSES and not resolved,
            "requires_cooking_event_fact": ingredient["food_category"] in HEAT_TREATMENT_FOOD_CLASSES and not resolved,
        }
        relevant_rows.append(record)
        if unknown_reason:
            unknown_register.append(record)

    decision_records = []
    for recipe in sorted(recipes, key=lambda row: int(row["id"])):
        recipe_id = int(recipe["id"])
        decision = _decision_for_recipe(facts_by_recipe.get(recipe_id, []))
        decision_records.append({"recipe_id": recipe_id, "title": recipe.get("title"), **decision})

    accepted_facts = [fact for fact in facts if fact.accepted]
    review_facts = [fact for fact in facts if not fact.accepted]
    decision_counts = Counter(row["decision_class"] for row in decision_records)
    pregnancy_relevant_accepted_facts = [
        fact for fact in accepted_facts if fact.food_category is not None
    ]
    pasteurization_known = sum(
        1 for fact in pregnancy_relevant_accepted_facts if fact.state_dimension == "pasteurization_status"
    )
    heat_known = sum(
        1 for fact in pregnancy_relevant_accepted_facts if fact.state_dimension == "raw_undercooked_status"
    )
    metrics = {
        "recipes_total": len(recipes),
        "recipes_with_explicit_process_state_evidence": extraction["recipes_with_any_explicit_process_state_evidence"],
        "ingredient_rows_with_linked_process_state_evidence": len({fact.ingredient_row_id for fact in accepted_facts if fact.ingredient_row_id is not None}),
        "verified_process_state_facts": len(accepted_facts),
        "review_required_process_state_facts": len(review_facts),
        "unknown_facts": len(unknown_register),
        "pregnancy_relevant_rows": len(relevant_rows),
        "pregnancy_relevant_rows_sufficiently_resolved": sum(1 for row in relevant_rows if row["sufficient_process_state"]),
        "pregnancy_relevant_rows_unresolved": sum(1 for row in relevant_rows if not row["sufficient_process_state"]),
        "pasteurization_known": pasteurization_known,
        "pasteurization_unknown": sum(1 for row in relevant_rows if row["food_category"] in PRODUCT_INSTANCE_FOOD_CLASSES and not row["sufficient_process_state"]),
        "heat_treatment_known": heat_known,
        "heat_treatment_unknown": sum(1 for row in relevant_rows if row["food_category"] in HEAT_TREATMENT_FOOD_CLASSES and not row["sufficient_process_state"]),
        "decision_counts": {
            "BLOCK": decision_counts.get("BLOCK", 0),
            "WARN": decision_counts.get("WARN", 0),
            "ESCALATE": decision_counts.get("ESCALATE", 0),
            "UNKNOWN": decision_counts.get("UNKNOWN", 0),
            "NO_RELEVANT_FACT": decision_counts.get("NO_RELEVANT_FACT", 0),
        },
        "static_recipe_facts": sum(1 for fact in accepted_facts if fact.fact_scope == "RECIPE_STATIC_FACT"),
        "product_instance_facts_required": sum(1 for row in relevant_rows if row["requires_product_instance_fact"]),
        "cooking_event_facts_required": sum(1 for row in relevant_rows if row["requires_cooking_event_fact"]),
    }
    return {
        "metrics": metrics,
        "process_state_facts": [fact.to_record() for fact in facts],
        "ingredient_step_linkage": extraction["linkage_records"],
        "pregnancy_relevant_rows": relevant_rows,
        "decision_simulation": decision_records,
        "unknown_reason_register": unknown_register,
    }


def legacy_or_ai_fact_for_review(
    *,
    origin: EvidenceOrigin,
    process_state: ProcessState = "cooked",
) -> ProcessStateFact:
    return ProcessStateFact(
        recipe_id=1,
        ingredient_row_id=1,
        ingredient_name="яйцо",
        canonical_food_key="chicken_egg",
        food_category="egg",
        state_dimension=_state_dimension(process_state),
        process_state=process_state,
        evidence_origin=origin,
        source_id="SRC-PLANAM-SAFETY-POLICY",
        source_role="PRIMARY",
        source_record_locator=f"test:{origin}",
        confidence="review_required",
        verification_status="review_required",
        provenance_status="needs_review",
        fact_scope="COOKING_EVENT_FACT",
        linkage_status="DIRECT_LINK",
        extraction_rule="test_non_verified_origin",
        review_reason="origin is not accepted for verified dry-run fact",
    )


__all__ = [
    "ProcessStateFact",
    "extract_process_state_facts",
    "ingredient_identity",
    "legacy_or_ai_fact_for_review",
    "pregnancy_food_category",
    "represent_explicit_process_state",
    "simulate_pregnancy_process_state",
]
