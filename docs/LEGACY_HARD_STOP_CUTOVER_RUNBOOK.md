# Legacy hard-stop cutover bridge (OD-18)

This procedure is for a future operator-approved production window. It does not
deploy V2 or change the legacy database schema. The bridge SHA must be checked
against the separately approved release before any server action.

## Legacy topology and provider inventory

Production compose runs `api`, `web`, `postgres`, `redis`, `nginx`, and
`certbot`. `api` starts two Uvicorn workers. Each worker starts the scheduler
and Telegram setup from the FastAPI lifespan; scheduler locking is in the API.
Webhook and callback handling, and FastAPI BackgroundTasks, also run in API.
There is no separate PLANAM worker service in this compose definition.

## Read-only production topology verification (2026-09-28)

The PLANAM VPS was inspected without changing production state. Production
remained on legacy SHA `1348799afc3d1d76dd7a72a13efc2a49a03c5210`.
`docker compose config --services` listed only `postgres`, `redis`, `api`,
`certbot`, `web`, and `nginx`. `docker top` showed one Uvicorn parent and two
worker processes in the API container. There is no separate PLANAM scheduler
or worker container; the scheduler and background tasks run in the API.

Telegram's read-only `getWebhookInfo` reported
`https://tg-relay.planam.ru/api/telegram/webhook`. The relay Caddy config
matches POST on that path and reverse-proxies to `https://planam.ru` with the
path unchanged. The production PLANAM Nginx HTTPS server's `/api/` location
then strips `/api` and proxies to the API container. The bridge's maintenance
check is in that location, as well as the PLANAM frontend and HTTP redirect
locations. The relay's Dengi webhook has a separate path and upstream; Dengi
and Avito have separate Nginx server blocks. Do not modify the relay.

The PLANAM API and web containers expose only Docker-internal ports. Host
listeners showed public ports 80/443 for Nginx, but no public 8000 or 3000
listener; direct external connection attempts to those ports timed out.
The only PLANAM PostgreSQL application client address observed mapped to the
API container on the PLANAM Docker network. The API's Redis hostname was
`redis`; that shared Redis container answered `PONG` and is not published.

Root and spool crontabs, systemd service/timer listings, cron directories,
host process listings, and active Docker services revealed no host-native
PLANAM writer or provider-capable process outside the API container. Recheck
these inventories immediately before the cutover; this is a point-in-time
observation. Avito `/health` and Dengi `/health` both returned 200 through
their local Nginx routes. `nginx -t` succeeded with deprecation warnings only.

The guarded external call sites are Telegram `sendMessage` (three modules),
`answerCallbackQuery` (two), bot setup (one), Telegram file download (two),
and OpenAI chat/transcription/vision (four). OCR uses the OpenAI vision path.
Legacy subscription routes grant entitlements and debit in-app Ams; no payment
capture or refund provider call was found in active API source. Verify that
no separately scheduled financial operation exists before the production window.

## Local verification

From the legacy bridge worktree:

```text
cd apps/api
python -m pytest -q
python -m scripts.legacy_cutover_control status
cd ../..
docker compose -f docker-compose.prod.yml config --quiet
```

Set `LEGACY_OUTBOUND_GUARD_ENABLED=true` for production parity. The bridge
defaults to normal delivery while Redis is reachable and the flag is absent.
If the flag cannot be read with the guard enabled, providers fail closed.
The operator CLI reads/writes only the namespaced Redis key; it has no HTTP
route. Restrict shell access to operators.

## Future production deployment

1. Verify production is the approved legacy base and has no tracked drift.
   Capture the current SHA, compose definition, image IDs and PLANAM config
   without printing secrets. Back up deployment-sensitive files.
2. Publish and materialize the exact approved bridge SHA. Build/recreate only
   the PLANAM API and required PLANAM Nginx configuration; test shared Nginx
   configuration before reload. Do not alter Dengi, Avito or the relay.
3. Confirm `docker compose -f docker-compose.prod.yml exec -T api python -m
   scripts.legacy_cutover_control status` reports `outbound_frozen: false` and
   `redis_reachable: true`. Verify ordinary PLANAM behavior.
4. Verify Avito's `avito_automation_prod-api-1` healthcheck and GET
   `https://avito.planam.ru/health`. Verify Dengi with GET
   `https://dengi.planam.ru/health`. Both must remain healthy.

## Begin cutover (PLANAM only)

1. Confirm API has no public `ports` mapping with `docker compose -f
   docker-compose.prod.yml config` and `docker port ai-food-family-api-1`.
   Inventory host cron/systemd timers, Docker jobs and direct internal clients
   capable of writing PLANAM. Stop or isolate any such writer before proceeding.
2. From `/var/www/ai-food-family`, create the flag in the existing template
   bind mount: `touch deploy/nginx/templates/planam-maintenance.enabled`.
   Verify `curl -i https://planam.ru/`, `curl -i
   https://planam.ru/api/health/live`, and a controlled POST to the registered
   `https://tg-relay.planam.ru/api/telegram/webhook` path each return 503.
   Verify Dengi, Avito and Nginx remain healthy.
   The ACME challenge path is exempt only for certificate renewal.
3. Run `docker compose -f docker-compose.prod.yml exec -T api python -m
   scripts.legacy_cutover_control outbound-freeze on`, then `status`. The
   output must report `outbound_frozen: true`, `redis_reachable: true`.
4. Run `docker compose -f docker-compose.prod.yml stop api`. Confirm the API
   container is stopped, no PLANAM Uvicorn/Python child process remains, and
   no separate scheduler/cron/background writer targets the legacy DB.
5. Inspect `pg_stat_activity` on the legacy PostgreSQL container using the
   operator's existing DB credentials. Exclude the inspection session and
   require zero application sessions. Observe DB write counters over a bounded
   interval and require no change. Only then record hard quiescence and take
   a restricted backup and immutable source snapshot.

Nginx's PLANAM server blocks both browser and `/api/` traffic, including the
Telegram webhook forwarded by relay to `planam.ru/api/telegram/webhook`.
Confirm the registered webhook URL and relay route again at preflight. A webhook routed
around PLANAM Nginx or a directly published API port is a stop condition.

## Rollback before V2 writes

Keep the Redis freeze key ON. Restore the exact legacy bridge runtime and
configuration, start the PLANAM API, and verify core reads/writes while the
maintenance flag remains present. Once safe, remove only
`deploy/nginx/templates/planam-maintenance.enabled` and recheck PLANAM,
Dengi, Avito and Nginx. Do not unfreeze providers automatically. A provider
request interrupted by API termination may have an unknown remote outcome;
reconcile notifications before an operator explicitly runs
`python -m scripts.legacy_cutover_control outbound-freeze off` in the API.
