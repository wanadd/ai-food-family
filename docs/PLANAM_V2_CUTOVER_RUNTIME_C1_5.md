# PLANAM V2 Cutover Runtime C1.5

This runtime is production-capable but this implementation run never connects to or mutates production. C2 remains a separate explicitly authorized operation.

## Local/disposable setup

Set `DATABASE_URL` to a disposable PostgreSQL database and run from `apps/api`:

```powershell
python -m app.cutover.cli runtime-preflight --environment DISPOSABLE --database-url $env:DATABASE_URL --database-identity disposable --expected-database-identity disposable --run-id demo
python -m app.cutover.cli runtime-status --environment DISPOSABLE --database-url $env:DATABASE_URL --database-identity disposable --expected-database-identity disposable --run-id demo
```

The runtime creates persistent state, transition, lock, authority, control, audit, and backfill mapping tables. `runtime-preflight` is read-only; state-changing commands are explicit.

## Operator sequence for a future C2

1. Verify environment/database identity and approved backup reference.
2. Create a run and record the preflight approval.
3. Acquire the DB-backed cutover lock.
4. Pause writes and freeze/drain jobs and outbox.
5. Run `AlembicMigrationOrchestrator.plan`, then execute only with the production guard, token, GO state, backup reference, and lock.
6. Run DB-backed backfill dry-run, inspect accounting, then execute bounded batches with stable mappings and checkpoints.
7. Reconcile real legacy/V2 tables; require zero unexplained loss and zero P0 conflicts.
8. Run DB-backed shadow comparisons, then switch readers and writers domain by domain.
9. Smoke test, reopen writes, observe, and reconcile again.

There is no all-in-one command. Production tokens are supplied through the operator environment and are never persisted or logged.
