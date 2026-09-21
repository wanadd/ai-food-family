# 06 Data Architecture

## Canonical entities

The food evidence foundation separates FoodIdentity from source observations, provenance, normalized units, nutrition facts, allergen and celiac facts, pregnancy process-state facts, PKU/phenylalanine facts, recipe-derived provenance, cooking/consumption linkage, and actual process state.

## Identity and provenance

Food identity is the stable canonical subject. A source observation is not a canonical food. Every material fact must retain source authority, source reference, extraction/normalization details, version, confidence, and explicit unknown state where applicable.

## Authority rules

- Custom SQL owns the physical evidence schema.
- ORM mappings are additive and must respect existing metadata ownership.
- Age in months is canonical for age-sensitive rules; derivations must be deterministic.
- Recipe-derived values never masquerade as authoritative source facts.
- Backfill is a separate authorized operation, not an automatic migration side effect.

## Safety representation

Use explicit states for `SAFE`, `WARN`, `ESCALATE`, `BLOCK`, and `UNKNOWN`. `UNKNOWN` is not a default safe value. Null, absent, or uncomputable values remain distinguishable from measured zero.

## Current physical checkpoint

M1-M4 physical evidence schema acceptance is 60/60 and committed in `a75b372`. ORM adoption is blocked by a metadata conflict; schema authority/bootstrap ordering is blocked by dependency order. Details are in [`18_CURRENT_STATE.md`](18_CURRENT_STATE.md).

