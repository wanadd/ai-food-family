# Rebuild And Cutover

## Strategy

The target migration strategy is additive, staged, conservative, and evidence-backed. Current implementation remains current state. Target architecture is documented separately and must not be distorted to match legacy convenience.

## Legacy profile policy

Legacy profile data is migration input, not target model authority. Explicit and semantically unambiguous facts may migrate. Ambiguous facts require reconfirmation. Derived facts are recalculated. Obsolete facts are discarded or archived by policy. Unsafe interpretation is never converted into deterministic certainty.

Legacy `allergies=[]` must not automatically mean verified `KNOWN_NONE` unless legacy semantics prove it. Legacy `age=2` must not manufacture `birth_date`.

## Legacy recipe policy

Legacy recipes are not the target canonical recipe library. Legacy recipe deletion is not authorized now. Future cutover may map, preserve references, archive, migrate selected media/history, or retire old content under a later explicit implementation/cutover task.

## Cutover sequence

1. Baseline schemas, data, runtime behavior, metrics, and rollback evidence.
2. Design target physical V2 schema and module ownership.
3. Add bounded compatibility adapters and projections with provenance and unknown states.
4. Migrate only high-confidence records with reconciliation and operator review for ambiguous records.
5. Use staged cohorts: internal/disposable, small opt-in, larger cohort, V2 authority, legacy retirement.
6. Use a controlled write pause when required: freeze, snapshot, migrate/reconcile, authority switch, validate, resume.
7. Retire compatibility code only after explicit criteria are met.

## Prohibitions and gates

Dual authoritative write is prohibited. There must be one authoritative writer for a given source of truth at every stage.

RI-2 is PASS for V2 database temporal integrity after Run A Wave 5. No uncontrolled NutritionTarget backfill is authorized; numeric SLO/RPO/RTO values remain deferred until real operational baseline exists.

Target schema authority transition is accepted as `LEGACY_SCHEMA_AUTHORITY -> VERIFIED_BASELINE -> SINGLE_V2_VERSIONED_MIGRATION_AUTHORITY`. Alembic is the V2 migration mechanism established in Wave 01. Wave 02 adds Core identity roots and legacy identity mappings under that authority.

Current Food APIs remain compatibility consumers of legacy user/family/member tables until a later cutover wave explicitly switches read/write authority.

Legacy recipe compatibility is bounded. Old public recipe IDs resolve through a compatibility resolver, then to canonical mapping when available, or to archive fallback when unmapped. Retirement requires explicit gates: canonical coverage sufficient, legacy references mapped or archive-resolvable, residual compatibility usage acceptable, historical records readable, no active canonical writer depends on the legacy recipe table, and owner approval.

Run A implements the additive Wave 5-7 V2 schema contracts only. It does not implement ImportantDate, AI memory, ORM 01E1, mass recipe migration, profile migration, database mutation, push, merge, deploy, or production change.
