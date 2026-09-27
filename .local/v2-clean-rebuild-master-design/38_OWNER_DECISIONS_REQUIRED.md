# Owner Decisions - Resolved Baseline

All decisions below are accepted for the final architecture freeze. No owner decisions remain unresolved. Commercial numeric limits remain runtime/product configuration, not architecture blockers.

| Decision | Status | Applied consequence |
|---|---|---|
| OD-01 CLEAN_V2_DB_SELECTIVE_IMPORT | ACCEPTED | New clean V2 DB; verified backup, extract/transform/validate/import/reconcile; old DB retained through stabilization. |
| OD-02 NAMESPACED_ENTITLEMENTS | ACCEPTED | Commercial plan -> policy/config -> effective capability/limit; no scattered plan checks. |
| OD-03 SEMANTIC_TABLE_COUNT | ACCEPTED | No artificial table cap; final catalog count is semantic and justified. |
| OD-04 STRICT_AMBIGUOUS_SAFETY_IMPORT | ACCEPTED | Ambiguity is ARCHIVE_ONLY/UNKNOWN/RECONFIRM_REQUIRED; never deterministic safety. |
| OD-05 MEASURED_RECOVERY_THRESHOLDS | ACCEPTED | Wave 12 thresholds measured during rehearsals with approved margins; no invented numbers. |
| OD-06 LEAST_PRIVILEGE_ADMIN | ACCEPTED | Sensitive support/admin access is explicit, purpose-bound, masked and audited. |
| OD-07 V2_PRODUCT_UX_BASELINE | ACCEPTED | `PLANAM V2 UX/PRODUCT BASELINE v1.0` frozen. |
| OD-08 MULTI_CLIENT_PRODUCT | ACCEPTED | Telegram, MAX, Web, Android and iOS are first-class clients of one product. |
| OD-09 CANONICAL_ACCOUNT_EXTERNAL_IDENTITY | ACCEPTED | Account/CorePerson/ExternalIdentity/VerifiedContact/Session are separate. Provider IDs are not Account IDs. |
| OD-10 PLATFORM_ADAPTER_BOUNDARY | ACCEPTED | Platform capabilities are behind small adapters; SDKs do not leak into business UI/domain. |
| OD-11 API_FIRST_APPLICATION_CONTRACT | ACCEPTED | One canonical `/api/v2` Application API; provider-specific bootstrap is edge-only. |
| OD-12 CLIENT_NEUTRAL_DATA_MODEL | ACCEPTED | One business state and provider-neutral canonical tables. |
| OD-13 PROVIDER_NEUTRAL_NOTIFICATIONS | ACCEPTED | NotificationIntent -> outbox/job -> routing -> provider delivery result. |
| OD-14 CANONICAL_MEDIA_ASSETS | ACCEPTED | MediaAsset is canonical; Telegram/MAX file IDs are metadata only. |
| OD-15 PERSON_OR_HOUSEHOLD_SCOPED_PLANNING | ACCEPTED | A Plan is exactly Person-owned or Household-owned; `XOR(person_id, household_id)` is required; personal mode has no implicit household; both scopes use the same client-neutral planning contract. |

Additional accepted flags:

- `MOBILE_FULLSCREEN_FIRST = ACCEPTED`
- `TELEGRAM_FIRST_IMPLEMENTED_CLIENT = YES`
- `TELEGRAM_CANONICAL_CLIENT = NO`
- `TELEGRAM_PRIVILEGED_CLIENT = NO`
- `TELEGRAM_PERMANENT_PRIMARY_CLIENT = NO`
- `MAX_FUTURE_FIRST_CLASS_CLIENT = YES`
- `ANDROID_FUTURE_FIRST_CLASS_CLIENT = YES`
- `IOS_FUTURE_FIRST_CLASS_CLIENT = YES`

`OWNER_DECISIONS_UNRESOLVED = 0`; `NEW_OWNER_DECISIONS = 0`.

OD-15 rationale: personal mode without family setup, clean CorePerson/Household separation, dependent-person support, client-neutral architecture and least-privilege authorization. A Person Plan uses the owning Person's FoodProfile and safety decision; a Household Plan uses participating Persons and conservative household aggregation. OD-01..OD-14 remain accepted and are not reopened.
