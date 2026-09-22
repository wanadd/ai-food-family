# Roadmap

1. Accept target architecture and Core contracts: complete.
2. Accept target physical V2 schema and module ownership blueprint: complete when `P0_PHYSICAL_V2_DESIGN_ACCEPTANCE_01_PASS` is recorded.
3. Specify implementation Wave 1: migration authority foundation, UUIDv7 helper, reference data, and PostgreSQL test harness.
4. Implement waves one at a time only after explicit wave-scoped authorization.
5. Apply the RI-2 physical gate before any NutritionTarget backfill.
6. Validate controlled cutover, rollback, observability, and safety invariants.
7. Deprecate compatibility readers only after parity, telemetry, archive fallback, retention, and owner acceptance.

P1 portability work includes retailer and money. P2 work includes shared conversation and a physical Core service. These priorities do not change the current implementation block.
