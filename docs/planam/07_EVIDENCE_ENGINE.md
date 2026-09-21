# 07 Evidence Engine

## Purpose

The evidence engine makes food facts computable without pretending that incomplete data is complete. It links a canonical food identity to authoritative sources, normalized facts, provenance, and downstream recipe/menu use.

## Evidence lifecycle

1. Match input to a FoodIdentity with explicit match confidence.
2. Resolve source authority and capture provenance.
3. Normalize units and retain the original value.
4. Store structured facts by domain.
5. Evaluate person policy and process state.
6. Expose result, confidence, and reason to menu and UX layers.

## Authority hierarchy

Source authority is domain-specific. Nutrient facts, allergens/celiac facts, pregnancy process-state facts, and PKU facts must each identify their own authoritative source and version. A general recipe or an LLM output cannot silently substitute for a missing safety fact.

## Non-computable cases

If identity, quantity, process state, person scope, or source evidence is missing, the engine returns an explicit unknown or escalation state. It does not infer phenylalanine from protein, infer safety from absence of an allergen label, or treat an unknown participation/portion as zero.

## Auditability

Every decision should be explainable through identity, source, fact, transformation, policy, and final state. The engine is composed with existing P0-A through P0-E services; a parallel safety engine is prohibited.

