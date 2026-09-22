# Current State

The repository is at the accepted architecture baseline on the feature branch. The current runtime remains the existing modular monolith and the accepted physical schema checkpoint is historical evidence, not a claim that the target architecture has been implemented.

Historical acceptance: CREATE_ALL_TABLES 47, CUSTOM_SQL_TABLES 7, Recipe Engine tables 6, authority overlap 0, physical schema 60/60, and full backend 1204 passed with 3 warnings. Fresh bootstrap, repeat bootstrap, preservation, concurrency 2/2, aborted-transaction recovery, failure restart, and Recipe Engine were accepted in the prior checkpoint. RI-2 is `BLOCKING_BEFORE_BACKFILL`.

Known current-state gaps remain: profile DTO completeness, fail-open menu sanitization, unknown-as-zero health/inferred macros, OCR uncertainty loss, job durability, and duplicate recipe/consumption truth. They are preserved as remediation input, not silently represented as completed target behavior.

Wave 01 V2 implementation is present as a foundation only: Alembic configuration, a marker-only baseline revision, explicit schema authority boundary checks, reference enum contracts, UUIDv7 generation, and a PostgreSQL migration acceptance harness.

Current runtime still uses the existing deterministic bootstrap authority for legacy tables during transition. V2 application objects are reserved for versioned migrations only, and Wave 01 creates no Core, FoodProfile, Recipe V2, planning, shopping, pantry, cooking, consumption, health, or ImportantDate tables.
