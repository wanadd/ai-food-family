# Roadmap

1. Accept target architecture and Core contracts: complete.
2. Accept target physical V2 schema and module ownership blueprint: complete when `P0_PHYSICAL_V2_DESIGN_ACCEPTANCE_01_PASS` is recorded.
3. Specify implementation Wave 1: complete.
4. Implement Wave 1 migration authority foundation, UUIDv7 helper, reference data, and PostgreSQL test harness: complete pending checkpoint acceptance.
5. Implement Wave 2 Core roots and legacy user/family/member idempotent mapping: complete pending checkpoint acceptance.
6. Specify and implement Wave 3 FoodProfile only after explicit wave-scoped authorization.
7. Apply and preserve the RI-2 physical gate before any NutritionTarget backfill: complete in Run A Wave 5.
8. Maintain additive Recipe V2 and Planning V2 compatibility checkpoints; Wave 8+ requires a separate specification and gate.
9. Validate controlled cutover, rollback, observability, and safety invariants.
9. Deprecate compatibility readers only after parity, telemetry, archive fallback, retention, and owner acceptance.

P1 portability work includes retailer and money. P2 work includes shared conversation and a physical Core service. These priorities do not change the current implementation block.
