# PLANAM Local Prod-Parity Audit

This environment runs PLANAM locally against a restored production-like PostgreSQL snapshot. It is for manual QA of menu, shopping, pantry, leftovers, wellness, users, families, and subscriptions without touching production.

## Differences From Production

- Web: `http://localhost:3000`
- API: `http://localhost:8000`
- PostgreSQL: local Docker volume on host port `5433`
- Redis: isolated Docker volume
- Web uses the prod-like standalone Docker build with a small `apps/web` context.
- Telegram outbound is disabled.
- Care and notification schedulers are disabled.
- Auth uses local parity mode with `LOCAL_PARITY_TELEGRAM_ID`.
- No production volumes or production secrets are used.

## Export Snapshot On VPS

Run on the VPS:

```bash
cd /var/www/ai-food-family
bash backend/scripts/export_prod_db_for_local_parity.sh
```

The script writes a read-only `pg_dump --format=custom --no-owner --no-acl` snapshot to:

```text
/var/www/ai-food-family/backups/local-parity/planam_prod_snapshot_YYYYMMDD_HHMM.dump
```

## Download Snapshot

Run locally:

```powershell
scp root@<VPS>:/var/www/ai-food-family/backups/local-parity/planam_prod_snapshot_YYYYMMDD_HHMM.dump C:\Projects\ai-food-family\.local-parity\db\planam_prod_snapshot.dump
```

## Configure

```powershell
cd C:\Projects\ai-food-family
Copy-Item .env.local-parity.example .env.local-parity
```

Edit `.env.local-parity` and set:

```text
LOCAL_PARITY_TELEGRAM_ID=<existing telegram_id from the snapshot>
```

Do not commit `.env.local-parity`.

## Import

```powershell
.\scripts\local-parity\import-prod-snapshot.ps1 -DumpPath .\.local-parity\db\planam_prod_snapshot.dump
```

The script restores into the isolated local parity Postgres volume and prints:

- `recipes_total`
- `max_recipe_id`
- `users_count`
- `latest_menu_selection_count`
- `shopping_lists_count`

The import is fail-fast. It only prints `Local parity import complete.` after `pg_restore`, schema check, and hard validation pass:

- `recipes_total >= 250`
- `max_recipe_id >= 265`
- `users_count > 0`
- `family_menu_selection_count > 0`

## Start

```powershell
.\scripts\local-parity\start.ps1
```

Open:

```text
http://localhost:3000
```

Click `Local parity login` → `Войти как QA user`.

## Smoke

```powershell
.\scripts\local-parity\smoke.ps1
```

Expected final line:

```text
LOCAL PARITY SMOKE: PASS
```

Smoke also enforces prod-compatible DB counts and verifies local parity auth plus disabled Telegram/care/notification side effects.

## Stop And Logs

```powershell
.\scripts\local-parity\logs.ps1
.\scripts\local-parity\stop.ps1
```

## Manual Audit Checklist

1. Home opens.
2. `/plan/today` opens.
3. `/home/shopping` opens.
4. `/home/pantry` opens.
5. `/home/leftovers` opens.
6. `/wellness` opens.
7. Replace one dish locally.
8. Delete one dish locally.
9. Mark one dish eaten locally.
10. Confirm shopping updates locally.
11. Confirm wellness updates locally.
12. Confirm no Telegram messages are sent.
13. Confirm care pending/sending does not grow.

## Update Snapshot

Repeat export, `scp`, import, then run smoke. The local volume is safe to drop/recreate because it is not production.

## Never Commit

- `.env.local-parity`
- `.local-parity/`
- `*.dump`
- `*.backup`
- `*.sql`
- production secrets
- database backups
