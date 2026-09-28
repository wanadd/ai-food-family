# PLANAM V2 Production Replacement Runbook

This is a future runbook. No `[СЕРВЕР / VPS]` command in this document was
executed during W11.

## Preconditions

Required before maintenance:

- owner-approved checkpoint SHA;
- W11 GO, including visual QA and representative import;
- clean V2 target and Alembic head `20260927_0019`;
- verified disk, DB connectivity, backup destination, and rollback operator;
- Telegram/provider checks that do not send a real notification;
- shared ingress health confirmed for PLANAM, `dengi.planam.ru`, and Avito.

## Local rehearsal

```text
[ЛОКАЛЬНО]
git rev-parse HEAD
python -m pytest -q
cd apps/web
npm test
npm run typecheck
npm run build
```

Use a fresh disposable PostgreSQL database, run `alembic upgrade 20260927_0019`,
run selective-import dry-run, review classifications, apply once, repeat for
idempotency, then destroy and recreate the target for determinism.

## Future server sequence

```text
[СЕРВЕР / VPS]
# 1. Confirm maintenance and write pause are active.
# 2. Inventory the immutable legacy source read-only.
# 3. Create a timestamped restricted backup and verify its SHA-256.
# 4. Create the clean V2 target database.
# 5. Run migrations to 20260927_0019.
# 6. Run selective-import dry-run; stop on fatal conflicts or production guard failure.
# 7. Review source counts, classifications, reconfirmations, archive/drop counts, and mappings.
# 8. Run the approved import once.
# 9. Run post-import integrity, safety, admin, analytics, and notification validations.
# 10. Run smoke checks before opening writes.
# 11. Open writes only after owner approval.
```

The legacy database remains immutable. Do not replay legacy notification jobs,
admin sessions, bearer tokens, cooking-as-consumption state, or ambiguous safety
facts. Do not infer dates, allergies, portions, participants, or pantry stock.

## Maintenance write boundary

Keep maintenance/write pause enabled through migration, import, validation, and
smoke. Open writes only after the new target is accepted. This prevents new V2
writes from diverging from the immutable legacy rollback source.

## Rollback

```text
[СЕРВЕР / VPS]
# 1. Keep maintenance enabled.
# 2. Stop the failed V2 runtime without mutating the legacy source.
# 3. Restore the previously approved PLANAM runtime/configuration.
# 4. Reconnect the immutable legacy runtime/database.
# 5. Verify PLANAM, dengi, Avito, and read-only health checks.
# 6. Keep writes paused until the owner accepts recovery.
# 7. Release maintenance only after recovery validation.
```

After V2 writes are opened, rollback requires an explicit owner decision because
those writes do not exist in the immutable legacy source. Do not blindly restore
a pre-cutover dump over a database that has accepted V2 writes.

## Smoke checklist

Home, Plan, Recipe, Shopping, Pantry, Events, Wellness, Account, Admin,
provider-neutral invitation, browser fallback, database health, durable job
health, and Telegram WebApp authentication must be checked without changing the
relay or sending a production message.

`TELEGRAM_RELAY_MUTATION=NO`, `DENGI_MUTATION=0`, and `AVITO_MUTATION=0`.
