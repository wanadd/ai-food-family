# 17 Decision Log

These are durable decisions captured from the repository source documents and current implementation checkpoint.

| ID | Decision | Consequence |
| --- | --- | --- |
| ADR-001 | Custom SQL is authoritative for the physical evidence schema; Alembic does not own these tables. | Bootstrap ordering and metadata boundaries must be explicit. |
| ADR-002 | `age_months` is the canonical age-sensitive representation. | Derivations are deterministic and source values are preserved. |
| ADR-003 | Evidence facts retain source authority and provenance. | Unsupported synthesis cannot become authoritative. |
| ADR-004 | `UNKNOWN` is distinct from `SAFE`. | Missing evidence escalates or remains unknown. |
| ADR-005 | FoodIdentity is separate from source observations. | Matching and evidence ingestion remain auditable. |
| ADR-006 | Nutrient facts require authoritative nutrient provenance. | Recipe values cannot silently replace source facts. |
| ADR-007 | Protein does not imply phenylalanine. | PKU computation requires its own evidence. |
| ADR-008 | Allergen and celiac facts are structured. | A single free-text dietary label is insufficient. |
| ADR-009 | Family safety is evaluated per person before aggregation. | Strict precedence and explicit participation are preserved. |
| ADR-010 | Gold V3 recipes are original, validated, structured production objects. | Source signals guide generation but are not user-facing recipes. |
| ADR-011 | Recipe images use one master and derived variants. | Crop failures require review, not a second master. |
| ADR-012 | Legacy recipe cleanup is a separate clean-slate direction, not an automatic migration. | No reset or deletion without authorization. |
| ADR-013 | Schema bootstrap ordering precedes ORM adoption and backfill. | Current technical stage is `P0-SCHEMA-BOOTSTRAP-ORDER-01`. |

