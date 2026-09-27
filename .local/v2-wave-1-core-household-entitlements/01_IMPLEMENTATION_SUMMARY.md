# Implementation summary

Wave 1 establishes household scope, explicit dependent permissions, effective entitlements, and bounded V2 API/frontend behavior.

New persistence tables: `entitlement_plans`, `entitlement_grants`, `entitlement_consumptions`.
Modified core tables: `core_persons`, `core_households`, `core_memberships` for mutation idempotency and provenance.

No Wave 2+ domains, production import, backfill, provider adapter, MAX, Android, or iOS work was added.
