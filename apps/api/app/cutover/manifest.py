from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import StrEnum
from typing import Any


class MigrationClass(StrEnum):
    AUTO_MIGRATE = "AUTO_MIGRATE"
    RECOMPUTE = "RECOMPUTE"
    RECONFIRM = "RECONFIRM"
    ARCHIVE_ONLY = "ARCHIVE_ONLY"
    COMPATIBILITY_ONLY = "COMPATIBILITY_ONLY"
    DO_NOT_MIGRATE = "DO_NOT_MIGRATE"
    DELETE_LATER = "DELETE_LATER"


@dataclass(frozen=True)
class MigrationManifestEntry:
    domain: str
    legacy_source: str
    v2_destination: str
    migration_class: MigrationClass
    transform_id: str
    validation_id: str
    rollback_relevance: str


def _entry(domain: str, source: str, destination: str, kind: MigrationClass, transform: str, validation: str, rollback: str) -> MigrationManifestEntry:
    return MigrationManifestEntry(domain, source, destination, kind, transform, validation, rollback)


MIGRATION_MANIFEST: tuple[MigrationManifestEntry, ...] = (
    _entry("identity", "users/families/family_members", "core_accounts/core_persons/core_households/core_memberships", MigrationClass.AUTO_MIGRATE, "core.identity.v1", "core.mapping.idempotent", "preserve_legacy_mapping"),
    _entry("profile", "user_profiles/family_members.nutrition_profile", "food_profiles/food_profile_facts", MigrationClass.AUTO_MIGRATE, "food_profile.knowledge_state.v1", "food_profile.reconfirmation.v1", "keep_legacy_input"),
    _entry("profile", "free_text_medical_restrictions", "food_profile_reconfirmations", MigrationClass.RECONFIRM, "profile.free_text.review.v1", "profile.reconfirm.queue.v1", "never_promote"),
    _entry("evidence", "food_nutrient_facts/food_safety_facts", "evidence_records/evidence_claims", MigrationClass.AUTO_MIGRATE, "evidence.source_preserving.v1", "evidence.provenance.v1", "legacy_read_fallback"),
    _entry("product", "packaged_products/product_instances", "product_label_facts/food_evidence_fact_links", MigrationClass.AUTO_MIGRATE, "product.identity_mapping.v1", "product.provenance.v1", "keep_identity_mapping"),
    _entry("nutrition", "legacy_nutrition_targets", "nutrition_target_versions", MigrationClass.AUTO_MIGRATE, "nutrition.interval_preserving.v1", "nutrition.ri2.v1", "retain_origin"),
    _entry("nutrition", "legacy_estimator_output", "nutrition_target_versions", MigrationClass.RECOMPUTE, "nutrition.recompute.v1", "nutrition.provenance.v1", "do_not_relabel"),
    _entry("recipes", "recipes", "recipes_v2/recipe_versions", MigrationClass.RECONFIRM, "recipe.explicit_mapping.v1", "recipe.reference_resolution.v1", "archive_fallback"),
    _entry("recipes", "recipe_images/media", "recipe_media_assets/recipe_version_media", MigrationClass.AUTO_MIGRATE, "recipe.media_reuse.v1", "recipe.media_integrity.v1", "preserve_assets"),
    _entry("recipes", "unmapped_legacy_recipes", "recipe_archive_fallbacks", MigrationClass.ARCHIVE_ONLY, "recipe.archive.v1", "recipe.archive_resolution.v1", "archive_payload"),
    _entry("planning", "menus/menu_items", "plans_v2/plan_revisions/plan_slots", MigrationClass.AUTO_MIGRATE, "planning.baseline_revision.v1", "planning.intent.v1", "immutable_imported_baseline"),
    _entry("planning", "cleared_menu_slots", "plan_slots", MigrationClass.AUTO_MIGRATE, "planning.explicit_empty.v1", "planning.empty_slot.v1", "preserve_empty"),
    _entry("shopping", "family_shopping_lists/items", "shopping_lists_v2/shopping_demands", MigrationClass.AUTO_MIGRATE, "shopping.intent_split.v1", "shopping.checked_not_purchase.v1", "retain_legacy_input"),
    _entry("pantry", "family_pantry_items", "pantry_inventory_v2", MigrationClass.AUTO_MIGRATE, "pantry.opening_balance.v1", "pantry.opening_balance.v1", "opening_balance_only"),
    _entry("pantry", "legacy_pantry_history_missing", "pantry_movements_v2", MigrationClass.DO_NOT_MIGRATE, "pantry.no_fabricated_history.v1", "pantry.no_fake_purchase.v1", "preserve_snapshot"),
    _entry("receipts", "receipt_ocr", "receipt_proposals_v2", MigrationClass.RECONFIRM, "receipt.ocr_proposal.v1", "receipt.unverified.v1", "no_acquisition"),
    _entry("cooking", "cooking_batches", "cooking_batches_v2/cooking_events_v2", MigrationClass.RECONFIRM, "cooking.observed_event.v1", "cooking.no_intent_proof.v1", "compatibility_only"),
    _entry("consumption", "meal_consumption_logs", "consumption_events_v2", MigrationClass.RECONFIRM, "consumption.person_scoped.v1", "consumption.no_cooked_inference.v1", "compatibility_only"),
    _entry("health", "health summaries", "health_projections_v2", MigrationClass.RECOMPUTE, "health.projection.v1", "health.completeness.v1", "recompute_from_facts"),
    _entry("notifications", "notification settings", "notification_intents_v2/notification_deliveries_v2", MigrationClass.AUTO_MIGRATE, "notification.preference.v1", "notification.dedupe.v1", "do_not_resend"),
    _entry("entitlements", "subscriptions", "entitlement_grants_v2", MigrationClass.COMPATIBILITY_ONLY, "entitlement.namespace.v1", "entitlement.access.v1", "do_not_rewrite_billing"),
    _entry("jobs", "legacy pending jobs", "durable_jobs_v2/outbox_events_v2", MigrationClass.COMPATIBILITY_ONLY, "jobs.side_effect_guard.v1", "jobs.idempotency.v1", "drain_or_freeze"),
    _entry("recipe_engine", "recipe_engine tables", "recipes_v2/recipe_versions", MigrationClass.COMPATIBILITY_ONLY, "recipe_engine.boundary.v1", "recipe.authority.v1", "retain_until_stable"),
    _entry("obsolete", "derived transient rows", "none", MigrationClass.DELETE_LATER, "obsolete.defer.v1", "obsolete.scope.v1", "delete_only_after_stabilization"),
)


def manifest_as_dicts() -> list[dict[str, Any]]:
    return [{**asdict(entry), "migration_class": entry.migration_class.value} for entry in MIGRATION_MANIFEST]


def manifest_class_counts() -> dict[str, int]:
    counts = {kind.value: 0 for kind in MigrationClass}
    for entry in MIGRATION_MANIFEST:
        counts[entry.migration_class.value] += 1
    return counts
