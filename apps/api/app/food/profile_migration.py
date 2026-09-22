from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.core.models import LegacyIdMapping
from app.food.profile_models import FoodProfile, FoodProfileFact, FoodProfileReconfirmation
from app.models.family import FamilyMember
from app.models.user_profile import UserProfile
from app.v2.reference_contracts import KnowledgeState
from app.v2.uuid7 import uuid7_str

FOOD_PROFILE_MIGRATION_LOCK_ID = 906_220_003

SOURCE_LEGACY_MIGRATED = "LEGACY_MIGRATED"
REPORTER_USER_DECLARED = "USER_DECLARED"
REPORTER_CAREGIVER_DECLARED = "CAREGIVER_DECLARED"

NO_VALUE_TOKENS = {"none", "no", "нет", "absent", "nothing", "known_none", "known-none"}
INTOLERANCE_TOKENS = {"lactose", "lactose_intolerance", "lactose intolerance", "лактаза", "лактоза"}
CELIAC_TOKENS = {"celiac", "coeliac", "celiac_disease", "gluten_celiac", "целиакия"}


@dataclass
class FoodProfileMigrationReport:
    user_profiles_scanned: int = 0
    family_members_scanned: int = 0
    food_profiles_created: int = 0
    food_profiles_reused: int = 0
    facts_created: int = 0
    facts_reused: int = 0
    reconfirmations_created: int = 0
    reconfirmations_reused: int = 0
    explicit_known_none_facts: int = 0
    ambiguous_empty_legacy_values: int = 0
    free_text_reconfirmation_cases: int = 0
    skipped_missing_core_mapping: int = 0
    errors: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "user_profiles_scanned": self.user_profiles_scanned,
            "family_members_scanned": self.family_members_scanned,
            "food_profiles_created": self.food_profiles_created,
            "food_profiles_reused": self.food_profiles_reused,
            "facts_created": self.facts_created,
            "facts_reused": self.facts_reused,
            "reconfirmations_created": self.reconfirmations_created,
            "reconfirmations_reused": self.reconfirmations_reused,
            "explicit_known_none_facts": self.explicit_known_none_facts,
            "ambiguous_empty_legacy_values": self.ambiguous_empty_legacy_values,
            "free_text_reconfirmation_cases": self.free_text_reconfirmation_cases,
            "skipped_missing_core_mapping": self.skipped_missing_core_mapping,
            "errors": list(self.errors),
        }


def migrate_legacy_food_profiles(db: Session, *, dry_run: bool = False) -> FoodProfileMigrationReport:
    report = FoodProfileMigrationReport()
    bind = db.get_bind()
    if bind.dialect.name == "postgresql" and not dry_run:
        db.execute(text("SELECT pg_advisory_xact_lock(:lock_id)"), {"lock_id": FOOD_PROFILE_MIGRATION_LOCK_ID})

    for profile in db.scalars(select(UserProfile).order_by(UserProfile.id)).all():
        report.user_profiles_scanned += 1
        person_id = _mapped_person_id(db, "users", profile.user_id)
        if person_id is None:
            report.skipped_missing_core_mapping += 1
            continue
        food_profile = _food_profile_for_person(
            db,
            person_id,
            report,
            SOURCE_LEGACY_MIGRATED,
            "user_profiles",
            profile.id,
            dry_run=dry_run,
        )
        if food_profile is None:
            continue
        _migrate_user_profile(db, food_profile, profile, report, dry_run=dry_run)

    for member in db.scalars(select(FamilyMember).order_by(FamilyMember.id)).all():
        report.family_members_scanned += 1
        person_id = _mapped_person_id(db, "family_members", member.id)
        if person_id is None:
            report.skipped_missing_core_mapping += 1
            continue
        food_profile = _food_profile_for_person(
            db,
            person_id,
            report,
            SOURCE_LEGACY_MIGRATED,
            "family_members",
            member.id,
            dry_run=dry_run,
        )
        if food_profile is None:
            continue
        _migrate_family_member_profile(db, food_profile, member, report, dry_run=dry_run)

    if not dry_run:
        db.commit()
    return report


def _mapped_person_id(db: Session, legacy_table: str, legacy_id: int | None) -> str | None:
    if legacy_id is None:
        return None
    mapping = db.scalar(
        select(LegacyIdMapping).where(
            LegacyIdMapping.legacy_table == legacy_table,
            LegacyIdMapping.legacy_id_text == str(legacy_id),
            LegacyIdMapping.target_table == "core_persons",
        )
    )
    return mapping.target_id_uuid if mapping is not None else None


def _food_profile_for_person(
    db: Session,
    person_id: str,
    report: FoodProfileMigrationReport,
    source_kind: str,
    source_legacy_table: str,
    source_legacy_id: int,
    *,
    dry_run: bool,
) -> FoodProfile | None:
    existing = db.scalar(select(FoodProfile).where(FoodProfile.person_id == person_id))
    if existing is not None:
        report.food_profiles_reused += 1
        return existing
    report.food_profiles_created += 1
    if dry_run:
        return None
    profile = FoodProfile(
        food_profile_id=uuid7_str(),
        person_id=person_id,
        profile_status="ACTIVE",
        provenance_json={
            "source_kind": source_kind,
            "source_legacy_table": source_legacy_table,
            "source_legacy_id": source_legacy_id,
        },
    )
    db.add(profile)
    db.flush()
    return profile


def _migrate_user_profile(
    db: Session,
    food_profile: FoodProfile,
    profile: UserProfile,
    report: FoodProfileMigrationReport,
    *,
    dry_run: bool,
) -> None:
    source = _source("user_profiles", profile.id, REPORTER_USER_DECLARED)
    _migrate_list_field(db, food_profile, "allergy", profile.allergies, source, report, dry_run=dry_run)
    _migrate_list_field(db, food_profile, "diet_pattern", profile.diets, source, report, dry_run=dry_run)
    _migrate_restrictions(db, food_profile, profile.restrictions, source, report, dry_run=dry_run)
    _migrate_typed_entries(db, food_profile, profile.typed_safety_profile, source, report, dry_run=dry_run)
    _migrate_typed_entries(db, food_profile, profile.typed_medical_context, source, report, dry_run=dry_run)
    _migrate_scalar(db, food_profile, "nutrition_goal", profile.nutrition_goal, source, report, dry_run=dry_run)
    _migrate_scalar(db, food_profile, "activity_level", profile.activity_level, source, report, dry_run=dry_run)
    _migrate_scalar(
        db,
        food_profile,
        "physical_activity_group",
        profile.physical_activity_group,
        source,
        report,
        dry_run=dry_run,
    )
    _migrate_scalar(db, food_profile, "life_stage", profile.life_stage, source, report, dry_run=dry_run)
    _migrate_scalar(db, food_profile, "gender", profile.gender, source, report, dry_run=dry_run)
    _migrate_measurement(db, food_profile, "height_cm", profile.height_cm, source, report, dry_run=dry_run)
    _migrate_measurement(db, food_profile, "weight_kg", profile.weight_kg, source, report, dry_run=dry_run)
    _queue_age_review(db, food_profile, profile.age, profile.age_months, source, report, dry_run=dry_run)
    _queue_text_review(db, food_profile, "medical_restrictions", profile.medical_restrictions, source, report, dry_run=dry_run)
    _queue_text_review(db, food_profile, "banned_foods", profile.banned_foods, source, report, dry_run=dry_run)
    _queue_text_review(db, food_profile, "favorite_foods", profile.favorite_foods, source, report, dry_run=dry_run)
    _queue_text_review(db, food_profile, "disliked_foods", profile.disliked_foods, source, report, dry_run=dry_run)


def _migrate_family_member_profile(
    db: Session,
    food_profile: FoodProfile,
    member: FamilyMember,
    report: FoodProfileMigrationReport,
    *,
    dry_run: bool,
) -> None:
    source = _source("family_members", member.id, REPORTER_CAREGIVER_DECLARED)
    profile = _dict(member.nutrition_profile)
    _migrate_list_field(db, food_profile, "diet_pattern", member.goals, source, report, dry_run=dry_run)
    _migrate_restrictions(db, food_profile, member.restrictions, source, report, dry_run=dry_run)
    _migrate_list_field(db, food_profile, "allergy", profile.get("allergies"), source, report, dry_run=dry_run)
    _migrate_list_field(db, food_profile, "allergy", profile.get("custom_allergies"), source, report, dry_run=dry_run)
    _migrate_restrictions(db, food_profile, profile.get("restrictions"), source, report, dry_run=dry_run)
    _migrate_restrictions(db, food_profile, profile.get("custom_restrictions"), source, report, dry_run=dry_run)
    _migrate_typed_entries(db, food_profile, profile.get("typed_safety_profile"), source, report, dry_run=dry_run)
    _migrate_typed_entries(db, food_profile, profile.get("typed_medical_context"), source, report, dry_run=dry_run)
    _migrate_scalar(db, food_profile, "nutrition_goal", profile.get("nutrition_goal"), source, report, dry_run=dry_run)
    _migrate_scalar(db, food_profile, "life_stage", profile.get("life_stage"), source, report, dry_run=dry_run)
    _migrate_scalar(db, food_profile, "gender", profile.get("gender") or profile.get("sex"), source, report, dry_run=dry_run)
    _queue_age_review(db, food_profile, profile.get("age") or profile.get("age_years"), profile.get("age_months"), source, report, dry_run=dry_run)
    _queue_text_review(db, food_profile, "notes", profile.get("notes"), source, report, dry_run=dry_run)


def _source(source_legacy_table: str, source_legacy_id: int, reporter_role: str) -> dict[str, Any]:
    return {
        "source_kind": SOURCE_LEGACY_MIGRATED,
        "source_legacy_table": source_legacy_table,
        "source_legacy_id_text": str(source_legacy_id),
        "reporter_role": reporter_role,
        "migration_status": "legacy_food_profile_migrated_with_reconfirmation_boundaries",
    }


def _migrate_list_field(
    db: Session,
    food_profile: FoodProfile,
    fact_type: str,
    raw: Any,
    source: dict[str, Any],
    report: FoodProfileMigrationReport,
    *,
    dry_run: bool,
) -> None:
    values = _list(raw)
    if raw is not None and not values:
        report.ambiguous_empty_legacy_values += 1
        _ensure_reconfirmation(
            db,
            food_profile,
            fact_type,
            "legacy_empty_value",
            "empty_legacy_value_not_known_none",
            source,
            report,
            dry_run=dry_run,
        )
        return
    for value in values:
        key = _key(value)
        if not key:
            continue
        if key in NO_VALUE_TOKENS:
            report.explicit_known_none_facts += 1
            _ensure_fact(
                db,
                food_profile,
                fact_type,
                "none",
                KnowledgeState.KNOWN_NONE.value,
                None,
                source,
                report,
                confirmation_status="UNCONFIRMED",
                dry_run=dry_run,
            )
        else:
            _ensure_fact(
                db,
                food_profile,
                fact_type,
                key,
                KnowledgeState.KNOWN_PRESENT.value,
                {"value": value, "normalized_key": key},
                source,
                report,
                confirmation_status="UNCONFIRMED",
                dry_run=dry_run,
            )


def _migrate_restrictions(
    db: Session,
    food_profile: FoodProfile,
    raw: Any,
    source: dict[str, Any],
    report: FoodProfileMigrationReport,
    *,
    dry_run: bool,
) -> None:
    values = _list(raw)
    if raw is not None and not values:
        report.ambiguous_empty_legacy_values += 1
        _ensure_reconfirmation(
            db,
            food_profile,
            "food_restriction",
            "legacy_empty_value",
            "empty_legacy_value_not_known_none",
            source,
            report,
            dry_run=dry_run,
        )
        return
    for value in values:
        key = _key(value)
        if not key:
            continue
        if key in NO_VALUE_TOKENS:
            report.explicit_known_none_facts += 1
            _ensure_fact(
                db,
                food_profile,
                "food_restriction",
                "none",
                KnowledgeState.KNOWN_NONE.value,
                None,
                source,
                report,
                confirmation_status="UNCONFIRMED",
                dry_run=dry_run,
            )
        elif key in INTOLERANCE_TOKENS:
            _ensure_fact(
                db,
                food_profile,
                "intolerance",
                "lactose",
                KnowledgeState.KNOWN_PRESENT.value,
                {"value": value, "normalized_key": "lactose"},
                source,
                report,
                confirmation_status="UNCONFIRMED",
                dry_run=dry_run,
            )
        else:
            _ensure_fact(
                db,
                food_profile,
                "food_restriction",
                key,
                KnowledgeState.KNOWN_PRESENT.value,
                {"value": value, "normalized_key": key},
                source,
                report,
                confirmation_status="UNCONFIRMED",
                dry_run=dry_run,
            )


def _migrate_typed_entries(
    db: Session,
    food_profile: FoodProfile,
    raw: Any,
    source: dict[str, Any],
    report: FoodProfileMigrationReport,
    *,
    dry_run: bool,
) -> None:
    values = _list(raw)
    if raw is not None and not values:
        report.ambiguous_empty_legacy_values += 1
        _ensure_reconfirmation(
            db,
            food_profile,
            "typed_food_safety_context",
            "legacy_empty_value",
            "empty_legacy_value_not_known_none",
            source,
            report,
            dry_run=dry_run,
        )
        return
    for entry in values:
        data = _dict(entry)
        key = _key(
            data.get("concept_id")
            or data.get("code")
            or data.get("condition")
            or data.get("name")
            or data.get("value")
            or entry
        )
        if not key:
            continue
        kind = _key(data.get("kind") or data.get("type") or data.get("category"))
        fact_type = "medical_food_context" if key in CELIAC_TOKENS or "medical" in kind else "typed_food_safety_context"
        if "allerg" in kind:
            fact_type = "allergy"
        elif "intolerance" in kind:
            fact_type = "intolerance"
        _ensure_fact(
            db,
            food_profile,
            fact_type,
            key,
            KnowledgeState.KNOWN_PRESENT.value,
            {"typed_entry": data or entry, "normalized_key": key},
            source,
            report,
            confirmation_status="UNCONFIRMED",
            dry_run=dry_run,
        )


def _migrate_scalar(
    db: Session,
    food_profile: FoodProfile,
    fact_type: str,
    value: Any,
    source: dict[str, Any],
    report: FoodProfileMigrationReport,
    *,
    dry_run: bool,
) -> None:
    key = _key(value)
    if not key:
        return
    _ensure_fact(
        db,
        food_profile,
        fact_type,
        key,
        KnowledgeState.KNOWN_PRESENT.value,
        {"value": value, "normalized_key": key},
        source,
        report,
        confirmation_status="UNCONFIRMED",
        dry_run=dry_run,
    )


def _migrate_measurement(
    db: Session,
    food_profile: FoodProfile,
    fact_type: str,
    value: Any,
    source: dict[str, Any],
    report: FoodProfileMigrationReport,
    *,
    dry_run: bool,
) -> None:
    if value is None:
        return
    _ensure_fact(
        db,
        food_profile,
        fact_type,
        fact_type,
        KnowledgeState.KNOWN_PRESENT.value,
        {"value": value, "unit": "cm" if fact_type == "height_cm" else "kg"},
        source,
        report,
        confirmation_status="UNCONFIRMED",
        dry_run=dry_run,
    )


def _queue_age_review(
    db: Session,
    food_profile: FoodProfile,
    age: Any,
    age_months: Any,
    source: dict[str, Any],
    report: FoodProfileMigrationReport,
    *,
    dry_run: bool,
) -> None:
    if age is None and age_months is None:
        return
    _ensure_reconfirmation(
        db,
        food_profile,
        "age_context",
        "legacy_declared_age",
        "legacy_age_not_core_birth_date",
        source,
        report,
        prompt_text="Confirm age or date of birth precision before using age-derived nutrition logic.",
        dry_run=dry_run,
    )


def _queue_text_review(
    db: Session,
    food_profile: FoodProfile,
    fact_type: str,
    value: Any,
    source: dict[str, Any],
    report: FoodProfileMigrationReport,
    *,
    dry_run: bool,
) -> None:
    if not isinstance(value, str) or not value.strip():
        return
    report.free_text_reconfirmation_cases += 1
    _ensure_reconfirmation(
        db,
        food_profile,
        fact_type,
        "legacy_free_text",
        "free_text_requires_user_reconfirmation",
        source,
        report,
        prompt_text=f"Review legacy {fact_type} free text before converting it into typed food facts.",
        dry_run=dry_run,
    )


def _ensure_fact(
    db: Session,
    food_profile: FoodProfile,
    fact_type: str,
    fact_key: str,
    knowledge_state: str,
    value_json: Any,
    source: dict[str, Any],
    report: FoodProfileMigrationReport,
    *,
    confirmation_status: str,
    dry_run: bool,
) -> FoodProfileFact | None:
    existing = db.scalar(
        select(FoodProfileFact).where(
            FoodProfileFact.food_profile_id == food_profile.food_profile_id,
            FoodProfileFact.fact_type == fact_type,
            FoodProfileFact.fact_key == fact_key,
            FoodProfileFact.source_kind == source["source_kind"],
            FoodProfileFact.source_legacy_table == source["source_legacy_table"],
            FoodProfileFact.source_legacy_id_text == source["source_legacy_id_text"],
        )
    )
    if existing is not None:
        report.facts_reused += 1
        return existing
    report.facts_created += 1
    if dry_run:
        return None
    fact = FoodProfileFact(
        fact_id=uuid7_str(),
        food_profile_id=food_profile.food_profile_id,
        fact_type=fact_type,
        fact_key=fact_key,
        knowledge_state=knowledge_state,
        value_json=value_json,
        provenance_json=dict(source),
        source_kind=source["source_kind"],
        source_legacy_table=source["source_legacy_table"],
        source_legacy_id_text=source["source_legacy_id_text"],
        confirmation_status=confirmation_status,
    )
    db.add(fact)
    return fact


def _ensure_reconfirmation(
    db: Session,
    food_profile: FoodProfile,
    fact_type: str,
    fact_key: str,
    reason: str,
    source: dict[str, Any],
    report: FoodProfileMigrationReport,
    *,
    prompt_text: str | None = None,
    dry_run: bool,
) -> FoodProfileReconfirmation | None:
    existing = db.scalar(
        select(FoodProfileReconfirmation).where(
            FoodProfileReconfirmation.food_profile_id == food_profile.food_profile_id,
            FoodProfileReconfirmation.fact_type == fact_type,
            FoodProfileReconfirmation.fact_key == fact_key,
            FoodProfileReconfirmation.reason == reason,
            FoodProfileReconfirmation.source_legacy_table == source["source_legacy_table"],
            FoodProfileReconfirmation.source_legacy_id_text == source["source_legacy_id_text"],
        )
    )
    if existing is not None:
        report.reconfirmations_reused += 1
        return existing
    report.reconfirmations_created += 1
    if dry_run:
        return None
    reconfirmation = FoodProfileReconfirmation(
        reconfirmation_id=uuid7_str(),
        food_profile_id=food_profile.food_profile_id,
        fact_type=fact_type,
        fact_key=fact_key,
        reason=reason,
        prompt_text=prompt_text,
        status="PENDING",
        provenance_json=dict(source),
        source_kind=source["source_kind"],
        source_legacy_table=source["source_legacy_table"],
        source_legacy_id_text=source["source_legacy_id_text"],
    )
    db.add(reconfirmation)
    return reconfirmation


def _list(raw: Any) -> list[Any]:
    if raw is None:
        return []
    if isinstance(raw, str):
        stripped = raw.strip()
        if not stripped:
            return []
        try:
            loaded = json.loads(stripped)
        except json.JSONDecodeError:
            return [stripped]
        return _list(loaded)
    if isinstance(raw, tuple):
        return list(raw)
    if isinstance(raw, list):
        return raw
    if isinstance(raw, set):
        return sorted(raw)
    return [raw]


def _dict(raw: Any) -> dict[str, Any]:
    if raw is None:
        return {}
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        stripped = raw.strip()
        if not stripped:
            return {}
        try:
            loaded = json.loads(stripped)
        except json.JSONDecodeError:
            return {}
        return loaded if isinstance(loaded, dict) else {}
    return {}


def _key(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, dict):
        return _key(value.get("concept_id") or value.get("value") or value.get("name") or value.get("label"))
    normalized = str(value).strip().lower().replace("-", "_")
    return "_".join(normalized.split())
