# Household and membership results

- Personal mode without household: PASS.
- Household creation and replay with the same idempotency key: PASS.
- Multiple households per person and deterministic listing: PASS.
- Owner/admin member addition and person without Account: PASS.
- Cross-household membership is rejected by server-derived context: PASS.
- Application services flush/read only; route/application layer owns commit.
