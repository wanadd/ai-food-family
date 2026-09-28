# PLANAM V2 Wave 11 Release Readiness

Status: `NO-GO` as of 2026-09-28.

## Baseline

- Branch: `main`
- W10 checkpoint: `9840e072a7524c376b51af4d4cdaadb759789459`
- Alembic head: `20260927_0019`
- Backend: `1395 passed, 3 skipped, 3 warnings`
- Frontend: `220 passed`
- Frontend lint, typecheck, and production build: `PASS`

## Gates

| Gate | Result | Evidence |
| --- | --- | --- |
| PostgreSQL migration acceptance | PASS | `tests/test_v2_postgresql_migration_acceptance.py`, 2 passed |
| Concurrent startup | PASS | `tests/test_concurrent_init_db_postgres.py`, 1 passed; 2/2, repeat 2/2, 4/4 workers |
| Full backend | PASS | 1395 passed, 3 skipped, 3 warnings |
| Full frontend | PASS | 33 files, 220 tests passed |
| Lint/typecheck/build | PASS | local commands completed successfully |
| W10 selective import fixture | PASS | 16 source records, 11 created, 4 reconfirmations, 0 fatal conflicts |
| Browser visual QA | PASS | Playwright Chromium launch, 120 screenshots across 12 personas, light/dark/desktop spot checks; `valid=true`, 0 auth/network/blank/route/forbidden findings |
| Representative import | BLOCKED | only 16-record fixture is safe and available; no approved representative source copy |

## W11.1 blocker closure evidence

Previous result: `PLANAM_P0_V2_WAVE_11_FULL_ACCEPTANCE_NO_GO` with B01 and B02
open.

### W11-B01: CLOSED

- Playwright package: `PASS`.
- Chromium launch: `PASS` using the existing local Playwright cache.
- Local Next app access: `PASS` on the supported `next dev` audit path.
- Audit walkthrough: `PASS`; `valid=true`, 120 screenshots, 12 personas,
  `network_failed=0`, `blank=0`, `route_assert=0`, `auth=0`, and
  `forbidden=0`.
- Visual spot checks: light mobile, dark mobile, and desktop home; Events and
  Wellness representative screens; Russian text, navigation, cards, safe-area
  bottom navigation, and dark contrast were visually inspected.
- Responsive capture: small mobile (`390x844`) and desktop (`1440x900`) were
  captured; browser-without-Telegram audit mode completed without Telegram SDK.
- Browser journey spot check: Home → Plan passed. The Events V2 client path was
  corrected to the canonical `/api/v2` prefix, and local audit requests now
  receive a fail-closed canonical V2 session bridge.
- Focused regression: Events V2, selective import, and PostgreSQL acceptance
  passed (`7 passed, 2 skipped`); frontend Events API tests passed (`2 passed`).
- Local evidence is retained under `.local/w11-visual-qa/`; bulk screenshots
  remain uncommitted.

### W11-B02: OPEN

Severity: `P1`, release blocker.

The approved 16-record W10 fixture is not representative. Existing dump-like
artifacts under `.local` remain production-shaped or potentially sensitive and
were not opened or used. No approved sanitized representative source is
available, so representative import apply, idempotency, recreate determinism,
referential integrity, and performance evidence remain unavailable.

Web `typecheck` and `lint` were attempted after the narrow B01 fix but the
local Node 24 process exhausted its heap before completion. The previous W11
baseline results remain unchanged; this environment limitation is recorded and
is not treated as a new product defect.

## W11 correction

Fresh concurrent startup exposed a metadata registration defect. `init_db()` now
registers canonical Recipe V2 metadata before dependent models are resolved,
and Wave 2 custom-SQL models map their ORM primary keys to the physical `id`
columns. No migration was added; PostgreSQL acceptance passed after the fix.

## Release blockers

### W11-B01: historical visual acceptance unavailable

Severity: `P1`, release blocker.

This was the state before W11.1 closure. The current closure evidence is recorded
above; this historical section is retained for auditability.

### W11-B02: representative import unavailable

Severity: `P1`, release blocker.

W10 evidence is fixture-only. Existing dump-like artifacts under `.local` are
production-shaped or potentially sensitive and were deliberately not opened or
used as an import source. No safe representative local source dataset was
available, so production-scale import duration, volume, and anomaly rates remain
unknown.

## Safety boundary

No production DB, old production DB, VPS, Telegram relay, webhook, shared ingress,
Dengi, Avito, DNS, or deployment was contacted or mutated. No production
notifications were sent. Existing dirty files unrelated to W11 were preserved.

## Decision

`PLANAM_P0_V2_WAVE_11_FULL_ACCEPTANCE_NO_GO`

Do not proceed to production replacement or cutover. Obtain an approved
representative sanitized source rehearsal before requesting GO.
