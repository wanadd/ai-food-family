# PLANAM 2026 — Beta Hardening Report

**Дата:** 2026-06-03  
**Ветка:** `sprint-0/planam-2026-foundation`  
**Scope:** Track B (P0-3, P0-4, P0-5) + Track C (page-level legacy redirects)

**Ограничения соблюдены:** новые функции не добавлялись, UI не менялся, схема БД не менялась (владелец черновика — `source_url` + `source_type=draft`).

---

## 1. Закрытые риски

| ID | Риск | Что сделано | Проверка |
|----|------|-------------|----------|
| **P0-3** | Подделка Telegram webhook при пустом secret | В non-development при пустом `TELEGRAM_WEBHOOK_SECRET` → **503**; при заданном secret — обязателен заголовок `X-Telegram-Bot-Api-Secret-Token`, иначе **403** | `tests/test_telegram_webhook_security.py` |
| **P0-4** | Утечка webhook URL через debug GET | Удалены `GET /telegram/webhook/info` и `GET /telegram/webhook/url` | Тест: маршруты отсутствуют в router |
| **P0-5** | Global write в каталог рецептов | `POST /recipes`: не-admin только `source_type=draft`; черновики `is_active=false`, owner в `source_url`; `PATCH`: admin или свой draft; публикация (`is_active`) — только admin | `tests/test_recipe_write_access.py` |
| **Track C** | Legacy `/menu`, `/shopping` при `UI_2026` без middleware | Page-level `redirect()` на `/plan/*`, `/home/shopping`, `/home/pantry` | Ручной smoke с `NEXT_PUBLIC_PLANAM_UI_2026=true` |

### Изменённые файлы (Track B + C)

**API**

- `apps/api/app/routers/telegram_bot.py`
- `apps/api/app/routers/recipes.py`
- `apps/api/app/services/recipes/authoring.py`
- `apps/api/app/services/recipes/access.py` *(новый)*

**Web**

- `apps/web/app/menu/page.tsx`
- `apps/web/app/shopping/page.tsx`
- `apps/web/app/shopping/pantry/page.tsx`

*(Уже были redirects: `menu/current`, `menu/generate`.)*

**Ops / env**

- `.env.production.example` — `TELEGRAM_WEBHOOK_SECRET`

### Добавленные тесты

- `apps/api/tests/test_telegram_webhook_security.py` (4 кейса)
- `apps/api/tests/test_recipe_write_access.py` (5 кейсов)

---

## 2. Оставшиеся риски

| ID | Статус | Влияние на закрытую бета |
|----|--------|---------------------------|
| **P0-1** | Частично (admin session + AppGate) | Owner-админка; не блокер для 10–50 тестеров при известном flow |
| **P0-2** | Open | Диагностика initData (dev) |
| **P0-6** | Open | `ADMIN_PIN` на prod — ops checklist |
| **P0-7** | Open | `TELEGRAM_WEBAPP_URL` / BotFather domain |
| **P1-*** | Open | IDOR checkins, CORS, HSTS, rate limits |
| **P2-4** | Open | Полная модель `user_recipe_drafts` + promote; сейчас draft через `source_type` + `source_url` |
| **Catalog** | Существующие `manual`/`import` в БД | Не затронуты; новые user-write в каталог закрыты |
| **Middleware** | `ROUTE_REDIRECTS` опционален | При `UI_2026=true` ключевые legacy URL редиректятся на уровне page |

---

## 3. Готовность к закрытой бете

**Вердикт: GO WITH CONDITIONS** (согласуется с [`BETA_READINESS_AUDIT.md`](BETA_READINESS_AUDIT.md), security score улучшен после Track B/C).

### Обязательный env на staging/prod

```env
NEXT_PUBLIC_PLANAM_UI_2026=true
NEXT_PUBLIC_PLANAM_DEFER_PHONE_GATE=true
ENVIRONMENT=production
TELEGRAM_WEBHOOK_SECRET=<strong-random>
ADMIN_PIN=<set>
TELEGRAM_WEBAPP_URL=https://<your-domain>
```

`NEXT_PUBLIC_PLANAM_ROUTE_REDIRECTS=true` — **рекомендуется**, но не обязателен для `/menu` и `/shopping` после Track C.

### Pre-launch checklist

1. Задать `TELEGRAM_WEBHOOK_SECRET` до включения prod traffic (иначе webhook **503**).
2. Убедиться, что nginx не проксирует удалённые debug paths (доп. слой).
3. Smoke: `/menu` → `/plan`, `/shopping` → `/home/shopping`, POST webhook с secret.
4. Состав тестеров: осознанный риск P0-6/P0-1 для админ-операций.
5. Не открывать публичный prod до P0-6 + payment hardening (Phase 2).

### Оценка готовности (после hardening)

| Область | До | После Track B/C |
|---------|-----|------------------|
| Security (webhook + catalog write) | 4 | **6** |
| UX legacy deep links | 6 | **7** |
| Closed beta (10–50 users) | Условно | **Да**, при checklist выше |

---

## 4. Deploy notes (P0-3)

После деплоя API с `ENVIRONMENT=production`:

1. Сгенерировать secret: `openssl rand -hex 32`
2. Прописать `TELEGRAM_WEBHOOK_SECRET` в `.env`
3. Перерегистрировать webhook (Bot API `setWebhook` с `secret_token`) — см. [`DEPLOY.md`](../DEPLOY.md)

Debug webhook URL больше не доступен через API; диагностика — через Bot API / логи контейнера.
