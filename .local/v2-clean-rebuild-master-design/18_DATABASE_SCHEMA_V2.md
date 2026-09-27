# Database Schema V2

One PostgreSQL database, logical ownership by domain, one versioned migration authority. New IDs are UUIDv7. Every tenant-owned row carries `household_id` or `person_id` as appropriate and constraints prevent cross-scope references.

## Core schema
`accounts`, `external_identities`, `verified_contacts`, `sessions`, `persons`, `households`, `memberships`, `person_relationships`, `permission_grants`, `legacy_id_mappings`.

`ExternalIdentity(provider, provider_subject)` is unique and provider-verified. `VerifiedContact` is optional, purpose-scoped and never the Account primary key. `Session` stores account, client type, issued/expiry/revocation, last activity and security metadata; provider init data is authentication evidence, not the session lifecycle.

## Food/evidence schema
`food_profiles`, `food_profile_facts`, `food_profile_reconfirmations`, `food_identities`, `food_aliases`, `food_composition_facts`, `packaged_products`, `product_instances`, `product_label_facts`, `source_registry`, `source_snapshots`, `evidence_records`, `evidence_claims`, `evidence_applicability`, `food_evidence_links`, `safety_rules`, `safety_decisions`, `nutrition_targets`.

## Recipe/media schema
`recipes`, `recipe_versions`, `recipe_ingredients`, `recipe_steps`, `recipe_tags`, `recipe_media`, `media_assets`, `recipe_validation_runs`, `recipe_legacy_mappings`, `recipe_archive_fallbacks`, `recipe_favorites`, `recipe_history`.

## Planning through operations
`plans`, `plan_revisions`, `plan_slots`, `plan_assignments`, `plan_participants`, `plan_portions`, `shopping_lists`, `shopping_demands`, `shopping_items`, `purchase_events`, `pantry_inventory`, `pantry_movements`, `receipt_documents`, `receipt_proposals`, `receipt_lines`, `cooking_sessions`, `prepared_foods`, `cooking_events`, `consumption_events`, `consumption_items`, `health_projections`, `health_deviations`, `notification_preferences`, `notification_intents`, `notification_deliveries`, `entitlement_plans`, `entitlement_grants`, `entitlement_consumptions`, `jobs`, `outbox_events`, `admin_audit_events`, `analytics_events`, `import_runs`, `import_records`, `backup_manifests`.

OD-15 ownership: `plans.person_id` and `plans.household_id` are nullable canonical foreign keys with exactly one populated. PostgreSQL must enforce `(person_id IS NOT NULL AND household_id IS NULL) OR (person_id IS NULL AND household_id IS NOT NULL)`. `PlanRevision`, `PlanSlot`, `Assignment`, `PlanParticipant` and `PlanPortion` inherit authorization through their Plan/Revision parent; child IDs are not independent scope authorities. Personal Plans have no implicit household.

## Identity and client neutrality
Provider IDs, Telegram file IDs, provider URLs and device tokens are integration metadata only. Business tables reference canonical Account/Person/Household/Recipe/MediaAsset IDs. Stable UUIDv7, `updated_at`, immutable revisions and idempotency keys provide future cache/offline boundaries without introducing sync/CRDT/event sourcing.

## Integrity
Use PK/FK/NOT NULL/UNIQUE/CHECK constraints for scope, state transitions, positive amounts, valid time ranges, explicit knowledge states, idempotency keys and immutable version rows. PostgreSQL enforces tenant FK pairing and effective-range non-overlap for active targets. Application enforces policy, authorization and safety decisions. Repositories never commit.
