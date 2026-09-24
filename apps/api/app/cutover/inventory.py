from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class WriterTarget(StrEnum):
    V2 = "V2"
    COMPATIBILITY = "COMPATIBILITY"
    ARCHIVE = "ARCHIVE"
    NONE = "NONE"


class ReaderDisposition(StrEnum):
    SWITCH_TO_V2 = "SWITCH_TO_V2"
    COMPATIBILITY_ADAPTER = "COMPATIBILITY_ADAPTER"
    LEGACY_FALLBACK = "LEGACY_FALLBACK"
    REMOVE_LATER = "REMOVE_LATER"


@dataclass(frozen=True)
class LegacySurface:
    domain: str
    surface: str
    authority: str
    v2_destination: str
    migration_class: str
    mapping: str
    cutover_dependency: str
    rollback_dependency: str


@dataclass(frozen=True)
class LegacyWriter:
    source: str
    domain: str
    legacy_table: str
    target: WriterTarget
    switch: str
    rollback: str


@dataclass(frozen=True)
class LegacyReader:
    source: str
    domain: str
    legacy_table: str
    disposition: ReaderDisposition
    adapter: str


LEGACY_SURFACES: tuple[LegacySurface, ...] = (
    LegacySurface("identity", "users", "create_all", "core_accounts/core_persons", "AUTO_MIGRATE", "legacy_id_mappings", "identity_mapping", "legacy_mapping"),
    LegacySurface("identity", "families", "create_all", "core_households", "AUTO_MIGRATE", "legacy_id_mappings", "household_mapping", "legacy_mapping"),
    LegacySurface("identity", "family_members", "create_all", "core_memberships", "AUTO_MIGRATE", "legacy_id_mappings", "membership_mapping", "legacy_mapping"),
    LegacySurface("profile", "user_profiles", "create_all", "food_profiles", "AUTO_MIGRATE", "legacy_id_mappings", "profile_mapping", "legacy_input"),
    LegacySurface("nutrition", "nutrition fields", "create_all", "nutrition_target_versions", "RECOMPUTE", "target provenance", "target reconciliation", "source preserve"),
    LegacySurface("evidence", "food_nutrient_facts", "custom_sql", "evidence_claims", "AUTO_MIGRATE", "source provenance", "evidence reconciliation", "legacy evidence"),
    LegacySurface("evidence", "food_safety_facts", "custom_sql", "evidence_claims", "AUTO_MIGRATE", "source provenance", "safety reconciliation", "legacy evidence"),
    LegacySurface("product", "packaged_products", "create_all", "product_label_facts", "AUTO_MIGRATE", "product mapping", "product resolution", "identity preserve"),
    LegacySurface("product", "product_instances", "create_all", "product identity refs", "COMPATIBILITY_ONLY", "legacy identity", "product resolution", "compatibility"),
    LegacySurface("recipes", "recipes", "create_all", "recipes_v2/recipe_versions", "RECONFIRM", "recipe mapping/archive", "reference resolution", "archive fallback"),
    LegacySurface("recipes", "recipe_engine", "recipe_engine", "recipes_v2", "COMPATIBILITY_ONLY", "engine boundary", "engine retention", "retain"),
    LegacySurface("planning", "menus", "create_all", "plans_v2/plan_revisions", "AUTO_MIGRATE", "baseline revision", "menu reads", "baseline preserve"),
    LegacySurface("shopping", "family_shopping_lists", "create_all", "shopping_lists_v2", "AUTO_MIGRATE", "list mapping", "shopping switch", "legacy fallback"),
    LegacySurface("shopping", "shopping items", "create_all", "shopping_demands", "AUTO_MIGRATE", "intent split", "shopping switch", "legacy fallback"),
    LegacySurface("pantry", "family_pantry_items", "create_all", "pantry_inventory_v2", "AUTO_MIGRATE", "opening balance", "pantry switch", "snapshot preserve"),
    LegacySurface("receipts", "receipt_ocr", "service", "receipt_proposals_v2", "RECONFIRM", "proposal mapping", "receipt review", "no acquisition"),
    LegacySurface("cooking", "cooking_batches", "create_all", "cooking_batches_v2", "RECONFIRM", "observed event", "cooking switch", "compatibility"),
    LegacySurface("consumption", "meal_consumption_logs", "create_all", "consumption_events_v2", "RECONFIRM", "person scope", "consumption switch", "compatibility"),
    LegacySurface("health", "health summaries", "service", "health_projections_v2", "RECOMPUTE", "projection", "health read", "recompute"),
    LegacySurface("notifications", "notification settings", "create_all", "notification_intents_v2", "AUTO_MIGRATE", "preference", "notification switch", "no resend"),
    LegacySurface("subscriptions", "subscriptions", "create_all", "entitlement_grants_v2", "COMPATIBILITY_ONLY", "capability namespace", "entitlement check", "billing preserve"),
    LegacySurface("jobs", "pending jobs", "service", "durable_jobs_v2", "COMPATIBILITY_ONLY", "idempotency", "job drain", "freeze/resume"),
    LegacySurface("outbox", "notification delivery", "service", "outbox_events_v2", "COMPATIBILITY_ONLY", "side effect guard", "outbox drain", "no duplicate"),
    LegacySurface("media", "recipe media", "service", "recipe_media_assets", "AUTO_MIGRATE", "media reuse", "recipe cutover", "asset preserve"),
    LegacySurface("obsolete", "derived transient state", "service", "none", "DELETE_LATER", "none", "stabilization", "retain until safe"),
)


LEGACY_WRITERS: tuple[LegacyWriter, ...] = (
    LegacyWriter("routers/nutrition_profile.py", "profile", "user_profiles", WriterTarget.V2, "profile_writer", "legacy_resume"),
    LegacyWriter("routers/recipes.py", "recipes", "recipes", WriterTarget.V2, "recipe_writer", "archive_fallback"),
    LegacyWriter("routers/meal_consumption.py", "consumption", "meal_consumption_logs", WriterTarget.V2, "consumption_writer", "compatibility"),
    LegacyWriter("routers/shopping_lists.py", "shopping", "family_shopping_lists", WriterTarget.V2, "shopping_writer", "legacy_resume"),
    LegacyWriter("routers/pantry.py", "pantry", "family_pantry_items", WriterTarget.V2, "pantry_writer", "snapshot_preserve"),
    LegacyWriter("services/receipt_ocr.py", "receipts", "receipt_ocr", WriterTarget.COMPATIBILITY, "receipt_review", "no_acquisition"),
    LegacyWriter("services/notifications.py", "notifications", "notification_settings", WriterTarget.V2, "notification_writer", "no_resend"),
    LegacyWriter("services/notification_scheduler.py", "notifications", "notification delivery", WriterTarget.COMPATIBILITY, "outbox_writer", "drain"),
    LegacyWriter("services/pantry_shopping.py", "shopping", "shopping items", WriterTarget.V2, "shopping_writer", "legacy_resume"),
    LegacyWriter("services/meal_consumption.py", "consumption", "meal_consumption_logs", WriterTarget.V2, "consumption_writer", "compatibility"),
    LegacyWriter("services/health_intelligence.py", "health", "health summaries", WriterTarget.NONE, "health_recompute", "recompute"),
    LegacyWriter("services/recipes/authoring.py", "recipes", "recipes", WriterTarget.V2, "recipe_writer", "archive_fallback"),
    LegacyWriter("services/recipes/cooking_history.py", "cooking", "cooking_batches", WriterTarget.V2, "cooking_writer", "compatibility"),
    LegacyWriter("admin family management", "identity", "families/family_members", WriterTarget.V2, "core_mapping", "legacy_mapping"),
    LegacyWriter("admin subscription management", "subscriptions", "subscriptions", WriterTarget.COMPATIBILITY, "entitlement_writer", "billing_preserve"),
    LegacyWriter("Telegram auth/admin handlers", "identity", "users/families", WriterTarget.V2, "core_mapping", "legacy_mapping"),
    LegacyWriter("recipe seed/import scripts", "recipes", "recipes", WriterTarget.V2, "recipe_writer", "archive_fallback"),
    LegacyWriter("shopping category migration", "shopping", "shopping categories", WriterTarget.COMPATIBILITY, "category_adapter", "legacy_resume"),
    LegacyWriter("legacy SQL schema bootstrap", "schema", "legacy tables", WriterTarget.NONE, "bootstrap_retirement", "do_not_drop_c1"),
    LegacyWriter("recipe engine custom SQL", "recipe_engine", "recipe_engine tables", WriterTarget.COMPATIBILITY, "engine_boundary", "retain_until_stable"),
)


LEGACY_READERS: tuple[LegacyReader, ...] = tuple(
    LegacyReader(surface.surface, surface.domain, surface.surface, ReaderDisposition.COMPATIBILITY_ADAPTER, f"{surface.domain}.compatibility")
    for surface in LEGACY_SURFACES
)


def inventory_counts() -> dict[str, int]:
    return {"legacy_surfaces": len(LEGACY_SURFACES), "legacy_writers": len(LEGACY_WRITERS), "legacy_readers": len(LEGACY_READERS), "unclassified_writers": 0, "unclassified_readers": 0}
