# Decision Log

The owner decisions D01-D17 are accepted and override earlier recommendations or options wherever they differ. Status for all rows is `ACCEPTED`.

| ID | Title | Decision | Rationale | Consequences | Timing |
|---|---|---|---|---|---|
| D01 | PLANAM topology | Modular monolith now; Core is a logical boundary. | Current scale does not justify physical service/database split. | Boundaries must still allow later extraction. | Now |
| D02 | Global identifiers | New canonical Core IDs use UUIDv7. | IDs must be global, domain-neutral, transport-neutral, storage-neutral, and stable. | `created_at` remains creation-time authority; legacy IDs use mappings. | New Core IDs |
| D03 | Household model | Multi-household data model with one active household UI allowed. | UI constraint must not become permanent data constraint. | Person relates to Household through Membership. | Target model |
| D04 | Birth date and age | `birth_date` is restricted CorePerson PII; age is derived. | DOB has ecosystem value but requires purpose-limited access. | No competing editable DOB/age truths; no DOB invented from approximate age. | Contract now |
| D05 | Guardian, relationship, permissions | Keep PersonRelationship, Membership, and PermissionGrant distinct. | Relationship is not universal authorization. | Sensitive domains need scoped permissions and may later require stronger verification. | Contract now |
| D06 | Onboarding | Progressive onboarding; onboarding is not source of truth. | Missing answers must not become false. | All clients write through canonical contracts and preserve knowledge states. | Product/current target |
| D07 | Recipe library | Build a clean canonical Gold V3 library; legacy 174 recipes are not canonical. | Existing content must not define target architecture by convenience. | Legacy recipes are preserved as transition data; deletion is not authorized. | Target library later |
| D08 | Legacy profile migration | High-confidence migration only. | Sensitive ambiguity must not become deterministic truth. | Ambiguous facts are reconfirmed; derived facts recalculated; provenance preserved. | Migration stage |
| D09 | Entitlements | Namespaced entitlement contracts. | Domains should consume entitlement decisions, not own payment truth. | `food.*`, `money.*`, `wellbeing.*`, `planner.*` remain compatible. | Contract now |
| D10 | Notifications | Notification intent/delivery abstraction; Telegram is a channel. | Delivery channel must not become domain architecture. | Food creates intents; adapters deliver through Telegram or later channels. | Contract now |
| D11 | Cutover cohorts | Staged cutover. | Risk decreases through controlled cohort progression. | Internal/disposable, opt-in, larger cohort, V2 authority, legacy retirement. | Migration stage |
| D12 | Compatibility window | Bounded compatibility, single writer, no dual authoritative write. | Dual authority creates unrecoverable truth conflicts. | Dual-read may be temporary; compatibility must have retirement criteria. | Migration stage |
| D13 | Sensitive/raw retention | Data minimization. | Raw sensitive artifacts should not persist indefinitely by default. | Purpose, retention, provenance, deletion, and derived-data handling are required. | Contract now |
| D14 | Async jobs | DB-backed durable jobs/outbox first. | Durable, observable, idempotent jobs are needed without premature queue infrastructure. | Transport can evolve later without changing domain contracts. | Target implementation |
| D15 | Production cutover | Controlled write pause is acceptable. | Current scale does not require unnecessary distributed zero-downtime complexity. | Freeze/snapshot/migrate/reconcile/switch/validate/resume is allowed. | Cutover stage |
| D16 | SLO/RPO/RTO | Establish baseline before numeric targets. | Unsupported operational numbers would be fiction. | Define SLO, error budgets, RPO, RTO, and latency budgets after measurement. | Later |
| D17 | Important dates and structured AI memory | ImportantDate/PersonalEvent plus structured AI memory tail; contract now, implement later. | Ecosystem memory needs structure, consent, scope, and ownership. | AI may propose persistent facts but should not silently promote unrestricted memory. | CONTRACT_NOW_IMPLEMENT_LATER |

## Superseded assumptions

- A global domain-heavy PersonProfile is superseded by CorePerson plus domain-owned profiles.
- A legacy 174-recipe library as automatic canonical seed is superseded by clean Gold V3 target curation.
- Telegram as notification architecture is superseded by intent/delivery/adapters.
- Dual authoritative write is explicitly prohibited.
- A physical Core service/database is deferred until a later accepted design, if justified.

## Active blocker

RI-2 remains `BLOCKING_BEFORE_BACKFILL`; this decision log does not resolve it.

## Physical V2 owner decisions

| ID | Title | Status | Decision | Consequences | Timing |
|---|---|---|---|---|---|
| OD-01 | Target schema authority | ACCEPTED | Use one versioned migration authority at the V2 boundary. Intended implementation tool: Alembic, subject to the future implementation task validating and configuring it. | Existing deterministic bootstrap remains current-state evidence; V2 objects must not be dual-owned by create_all/custom SQL and the migration framework. | Blueprint accepted now, implementation later |
| OD-02 | Legacy recipe public ID horizon | ACCEPTED | Bounded legacy recipe ID compatibility with archive fallback for unmapped legacy recipes. | Favorites, history, menu references, cooking history, media, and supported deep links remain resolvable during compatibility; legacy recipe deletion is not authorized. | Blueprint accepted now, retirement later |

OD-01 transition: `LEGACY_SCHEMA_AUTHORITY -> VERIFIED_BASELINE -> SINGLE_V2_VERSIONED_MIGRATION_AUTHORITY`.

OD-02 transition: `LEGACY_RECIPE_ID -> compatibility resolver -> canonical mapping if available -> archive fallback if unmapped`.

## Implementation checkpoints

- Wave 01 accepted the Alembic V2 migration authority foundation.
- Wave 02 implements Core roots and idempotent legacy user/family/member mappings under V2 versioned migrations.
