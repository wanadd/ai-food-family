# Core Contract

## Purpose

PLANAM Core is the canonical logical boundary for stable ecosystem identity and shared cross-domain primitives inside the current modular monolith. It is not a separate service now and not a separate database now, but its contracts must be designed so future physical extraction remains possible.

## Core-owned concepts

Core conceptually owns Account, AuthIdentity, Person, Household, Membership, PersonRelationship, scoped PermissionGrant primitives, entitlement contracts/state, notification preference contracts, restricted CorePerson facts, consent/visibility metadata, ImportantDate/PersonalEvent contracts, and structured long-lived ecosystem memory boundaries.

Core explicitly does not own FoodProfile, food evidence, nutrition facts, recipe truth, pantry/product facts, cooking facts, consumption facts, health-domain facts, domain-specific memories, Telegram delivery semantics, payment provider truth, or arbitrary domain profile data.

## Identity model

`Account` represents authentication. `Person` represents a human. `Membership` connects a Person to a Household. `Household` is not Account. A dependent or child Person may exist without an Account. A Person may have multiple household memberships, while the current product UI may expose only one active household.

Canonical relation:

```text
Person -> Membership -> Household
```

Person must not be permanently modeled with one canonical household ownership field.

## Global IDs

New canonical Core IDs use UUIDv7:

- `account_id`;
- `person_id`;
- `household_id`;
- `membership_id`.

UUIDv7 is used for global uniqueness, domain neutrality, transport neutrality, storage neutrality, stable lifecycle identity, and future physical separation. UUIDv7 ordering does not replace `created_at`; `created_at` remains the authoritative creation timestamp. Legacy IDs are bridged through explicit mappings and are not forcibly rewritten by this checkpoint.

## Birth date, age, and profile data

`birth_date` is a restricted CorePerson fact. It has ecosystem value beyond Food, but domain access is purpose-limited and authorized. Age and `age_months` are derived at an evaluation date. Exact DOB must never be manufactured from approximate age. If exact DOB is unknown, a dated declared-age assertion may exist with precision and provenance.

Onboarding is an input workflow, not a source-of-truth model. Canonical knowledge states preserve distinctions such as `UNKNOWN`, `NOT_PROVIDED`, `KNOWN_NONE`, and `KNOWN_PRESENT`.

## Relationships and permissions

PersonRelationship, Membership, and PermissionGrant are separate. A relationship such as `parent_of` or `guardian_of` does not automatically grant access to every future sensitive domain. Sensitive permissions require scoped authorization and may later require stronger verification.

## Important dates and structured memory

D17 accepts ImportantDate/PersonalEvent as a Core contract now and implementation later. Birth date remains a first-class CorePerson fact and is not generalized away into a generic event.

ImportantDate/PersonalEvent may later support celebration menus, planner reminders, optional Money budgeting flows, and other authorized domains. AI may propose structured memory from conversation, but persistent cross-domain promotion requires ownership, visibility, consent/confirmation where applicable, purpose limitation, and domain permissions.
