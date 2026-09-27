# Schema and migration

- Previous head: `20260927_0011`
- Wave 1 head: `20260927_0012`
- New tables: exactly 3.
- PostgreSQL constraint namespace collision was found during rehearsal and corrected by naming the new consumption constraint `uq_entitlement_consumptions_grant_idempotency`.
- Entitlement grants enforce exactly one account/household/person subject, valid intervals, status, and nonnegative limits.
- Consumption enforces nonnegative amount and `(grant_id, idempotency_key)` uniqueness.
