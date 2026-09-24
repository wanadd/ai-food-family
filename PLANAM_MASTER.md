# PLANAM Master

## Canonical status

PLANAM is accepted as a modular monolith with explicit logical domain boundaries. This document is the durable navigation entrypoint for the accepted target architecture, the product/ecosystem direction, current implementation facts, and the next architecture stage.

The accepted physical V2 blueprint is canonical in [24_PHYSICAL_V2_BLUEPRINT.md](docs/planam/24_PHYSICAL_V2_BLUEPRINT.md). Implementation remains wave-scoped and separately authorized. Wave 01 establishes the versioned migration foundation, reference enum contracts, UUIDv7 helper, and PostgreSQL migration test harness. Wave 02 establishes Core identity roots and idempotent legacy user/family/member mapping; it does not create FoodProfile, Recipe V2, planning, shopping, pantry, cooking, consumption, health, or ImportantDate V2 tables.

## Product and ecosystem vision

PLANAM Food remains the first product surface, but the target architecture treats PLANAM as an ecosystem. Food, Planner, Health, AI, Notifications, Money, and future domains share stable Core identity and explicit contracts rather than copying profile truth into each domain.

The accepted topology now is:

- modular monolith;
- one repository/application boundary as appropriate;
- one PostgreSQL database;
- logical domain ownership;
- explicit application/domain contracts.

Later, if justified by evidence and accepted design, Core or other domains may be physically extracted. That later possibility does not change the current topology.

## PLANAM Core

PLANAM Core is the logical owner of Account, AuthIdentity, Person, Household, Membership, PersonRelationship, scoped permissions, entitlement contracts, notification preferences, restricted CorePerson facts, ImportantDate/PersonalEvent contracts, and structured long-lived ecosystem memory boundaries.

Core is not a separate service now. Core is not a separate database now. Core IDs for new canonical global entities are UUIDv7: `account_id`, `person_id`, `household_id`, and `membership_id`. UUIDv7 gives globally unique, domain-neutral, transport-neutral, storage-neutral IDs while `created_at` remains the authoritative creation timestamp.

## Non-negotiable invariants

Account is not Person. Person is not Membership. Household is not Account. A dependent Person may exist without an Account. Same `person_id` across domains does not grant universal data access. UI workflow is not the domain model, and onboarding is not a source of truth.

FoodProfile is Food-owned. CorePerson plus domain profiles is preferred over a giant global PersonProfile. Direct cross-domain database reads are prohibited by default; domains use explicit application contracts, projections, events, ports, or authorized APIs/services.

AI output is not authoritative evidence. Missing nutrient is not zero. Missing allergen is not absence. `UNKNOWN` is not `SAFE`. Allergy is not intolerance. Celiac disease is not gluten-free preference. Planned, cooked, and consumed are distinct. Person-level evaluation happens before household aggregation, and hard safety is never averaged.

## Food target architecture

The food domain owns FoodProfile, dietary policy, allergies, intolerances, celiac facts, pregnancy/process-state facts, PKU/phenylalanine facts, nutrition targets, evidence links, recipe facts, planning/menu contracts, shopping, pantry/product facts, OCR-derived facts, cooking facts, consumption facts, and food safety decisions.

The new canonical recipe library is a clean Gold V3 library built against target contracts. The legacy 174 recipes are transition data, not the target canonical library. Legacy recipe deletion is not authorized by this checkpoint.

## AI, memory, and important dates

PLANAM AI may assist, explain, propose, summarize, and orchestrate authorized workflows. It does not own identity, evidence, medical safety, entitlement truth, payment truth, or unrestricted database access.

Persistent AI memory must be structured, scoped, provenance-bearing, consent-aware, and bounded. D17 accepts ImportantDate/PersonalEvent and structured AI memory as a Core contract now, with implementation later.

## Migration and cutover

Migration is additive, staged, and conservative. Legacy profile data is migration input, not target authority. High-confidence facts may migrate; ambiguous sensitive facts require reconfirmation; derived values are recalculated; unsafe interpretation is never converted into deterministic certainty.

Compatibility layers are temporary and bounded. Dual-read may exist temporarily. Dual authoritative write is prohibited. At every stage there is one writer for a given source of truth.

## Current implementation state

Current implementation facts remain separated in [docs/planam/18_CURRENT_STATE.md](docs/planam/18_CURRENT_STATE.md). Historical implementation acceptance remains evidence: physical schema 60/60, `CREATE_ALL_TABLES = 47`, `CUSTOM_SQL_TABLES = 7`, Recipe Engine tables 6, authority overlap 0, RI-3 PASS, and full backend 1204 passed with 3 warnings.

Wave 01 V2 implementation adds Alembic as the single future V2 versioned migration authority, with a marker-only baseline revision and explicit no-dual-authority checks. Wave 02 adds `core_accounts`, `core_auth_identities`, `core_persons`, `core_households`, `core_memberships`, `core_person_relationships`, `core_permission_grants`, and `legacy_id_mappings` under V2 versioned migrations. Current legacy bootstrap remains the runtime owner for existing legacy tables during transition; application startup does not run Alembic.

Run A Waves 5-7 are accepted in three independent checkpoints. RI-2 is PASS for V2 schema integrity through PostgreSQL range/exclusion protection; no NutritionTarget backfill was performed. Recipe V2 and Planning V2 are additive and legacy-compatible. Wave 8+ remains separately unauthorized.

## Canonical document index

- Product behavior: [00_PROJECT_IDENTITY.md](docs/planam/00_PROJECT_IDENTITY.md), [01_PRODUCT_PRINCIPLES.md](docs/planam/01_PRODUCT_PRINCIPLES.md), [02_PRODUCT_ARCHITECTURE.md](docs/planam/02_PRODUCT_ARCHITECTURE.md), [03_UX_AND_PRODUCT_BEHAVIOR.md](docs/planam/03_UX_AND_PRODUCT_BEHAVIOR.md).
- Core and person model: [20_CORE_CONTRACT.md](docs/planam/20_CORE_CONTRACT.md), [12_FAMILY_AND_PERSON_MODEL.md](docs/planam/12_FAMILY_AND_PERSON_MODEL.md).
- Food, evidence, nutrition, safety, recipes, and menus: [21_FOOD_PROFILE_AND_FACTS.md](docs/planam/21_FOOD_PROFILE_AND_FACTS.md), [07_EVIDENCE_ENGINE.md](docs/planam/07_EVIDENCE_ENGINE.md), [08_NUTRITION_AND_SAFETY.md](docs/planam/08_NUTRITION_AND_SAFETY.md), [09_RECIPE_GOLD_V3.md](docs/planam/09_RECIPE_GOLD_V3.md), [10_MENU_ENGINE.md](docs/planam/10_MENU_ENGINE.md).
- Ecosystem and integrations: [22_ECOSYSTEM_CONTRACTS.md](docs/planam/22_ECOSYSTEM_CONTRACTS.md), [11_SHOPPING_AND_PANTRY.md](docs/planam/11_SHOPPING_AND_PANTRY.md), [13_TELEGRAM_AND_PLATFORM.md](docs/planam/13_TELEGRAM_AND_PLATFORM.md), [14_INFRASTRUCTURE_AND_DEPLOYMENT.md](docs/planam/14_INFRASTRUCTURE_AND_DEPLOYMENT.md).
- Cutover and status: [23_REBUILD_AND_CUTOVER.md](docs/planam/23_REBUILD_AND_CUTOVER.md), [18_CURRENT_STATE.md](docs/planam/18_CURRENT_STATE.md), [19_ROADMAP.md](docs/planam/19_ROADMAP.md).
- Physical V2 implementation blueprint: [24_PHYSICAL_V2_BLUEPRINT.md](docs/planam/24_PHYSICAL_V2_BLUEPRINT.md).
- Decisions and prohibitions: [17_DECISION_LOG.md](docs/planam/17_DECISION_LOG.md), [16_DO_NOT_DO.md](docs/planam/16_DO_NOT_DO.md), [15_TESTING_AND_QA.md](docs/planam/15_TESTING_AND_QA.md).

## Next stage

The next stage is implementation Wave 3 specification for FoodProfile. Each wave still requires its own scope, gates, and acceptance.
