# Security Fix Roadmap — ПланАм

**Дата:** 2026-06-03  
**Основа:** [`SECURITY_AUDIT.md`](SECURITY_AUDIT.md)  
**Принцип:** код не менялся при составлении roadmap; пункты ниже — **план работ**.

**Легенда риска продукта:** 🟢 низкий · 🟡 средний · 🔴 высокий

---

## Phase 0 — срочно до новых функций

Цель: закрыть **open issue админки**, критичные дыры в webhook и каталоге рецептов, ops-секреты.

| ID | Что исправить | Почему важно | Файлы / модули | Риск сломать продукт | Как проверить | Критерий готовности |
|----|---------------|--------------|----------------|----------------------|---------------|---------------------|
| **P0-1** | **Admin: `admin_session` + AppGate** — захват `?admin_session=` до `AppGate` или отдельный loading path для `/admin`; не терять token при `TelegramRequiredScreen` | PIN работает, панель недоступна — блокер операций | `AppProviders.tsx`, `AppGate.tsx`, новый `AdminSessionBootstrap.tsx` (или `app/admin/layout.tsx`), `AdminSessionCapture.tsx`, `TelegramProvider.tsx` | 🟡 UX/auth flow | Bot: `/admin` → PIN → кнопка → `/admin` открывается в Telegram; `sessionStorage.planam_admin_session` set; нет «Нужен Telegram» при валидном Mini App | Owner открывает админку с первого раза; `GET /admin/ping` 200 |
| **P0-2** | **Admin: диагностика `initData`** — логирование (dev-only) длины `initData`, platform, timing после `loadTelegramWebApp` | Отделить «нет Telegram» от «race SDK» | `telegram-webapp.ts`, `TelegramProvider.tsx` | 🟢 | DevTools / server logs on staging | Root cause задокументирован; retry срабатывает если race |
| **P0-3** | **Webhook: fail-closed** — если `ENVIRONMENT=production` и `TELEGRAM_WEBHOOK_SECRET` пуст → 503 или reject; иначе require header | Подделка Telegram updates | `routers/telegram_bot.py`, `config.py`, `.env.production.example` | 🟡 Legit webhook if secret not set yet | POST fake body without header → 403; with secret → 200 | Secret задан на prod; документирован deploy step |
| **P0-4** | **Удалить/закрыть debug webhook GET** | Утечка URL webhook | `telegram_bot.py` — `/webhook/info`, `/webhook/url` | 🟢 | Anonymous GET → 404/401 | Endpoints недоступны снаружи |
| **P0-5** | **Recipes: запрет global write** — `POST/PATCH /recipes` только admin или user-owned draft (`source_type`, `created_by`) | Integrity каталога + AI | `routers/recipes.py`, `services/recipes/authoring.py`, models | 🔴 если clients rely on user create | Verified user PATCH чужого recipe → 403; admin OK | Нет user-write в system catalog |
| **P0-6** | **Ops: `ADMIN_PIN` в prod** | PIN не доходит до API | `docker-compose.prod.yml`, `DEPLOY.md`, `.env.production.example` | 🟢 | Container env has `ADMIN_PIN`; `/admin` flow | PIN verify works in prod |
| **P0-7** | **Ops: `TELEGRAM_WEBAPP_URL=https://planam.ru`** + BotFather Web App domain | Wrong Mini App host | env, BotFather | 🟡 | WebApp button opens correct origin | Domain match checklist |

**Phase 0 exit criteria:** P0-1 + P0-3 + P0-5 + P0-6 done; admin panel usable by owner in Telegram.

---

## Phase 1 — до закрытого beta-теста

Цель: IDOR/scope fixes, базовая защита инфраструктуры, снижение XSS impact.

| ID | Что исправить | Почему важно | Файлы / модули | Риск | Проверка | Готово когда |
|----|---------------|--------------|----------------|------|----------|--------------|
| **P1-1** | **meal-checkins: `family_member_id` validation** | Cross-member write | `meal_attendance.py`, `meal_checkins.py` | 🟡 | POST with other family member id → 404 | Same pattern as `recipes.py` rate |
| **P1-2** | **meal-checkins: use `get_app_scope`** | Scope drift personal/family | `meal_checkins.py` | 🟡 | Toggle `X-App-Mode` → checkin lands in correct scope | Consistent with shopping/pantry |
| **P1-3** | **AppGate: no children until `mounted`/auth settled** | Flash unauthenticated UI | `TelegramProvider.tsx`, `AppGate.tsx` | 🟡 | Hard refresh — no flash of home before auth | Single loading state |
| **P1-4** | **Telegram SDK retry** — re-run `runAuth` on delayed `initData` | Slow clients | `telegram-webapp.ts`, `TelegramProvider.tsx` | 🟢 | Throttle network; auth succeeds | <1% false «Нужен Telegram» |
| **P1-5** | **Unit tests `validate_init_data`** | HMAC regressions | `tests/test_telegram_validate.py`, `validate.py` | 🟢 | CI green | valid/invalid/expired cases |
| **P1-6** | **Nginx HSTS + baseline headers** | MITM, sniffing | `deploy/nginx/templates/app-ssl.conf.template` | 🟡 | `curl -I` shows HSTS | HSTS on prod HTTPS |
| **P1-7** | **CORS tighten** — explicit methods/headers | Over-permissive CORS | `main.py`, env `BACKEND_CORS_ORIGINS` | 🟡 | Preflight from wrong origin fails | Only prod domain allowed |
| **P1-8** | **Backup hygiene** — не копировать raw `.env` в backup без encryption note | Secret leak on disk | `backup.py`, `scripts/backup.sh`, docs | 🟢 | Backup docs updated | Ops runbook |

**Phase 1 exit criteria:** P1-1, P1-2, P1-5, P1-6; beta testers cannot access other families' checkins.

---

## Phase 2 — до оплат

Цель: paywall completeness, AI hardening, session model improvements.

| ID | Что исправить | Почему важно | Файлы / модули | Риск | Проверка | Готово когда |
|----|---------------|--------------|----------------|------|----------|--------------|
| **P2-1** | **Paywall audit** — все PRO/AMS features call server `require_pro` / `assert_*` | Client-only gating bypass | `routers/*`, `subscription.py`, `progress.py`, `care.py`, `menus.py` | 🟡 | Free user direct API to PRO endpoints → 402/403 | Checklist 100% server enforced |
| **P2-2** | **AI output validation** — schema for menu JSON, recipe_id allowlist | Bad/malicious AI output | `menu_ai_parsing.py`, `ai.py` | 🟡 | Fuzz malformed JSON | No crash; reject invalid |
| **P2-3** | **Prompt injection mitigations** — length limits, strip control chars in user text fields | Manipulation of AI | `ai_context.py`, onboarding/profile schemas | 🟢 | Pen-test strings in profile | Documented limits |
| **P2-4** | **Recipe draft vs published** — user drafts not in `is_active` catalog until approve | AI-03 | models, `authoring.py`, admin promote | 🔴 data migration care | User recipe invisible in catalog until approve | Clear separation |
| **P2-5** | **Shorter initData TTL or server session** — post `/auth/telegram` issue session token | T-01 replay | `auth.py`, `deps.py`, web client | 🔴 auth architecture | Stolen old initData rejected after TTL | Design doc + implementation |
| **P2-6** | **Admin session hardening** — optional IP bind, rotate on use, shorter TTL | A-03 XSS | `admin_auth.py`, web `session.ts` | 🟡 | Steal token from other IP → fail (if enabled) | Threat model accepted |
| **P2-7** | **API rate limits** — per-IP / per-telegram_id on auth & AI | DoS, cost | `main.py` middleware or nginx | 🟡 | Load test 429 | Limits documented |

**Phase 2 exit criteria:** P2-1 complete; payment launch blocked without P2-1 + P2-5 decision.

---

## Phase 3 — перед масштабированием

Цель: defense in depth, referral-safe foundation, ops at scale.

| ID | Что исправить | Почему важно | Файлы / модули | Риск | Проверка | Готово когда |
|----|---------------|--------------|----------------|------|----------|--------------|
| **P3-1** | **CSP + Next security headers** | XSS (T-02) | `next.config.mjs`, nginx | 🔴 breakage if CSP too strict | Staging smoke all pages | CSP report-only → enforce |
| **P3-2** | **Redis AUTH** | INF-02 | `docker-compose.prod.yml`, redis config | 🟡 | Redis CLI without auth fails | Password in secret store |
| **P3-3** | **Global audit logging** — sensitive admin actions to SIEM | Insider threat | `admin_audit.py` | 🟢 | Export sample | Retention policy |
| **P3-4** | **Referral/partner design review** (before code) | REF-* fraud | new modules | 🟢 | Threat model doc | Signed off by owner |
| **P3-5** | **Implement referral with:** idempotent grants, anti-self-referral, phone gate, velocity limits | Future payout fraud | TBD | 🔴 | Test farm simulation | REF checklist in SECURITY_AUDIT §10 |
| **P3-6** | **Penetration test** — external | Pre-scale confidence | — | 🟢 | Report | Critical/high fixed |
| **P3-7** | **Dependency & container scanning** | Supply chain | CI | 🟢 | CI job | No critical CVEs unmitigated |

**Phase 3 exit criteria:** P3-1, P3-2, P3-6; referral feature only after P3-4.

---

## Mapping: Audit ID → Phase

| Audit ID | Phase | Priority |
|----------|-------|----------|
| A-01, F-01 (admin) | **P0-1, P0-2** | P0 |
| API-02, SEC-02 | **P0-3, P0-4** | P0 |
| API-01, AI-03 | **P0-5, P2-4** | P0 + P2 |
| SEC-01, A-02, P0-7 | **P0-6, P0-7** | P0 |
| API-04, API-05, FI-01 | **P1-1, P1-2** | P1 |
| F-02, F-03 | **P1-3, P1-4** | P1 |
| T-03 | **P1-5** | P1 |
| INF-03, API-07 | **P1-6, P1-7** | P1 |
| SUB-01 | **P2-1** | P2 |
| AI-01, AI-02 | **P2-2, P2-3** | P2 |
| T-01, T-02 | **P2-5, P3-1** | P2–P3 |
| INF-02, INF-04 | **P3-2, P2-7** | P2–P3 |
| REF-* | **P3-4, P3-5** | P3 (pre-feature) |

---

## Open Issue Tracker (Admin)

| Status | Item | Owner action |
|--------|------|--------------|
| **OPEN** | `/admin` → `TelegramRequiredScreen` | Execute **P0-1**; verify BotFather + `TELEGRAM_WEBAPP_URL` (**P0-7**) |
| mitigated | Bot button `url` vs `web_app` | Already `web_app` in `admin_bot.py` |
| mitigated | Relative admin URL | `admin_auth.admin_webapp_url` uses `https://planam.ru` fallback |

---

## Suggested execution order (2-week sketch)

```text
Week 1: P0-1 → P0-3 → P0-5 → P0-6 (deploy)
Week 2: P1-1 → P1-2 → P1-5 → P1-6
Before payments: P2-1 → P2-5 decision
Before 10k users: P3-1 → P3-2 → P3-6
```

---

## Definition of Done (program level)

1. **Zero high** findings open from Phase 0–1 list in production.
2. Admin panel: owner workflow documented in [`ADMIN_PANEL_INCIDENT_AUDIT.md`](ADMIN_PANEL_INCIDENT_AUDIT.md) + verified on prod Telegram.
3. Webhook secret mandatory on prod.
4. No verified-user write to system recipe catalog.
5. Security regression tests in CI (`validate_init_data` minimum).

---

*Roadmap синхронизирован с [`SECURITY_AUDIT.md`](SECURITY_AUDIT.md). Обновлять после каждого закрытого finding.*
