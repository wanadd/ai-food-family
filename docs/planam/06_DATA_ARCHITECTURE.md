# Data Architecture

Core owns Account, Person, Household, Membership, relationship, permissions, consent, and restricted profile identity. Food owns FoodProfile and typed evidence-backed food facts. Recipe, planning, cooking, consumption, shopping, pantry, health, AI, notifications, and integrations have separate ownership contracts.

Every safety-relevant fact preserves person scope, provenance, time validity, and uncertainty. Missing, unknown, declined, and not-applicable are not numeric zero or safe. Person-first resolution precedes aggregation. The physical schema checkpoint is historical evidence: 60/60 physical tables, with RI-2 `BLOCKING_BEFORE_BACKFILL`.

Wave 02 implements Core identity roots and `legacy_id_mappings` under V2 versioned migrations. FoodProfile and safety/health facts remain Food-owned and are not migrated into Core.
