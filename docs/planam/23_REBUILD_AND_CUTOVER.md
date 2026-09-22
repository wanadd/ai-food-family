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

RI-2 remains `BLOCKING_BEFORE_BACKFILL`. No backfill is authorized before RI-2 is resolved. Numeric SLO/RPO/RTO values are deferred until real operational baseline exists.

This checkpoint does not implement target physical V2 schema, ImportantDate, AI memory, ORM 01E1, recipe migration, profile migration, database mutation, push, merge, deploy, or production change.
