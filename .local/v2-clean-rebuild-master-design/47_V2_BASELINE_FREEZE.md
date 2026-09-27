# PLANAM V2 UX/Product Baseline v1.0

Status: FROZEN architecture baseline after OD-01..OD-14 acceptance, amended by OD-15 on 2026-09-27.

AMENDMENT = OD-15 PERSON_OR_HOUSEHOLD_SCOPED_PLANNING
AMENDMENT_DATE = 2026-09-27
AMENDMENT_REASON = resolve personal-vs-household Planning scope contradiction
PERSONAL_PLAN_SCOPE = PERSON
HOUSEHOLD_PLAN_SCOPE = HOUSEHOLD
PLAN_OWNER_XOR = REQUIRED
IMPLICIT_PERSONAL_HOUSEHOLD = NO
PERSON_MODE_WITHOUT_HOUSEHOLD = YES

- `MULTI_CLIENT_CORE`: YES
- `TELEGRAM_FIRST_IMPLEMENTED_CLIENT`: YES
- `MOBILE_FULLSCREEN_FIRST`: YES
- `MAX_FIRST_CLASS_FUTURE_CLIENT`: YES
- `ANDROID_FIRST_CLASS_FUTURE_CLIENT`: YES
- `IOS_FIRST_CLASS_FUTURE_CLIENT`: YES
- `ONE_CANONICAL_ACCOUNT`: YES
- `EXTERNAL_IDENTITY_MODEL`: READY
- `CLIENT_NEUTRAL_BUSINESS_DATA`: YES
- `API_FIRST`: YES
- `PROVIDER_NEUTRAL_NOTIFICATIONS`: YES
- `CANONICAL_MEDIA_ASSETS`: YES
- `CLEAN_V2_DB`: YES
- `SELECTIVE_IMPORT`: YES
- `LEAST_PRIVILEGE`: YES
- `FOOD_SAFETY_FAIL_CLOSED`: YES

PLANAM is a multi-client architecture with Telegram as the first implemented client. Telegram is not canonical, privileged or permanently primary. "Future client ready" means architectural compatibility, not implemented integration. Later MAX/Android/iOS work normally adds provider authentication, platform adapter, delivery/payment adapter and shell/UI integration without rewriting business domains.

Changes after this freeze require a new versioned product/architecture decision. Normal UX improvements remain possible when they preserve these invariants.
