"""Per-person family food safety, nutrition, and quantity aggregation.

P0-F keeps person identity through safety/nutrition decisions and only derives
family-level views after each participating person has been evaluated.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from types import SimpleNamespace
from typing import Any, Literal

from sqlalchemy.orm import Session

from app.models.family import FamilyMember
from app.models.meal_eating_schedule import MealEatingSchedule
from app.models.recipe import Recipe
from app.models.user import User
from app.nutrition.restriction_safety import (
    RestrictionConflict,
    explain_recipe_restriction_conflicts,
)
from app.services import family as family_service
from app.services.app_scope import AppScope
from app.services.family_member_nutrition import (
    member_is_virtual,
    virtual_nutrition_from_member,
)
from app.services.meal_attendance import WEEKDAY_KEYS
from app.services.nutrition.target_resolver import (
    TargetResolverResult,
    facts_from_family_member,
    facts_from_user_profile,
    resolve_evidence_targets,
)
from app.services.onboarding import get_or_create_profile
from app.services.recipe_storage import aggregate_ingredients_for_shopping, scale_ingredients

ParticipationState = Literal["participates", "does_not_participate", "unknown"]
PortionState = Literal["explicit", "derived_default", "unknown"]
SafetyDecision = Literal["SAFE", "WARN", "UNKNOWN", "ESCALATE", "BLOCK"]
NutritionComplianceState = Literal[
    "within_applicable_target",
    "outside_applicable_target",
    "target_unavailable",
    "nutrient_facts_unavailable",
    "portion_unknown",
    "unknown",
    "escalate",
]

SAFETY_PRECEDENCE: dict[SafetyDecision, int] = {
    "SAFE": 0,
    "WARN": 1,
    "UNKNOWN": 2,
    "ESCALATE": 3,
    "BLOCK": 4,
}


@dataclass(frozen=True)
class PersonProfileRef:
    person_id: str
    family_member_id: int | None
    user_id: int | None
    display_name: str
    profile_source: str
    profile: Any


@dataclass(frozen=True)
class PersonParticipation:
    person_id: str
    participation_state: ParticipationState
    source: str
    origin: str
    family_member_id: int | None = None


@dataclass(frozen=True)
class PersonPortion:
    person_id: str
    serving_factor: float | None
    state: PortionState
    source: str
    origin: str
    family_member_id: int | None = None


@dataclass(frozen=True)
class PersonSafetyResult:
    person_id: str
    recipe_id: int | None
    decision: SafetyDecision
    reasons: list[str]
    conflicts: list[RestrictionConflict] = field(default_factory=list)


@dataclass(frozen=True)
class PersonNutritionResult:
    person_id: str
    recipe_id: int | None
    target_result: TargetResolverResult
    nutrient_fact_provenance: dict[str, Any]
    portion: PersonPortion
    calculated_values: dict[str, float | None]
    compliance_state: NutritionComplianceState
    reasons: list[str]


@dataclass(frozen=True)
class FamilySafetyAggregation:
    participant_results: list[PersonSafetyResult]
    aggregate_decision: SafetyDecision
    blocking_people: list[PersonSafetyResult]
    escalating_people: list[PersonSafetyResult]
    unknown_people: list[PersonSafetyResult]
    precedence: tuple[SafetyDecision, ...] = (
        "BLOCK",
        "ESCALATE",
        "UNKNOWN",
        "WARN",
        "SAFE",
    )


@dataclass(frozen=True)
class FamilyNutritionAggregation:
    participant_results: list[PersonNutritionResult]
    summary_counts: dict[str, int]


@dataclass(frozen=True)
class FamilyQuantityAggregation:
    participant_portions: list[PersonPortion]
    total_serving_factor: float | None
    state: Literal["complete", "incomplete"]
    reasons: list[str]


@dataclass(frozen=True)
class FamilyRecipeAggregation:
    participants: list[PersonProfileRef]
    participations: list[PersonParticipation]
    safety: FamilySafetyAggregation
    nutrition: FamilyNutritionAggregation | None
    quantity: FamilyQuantityAggregation


def person_id_for_member(member: FamilyMember) -> str:
    return f"family_member:{member.id}"


def profile_ref_for_member(db: Session, member: FamilyMember) -> PersonProfileRef:
    if member_is_virtual(member):
        return PersonProfileRef(
            person_id=person_id_for_member(member),
            family_member_id=member.id,
            user_id=member.user_id,
            display_name=member.display_name,
            profile_source="family_member.nutrition_profile",
            profile=virtual_nutrition_from_member(member),
        )
    if member.user_id is None:
        return PersonProfileRef(
            person_id=person_id_for_member(member),
            family_member_id=member.id,
            user_id=None,
            display_name=member.display_name,
            profile_source="missing_linked_user",
            profile=None,
        )
    user = db.query(User).filter(User.id == member.user_id).one_or_none()
    profile = get_or_create_profile(db, user) if user else None
    return PersonProfileRef(
        person_id=person_id_for_member(member),
        family_member_id=member.id,
        user_id=member.user_id,
        display_name=member.display_name,
        profile_source="user_profile",
        profile=profile,
    )


def profile_ref_for_user(db: Session, user: User) -> PersonProfileRef:
    return PersonProfileRef(
        person_id=f"user:{user.id}",
        family_member_id=None,
        user_id=user.id,
        display_name=user.first_name or user.username or f"User {user.id}",
        profile_source="user_profile",
        profile=get_or_create_profile(db, user),
    )


def profile_refs_for_scope(db: Session, user: User, scope: AppScope) -> list[PersonProfileRef]:
    if scope.is_personal:
        return [profile_ref_for_user(db, user)]
    family = family_service.get_family_for_user(db, user)
    if family is None or not family.members:
        return [profile_ref_for_user(db, user)]
    return [
        profile_ref_for_member(db, member)
        for member in sorted(family.members, key=lambda item: item.id)
    ]


def _weekday_key(on_date: date) -> str:
    return WEEKDAY_KEYS[on_date.weekday()]


def participation_for_member(
    db: Session,
    member: FamilyMember,
    *,
    meal_type: str,
    on_date: date | None = None,
) -> PersonParticipation:
    on_date = on_date or date.today()
    row = (
        db.query(MealEatingSchedule)
        .filter(MealEatingSchedule.family_member_id == member.id)
        .one_or_none()
    )
    if row is None:
        return PersonParticipation(
            person_id=person_id_for_member(member),
            family_member_id=member.id,
            participation_state="participates",
            source="legacy_default_home",
            origin="fallback",
        )
    data = row.schedule_json or {}
    meal_cfg = data.get(meal_type)
    if isinstance(meal_cfg, dict):
        raw = meal_cfg.get(_weekday_key(on_date), meal_cfg.get("default"))
    else:
        raw = data.get("default_home", None)
    if raw in {"home", True}:
        state: ParticipationState = "participates"
    elif raw in {"away", "out", False}:
        state = "does_not_participate"
    else:
        state = "unknown"
    return PersonParticipation(
        person_id=person_id_for_member(member),
        family_member_id=member.id,
        participation_state=state,
        source="meal_eating_schedule",
        origin="explicit" if state != "unknown" else "ambiguous",
    )


def participation_for_scope(
    db: Session,
    user: User,
    scope: AppScope,
    *,
    meal_type: str,
    on_date: date | None = None,
) -> list[PersonParticipation]:
    if scope.is_personal:
        return [
            PersonParticipation(
                person_id=f"user:{user.id}",
                family_member_id=None,
                participation_state="participates",
                source="personal_scope",
                origin="explicit_scope",
            )
        ]
    family = family_service.get_family_for_user(db, user)
    if family is None or not family.members:
        return [
            PersonParticipation(
                person_id=f"user:{user.id}",
                family_member_id=None,
                participation_state="participates",
                source="missing_family_fallback",
                origin="fallback",
            )
        ]
    return [
        participation_for_member(db, member, meal_type=meal_type, on_date=on_date)
        for member in sorted(family.members, key=lambda item: item.id)
    ]


def _age_months_for_profile_ref(ref: PersonProfileRef) -> int | None:
    return getattr(ref.profile, "age_months", None) if ref.profile is not None else None


def portion_for_person(
    ref: PersonProfileRef,
    participation: PersonParticipation,
    *,
    explicit_serving_factor: float | None = None,
    explicit_person_portions: dict[str, float | None] | None = None,
) -> PersonPortion:
    if participation.participation_state != "participates":
        return PersonPortion(
            person_id=ref.person_id,
            family_member_id=ref.family_member_id,
            serving_factor=None,
            state="unknown",
            source="not_applicable_until_participation",
            origin=participation.participation_state,
        )
    if explicit_person_portions and ref.person_id in explicit_person_portions:
        value = explicit_person_portions[ref.person_id]
        return PersonPortion(
            person_id=ref.person_id,
            family_member_id=ref.family_member_id,
            serving_factor=value,
            state="explicit" if value is not None else "unknown",
            source="person_portion",
            origin="explicit",
        )
    if explicit_serving_factor is not None:
        return PersonPortion(
            person_id=ref.person_id,
            family_member_id=ref.family_member_id,
            serving_factor=float(explicit_serving_factor),
            state="explicit",
            source="meal_serving_factor",
            origin="explicit",
        )
    age_months = _age_months_for_profile_ref(ref)
    if age_months is not None and age_months < 216:
        return PersonPortion(
            person_id=ref.person_id,
            family_member_id=ref.family_member_id,
            serving_factor=0.75,
            state="derived_default",
            source="age_based_child_portion_fallback",
            origin="fallback",
        )
    return PersonPortion(
        person_id=ref.person_id,
        family_member_id=ref.family_member_id,
        serving_factor=1.0,
        state="derived_default",
        source="adult_portion_fallback",
        origin="fallback",
    )


def aggregate_quantity(portions: list[PersonPortion]) -> FamilyQuantityAggregation:
    reasons: list[str] = []
    total = 0.0
    for portion in portions:
        if portion.serving_factor is None:
            reasons.append(f"{portion.person_id}:portion_unknown")
            continue
        total += portion.serving_factor
    if reasons:
        return FamilyQuantityAggregation(
            participant_portions=portions,
            total_serving_factor=None,
            state="incomplete",
            reasons=reasons,
        )
    return FamilyQuantityAggregation(
        participant_portions=portions,
        total_serving_factor=total,
        state="complete",
        reasons=[],
    )


def _decision_from_conflicts(conflicts: list[RestrictionConflict]) -> SafetyDecision:
    if not conflicts:
        return "SAFE"
    decision: SafetyDecision = "WARN"
    for conflict in conflicts:
        key = conflict.restriction_key.lower()
        if ":escalate" in key:
            candidate: SafetyDecision = "ESCALATE"
        elif ":unknown" in key or "celiac_disease:unknown" in key:
            candidate = "UNKNOWN"
        elif conflict.severity == "hard":
            candidate = "BLOCK"
        else:
            candidate = "WARN"
        if SAFETY_PRECEDENCE[candidate] > SAFETY_PRECEDENCE[decision]:
            decision = candidate
    return decision


def evaluate_person_safety(recipe: Any, ref: PersonProfileRef) -> PersonSafetyResult:
    if ref.profile is None:
        return PersonSafetyResult(
            person_id=ref.person_id,
            recipe_id=getattr(recipe, "id", None),
            decision="UNKNOWN",
            reasons=["profile_unavailable"],
            conflicts=[],
        )
    conflicts = explain_recipe_restriction_conflicts(recipe, ref.profile)
    decision = _decision_from_conflicts(conflicts)
    return PersonSafetyResult(
        person_id=ref.person_id,
        recipe_id=getattr(recipe, "id", None),
        decision=decision,
        reasons=[conflict.reason for conflict in conflicts],
        conflicts=conflicts,
    )


def aggregate_safety(results: list[PersonSafetyResult]) -> FamilySafetyAggregation:
    aggregate: SafetyDecision = "SAFE"
    for result in results:
        if SAFETY_PRECEDENCE[result.decision] > SAFETY_PRECEDENCE[aggregate]:
            aggregate = result.decision
    return FamilySafetyAggregation(
        participant_results=results,
        aggregate_decision=aggregate,
        blocking_people=[r for r in results if r.decision == "BLOCK"],
        escalating_people=[r for r in results if r.decision == "ESCALATE"],
        unknown_people=[r for r in results if r.decision == "UNKNOWN"],
    )


def _target_result_for_ref(ref: PersonProfileRef) -> TargetResolverResult:
    if ref.profile is None:
        return TargetResolverResult(status="insufficient_data", reason="missing_profile")
    if ref.profile_source == "family_member.nutrition_profile":
        facts = facts_from_family_member(
            SimpleNamespace(
                nutrition_profile=ref.profile.model_dump(mode="json"),
                is_virtual=True,
                user_id=None,
            )
        )
    else:
        facts = facts_from_user_profile(ref.profile)
    return resolve_evidence_targets(facts)


def _recipe_nutrients(recipe: Any) -> tuple[dict[str, float | None], dict[str, Any]]:
    values = {
        "kcal": getattr(recipe, "nutrition_kcal_per_serving", None),
        "protein": getattr(recipe, "nutrition_protein_per_serving", None),
        "fat": getattr(recipe, "nutrition_fat_per_serving", None),
        "carbs": getattr(recipe, "nutrition_carbs_per_serving", None),
    }
    if all(value is None for value in values.values()):
        values = {
            "kcal": getattr(recipe, "calories_per_serving", None),
            "protein": getattr(recipe, "protein_g", None),
            "fat": getattr(recipe, "fat_g", None),
            "carbs": getattr(recipe, "carbs_g", None),
        }
        source_kind = "legacy_recipe_macro_fields"
    else:
        source_kind = getattr(recipe, "nutrition_source_kind", None) or getattr(
            recipe, "nutrition_confidence", None
        )
    provenance = getattr(recipe, "nutrition_provenance_json", None)
    if not isinstance(provenance, dict):
        provenance = {}
    provenance = {
        **provenance,
        "nutrition_source_kind": provenance.get("nutrition_source_kind") or source_kind,
        "confidence": getattr(recipe, "nutrition_confidence", None),
    }
    return values, provenance


def evaluate_person_nutrition(
    recipe: Any,
    ref: PersonProfileRef,
    portion: PersonPortion,
) -> PersonNutritionResult:
    target = _target_result_for_ref(ref)
    nutrients, provenance = _recipe_nutrients(recipe)
    reasons: list[str] = []
    calculated: dict[str, float | None] = {key: None for key in nutrients}
    if portion.serving_factor is None:
        reasons.append("portion_unknown")
        state: NutritionComplianceState = "portion_unknown"
    elif any(value is None for value in nutrients.values()):
        reasons.append("nutrient_facts_unavailable")
        state = "nutrient_facts_unavailable"
    elif not target.resolved or target.resolution is None:
        reasons.append(target.reason or target.status)
        state = "target_unavailable" if target.status in {"insufficient_data", "unsupported_scope"} else "escalate"
        calculated = {key: float(value) * portion.serving_factor for key, value in nutrients.items()}
    else:
        calculated = {key: float(value) * portion.serving_factor for key, value in nutrients.items()}
        targets = target.resolution.targets
        target_values = {
            "kcal": targets.calories_target,
            "protein": targets.protein_target_g,
            "fat": targets.fat_target_g,
            "carbs": targets.carbs_target_g,
        }
        if any(value is None for value in target_values.values()):
            state = "unknown"
            reasons.append("target_partially_unavailable")
        elif any(calculated[key] is not None and calculated[key] > float(target_values[key]) for key in target_values):
            state = "outside_applicable_target"
        else:
            state = "within_applicable_target"
    return PersonNutritionResult(
        person_id=ref.person_id,
        recipe_id=getattr(recipe, "id", None),
        target_result=target,
        nutrient_fact_provenance=provenance,
        portion=portion,
        calculated_values=calculated,
        compliance_state=state,
        reasons=reasons,
    )


def aggregate_nutrition(results: list[PersonNutritionResult]) -> FamilyNutritionAggregation:
    counts = {
        "participants_evaluated": len(results),
        "within": 0,
        "outside": 0,
        "unknown": 0,
        "escalation_required": 0,
    }
    for result in results:
        if result.compliance_state == "within_applicable_target":
            counts["within"] += 1
        elif result.compliance_state == "outside_applicable_target":
            counts["outside"] += 1
        elif result.compliance_state == "escalate":
            counts["escalation_required"] += 1
        else:
            counts["unknown"] += 1
    return FamilyNutritionAggregation(participant_results=results, summary_counts=counts)


def build_recipe_family_aggregation(
    db: Session,
    user: User,
    scope: AppScope,
    recipe: Recipe,
    *,
    meal_type: str,
    on_date: date | None = None,
    explicit_person_portions: dict[str, float | None] | None = None,
) -> FamilyRecipeAggregation:
    refs = profile_refs_for_scope(db, user, scope)
    participation_by_id = {
        p.person_id: p
        for p in participation_for_scope(db, user, scope, meal_type=meal_type, on_date=on_date)
    }
    participations = [participation_by_id.get(ref.person_id) for ref in refs]
    resolved_participations = [
        p
        if p is not None
        else PersonParticipation(ref.person_id, "unknown", "missing_participation", "unknown", ref.family_member_id)
        for ref, p in zip(refs, participations)
    ]
    participating_refs = [
        ref
        for ref, participation in zip(refs, resolved_participations)
        if participation.participation_state == "participates"
    ]
    portions = [
        portion_for_person(
            ref,
            participation_by_id.get(ref.person_id)
            or PersonParticipation(ref.person_id, "unknown", "missing_participation", "unknown", ref.family_member_id),
            explicit_person_portions=explicit_person_portions,
        )
        for ref in refs
        if (participation_by_id.get(ref.person_id) is not None and participation_by_id[ref.person_id].participation_state == "participates")
    ]
    safety_results = [evaluate_person_safety(recipe, ref) for ref in participating_refs]
    safety_results.extend(
        PersonSafetyResult(
            person_id=ref.person_id,
            recipe_id=getattr(recipe, "id", None),
            decision="UNKNOWN",
            reasons=["participation_unknown"],
            conflicts=[],
        )
        for ref, participation in zip(refs, resolved_participations)
        if participation.participation_state == "unknown"
    )
    nutrition_results = [
        evaluate_person_nutrition(recipe, ref, portion)
        for ref, portion in zip(participating_refs, portions)
    ]
    return FamilyRecipeAggregation(
        participants=refs,
        participations=resolved_participations,
        safety=aggregate_safety(safety_results),
        nutrition=aggregate_nutrition(nutrition_results),
        quantity=(
            FamilyQuantityAggregation(
                participant_portions=aggregate_quantity(portions).participant_portions,
                total_serving_factor=None,
                state="incomplete",
                reasons=[
                    *aggregate_quantity(portions).reasons,
                    *[
                        f"{participation.person_id}:participation_unknown"
                        for participation in resolved_participations
                        if participation.participation_state == "unknown"
                    ],
                ],
            )
            if any(p.participation_state == "unknown" for p in resolved_participations)
            else aggregate_quantity(portions)
        ),
    )


def required_servings_for_meal(
    db: Session,
    user: User,
    scope: AppScope,
    *,
    meal_type: str,
    on_date: date | None = None,
) -> FamilyQuantityAggregation:
    if scope.is_personal:
        return FamilyQuantityAggregation(
            participant_portions=[
                PersonPortion(
                    person_id=f"user:{user.id}",
                    family_member_id=None,
                    serving_factor=1.0,
                    state="explicit",
                    source="personal_scope",
                    origin="explicit_scope",
                )
            ],
            total_serving_factor=1.0,
            state="complete",
            reasons=[],
        )
    refs = profile_refs_for_scope(db, user, scope)
    participation_by_id = {
        p.person_id: p
        for p in participation_for_scope(db, user, scope, meal_type=meal_type, on_date=on_date)
    }
    portions = [
        portion_for_person(ref, participation)
        for ref in refs
        if (participation := participation_by_id.get(ref.person_id))
        and participation.participation_state == "participates"
    ]
    unknowns = [
        participation
        for participation in participation_by_id.values()
        if participation.participation_state == "unknown"
    ]
    aggregation = aggregate_quantity(portions)
    if unknowns:
        return FamilyQuantityAggregation(
            participant_portions=aggregation.participant_portions,
            total_serving_factor=None,
            state="incomplete",
            reasons=[*aggregation.reasons, *[f"{p.person_id}:participation_unknown" for p in unknowns]],
        )
    return aggregation


def scale_recipe_for_family_meal(
    db: Session,
    user: User,
    scope: AppScope,
    recipe: Recipe,
    *,
    meal_type: str,
    fallback_servings: int = 1,
) -> tuple[list[dict[str, Any]], FamilyQuantityAggregation]:
    quantity = required_servings_for_meal(db, user, scope, meal_type=meal_type)
    if quantity.state == "complete" and quantity.total_serving_factor is not None:
        target = max(1, round(quantity.total_serving_factor))
    else:
        target = max(1, fallback_servings)
    return scale_ingredients(recipe, target), quantity


def aggregate_scaled_ingredients(items: list[dict[str, Any]]) -> list[dict[str, str]]:
    return aggregate_ingredients_for_shopping(items)
