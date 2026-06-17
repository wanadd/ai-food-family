# PLANAM Audit Mode (local only)

Audit mode lets Cursor, Playwright, and developers run the full PLANAM UI **without Telegram Mini App initData**. It is **disabled in production** even if environment variables are set incorrectly.

## Safety rules

Audit mode is active only when **all** are true:

```text
environment=development          (backend)
NODE_ENV !== "production"      (frontend build/runtime)
PLANAM_AUDIT_MODE=true         (backend)
NEXT_PUBLIC_PLANAM_AUDIT_MODE=true (frontend)
```

Additionally:

- Only whitelisted persona slugs (`audit_*`) are accepted — no arbitrary `user_id`.
- Optional shared secret: `PLANAM_AUDIT_SECRET` / `NEXT_PUBLIC_PLANAM_AUDIT_SECRET`.
- Production Telegram auth is unchanged.
- Do not enable audit flags on VPS/production Docker.

## Enable locally

### Backend (`apps/api/.env` or shell)

```text
environment=development
PLANAM_AUDIT_MODE=true
PLANAM_AUDIT_SECRET=local-audit-secret
PLANAM_AUDIT_CORS_ORIGINS=http://localhost:3000,http://localhost:3001,http://localhost:3002,http://127.0.0.1:3000,http://127.0.0.1:3001,http://127.0.0.1:3002
```

When audit mode is active in development, these origins are merged into CORS automatically (never in production).

### Frontend (`apps/web/.env.local`)

```text
NEXT_PUBLIC_PLANAM_UI_2026=true
NEXT_PUBLIC_PLANAM_AUDIT_MODE=true
NEXT_PUBLIC_PLANAM_AUDIT_SECRET=local-audit-secret
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Restart `next dev` after changing `.env.local` — `NEXT_PUBLIC_*` values are baked into the client bundle at startup.

## Seed audit personas

```powershell
cd C:\Projects\ai-food-family
$env:PYTHONPATH="apps/api"
$env:PLANAM_AUDIT_MODE="true"
$env:environment="development"
python backend/scripts/seed_audit_personas.py
```

Creates users with `telegram_id` 900_000_001–900_000_013, pantry/consumption/family fixtures where applicable.

## Open a persona

### URL parameter

```text
http://localhost:3000/?auditPersona=audit_personal_day5
http://localhost:3000/plan/today?auditPersona=audit_family_admin
```

Stored in `localStorage` key `planam.audit.persona`.

### Dev panel

```text
http://localhost:3000/dev/audit
```

Only renders when `NEXT_PUBLIC_PLANAM_AUDIT_MODE=true` (404 otherwise).

## Run Playwright audit

```powershell
cd C:\Projects\ai-food-family\apps\web
npm run dev

# another terminal — API must be running with audit mode
$env:PLANAM_AUDIT_BASE_URL="http://localhost:3002"
node scripts/audit-walkthrough.mjs
```

The runner fails (exit code 1) if auth/CORS errors appear in the browser console. Check `reports/ux_audit/AUDIT_RUN_STATUS.md` for `valid: true/false`.

Output:

```text
reports/ux_audit/screenshots/audit_<persona>_<route>.png
reports/ux_audit/network/findings.json
reports/ux_audit/logs/console.json
reports/ux_audit/AUDIT_RUN_STATUS.md
```

## Personas

| Slug | Purpose |
|------|---------|
| `audit_new_user` | Empty / first run |
| `audit_personal_day5` | Returning user, pantry, marks |
| `audit_family_admin` | Family admin + prepared food |
| `audit_family_adult` | Ordinary member |
| `audit_athlete` | Sport / PRO plan |
| `audit_strict_diet` | Restrictions |
| `audit_healthy_eating` | Soft wellness segment |
| `audit_start_trial` … `audit_family_pro` | Tariff states |

## API headers (automatic in audit mode)

```text
X-Telegram-Init-Data: planam-audit-v1:<persona>
X-Planam-Audit-Persona: <persona>
X-Planam-Audit-User: <persona>
X-Planam-Audit-Secret: <secret if configured>
```

## Turn off

```text
PLANAM_AUDIT_MODE=false
NEXT_PUBLIC_PLANAM_AUDIT_MODE=false
```

Restart dev servers. `/dev/audit` returns 404.

## Forbidden in production

- `PLANAM_AUDIT_MODE=true`
- `NEXT_PUBLIC_PLANAM_AUDIT_MODE=true`
- Running `seed_audit_personas.py`

`is_audit_mode_enabled()` returns `False` when `environment != development`.
