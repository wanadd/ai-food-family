# Current State

The repository is at the accepted architecture baseline on the feature branch. The current runtime remains the existing modular monolith and the accepted physical schema checkpoint is historical evidence, not a claim that the target architecture has been implemented.

Wave 4 adds the V2 food evidence foundation as an additive source/provenance layer: evidence sources, source snapshots, evidence records and claims, composition facts, product label facts, and fact links are versioned-migration-owned. Wave 5 adds the versioned `nutrition_target_versions` table with PostgreSQL range exclusion for RI-2. Wave 6 adds additive Recipe V2 and Wave 7 adds additive Planning V2. Wave 8 adds provenance-aware Shopping/Pantry/Receipt proposal tables and typed contracts. Existing legacy evidence/product/target/recipe/menu/shopping/pantry/receipt tables remain preserved as compatibility surfaces; Cooking/Consumption V2, Health, ImportantDate, and PlanAm_money remain outside the completed scope until later gates.

Historical acceptance: CREATE_ALL_TABLES 47, CUSTOM_SQL_TABLES 7, Recipe Engine tables 6, authority overlap 0, physical schema 60/60, and full backend 1204 passed with 3 warnings. Wave 5 closes RI-2 for V2 schema integrity without backfill. Wave 6 adds additive Recipe/RecipeVersion, media, validation, and bounded legacy mapping/archive tables. Wave 7 adds versioned Plan/Revision/Slot, explicit-empty semantics, participants, portions, and legacy menu compatibility; legacy recipes and menus remain preserved and are not mass-converted or deleted.

Known current-state gaps remain: profile DTO completeness, fail-open menu sanitization, unknown-as-zero health/inferred macros, OCR uncertainty loss, job durability, and duplicate recipe/consumption truth. They are preserved as remediation input, not silently represented as completed target behavior.

Wave 01 V2 implementation is present: Alembic configuration, a marker-only baseline revision, explicit schema authority boundary checks, reference enum contracts, UUIDv7 generation, and a PostgreSQL migration acceptance harness.

Wave 02 Core roots are present in versioned migrations only: accounts, auth identities, persons, households, memberships, person relationships, permission grants, and legacy id mappings. Legacy user/family/family_member mapping is additive and idempotent. Telegram auth and current Food family behavior remain on the existing compatibility path.

Current runtime still uses the existing deterministic bootstrap authority for legacy tables during transition. V2 application objects are reserved for versioned migrations only, and Wave 02 creates no FoodProfile, Recipe V2, planning, shopping, pantry, cooking, consumption, health, or ImportantDate tables.
