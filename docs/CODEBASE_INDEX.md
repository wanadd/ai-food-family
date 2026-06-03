# CODEBASE INDEX

Предварительная индексация проекта **ai-food-family** (ПланАм).  
Сгенерировано: 2026-06-03. Только read-only обзор — код не изменялся.

## Обзор структуры

| Путь | Назначение |
|------|------------|
| `apps/web/` | Next.js 14 (App Router), Telegram Mini App UI |
| `apps/api/` | FastAPI backend, PostgreSQL, Redis |
| `backend/scripts/` | Python-скрипты обработки рецептов и nutrition |
| `scripts/` | Утилиты: seed, reset user, backup/restore |
| `deploy/` | nginx, certbot, production entrypoints |
| `docs/` | Документация проекта |

**Стек:** Next.js 14.2.5 · React 18 · FastAPI · PostgreSQL 16 · Redis 7 · Docker Compose

---

## Страницы (Next.js App Router)

47 страниц (`page.tsx`):

| Route | Файл |
|-------|------|
| `/` | `apps/web/app/page.tsx` |
| `/onboarding` | `apps/web/app/onboarding/page.tsx` |
| `/profile` | `apps/web/app/profile/page.tsx` |
| `/profile/nutrition` | `apps/web/app/profile/nutrition/page.tsx` |
| `/family` | `apps/web/app/family/page.tsx` |
| `/pantry` | `apps/web/app/pantry/page.tsx` |
| `/shopping` | `apps/web/app/shopping/page.tsx` |
| `/shopping/pantry` | `apps/web/app/shopping/pantry/page.tsx` |
| `/shopping/leftovers` | `apps/web/app/shopping/leftovers/page.tsx` |
| `/recipes` | `apps/web/app/recipes/page.tsx` |
| `/recipes/[id]` | `apps/web/app/recipes/[id]/page.tsx` |
| `/menu` | `apps/web/app/menu/page.tsx` |
| `/menu/current` | `apps/web/app/menu/current/page.tsx` |
| `/menu/generate` | `apps/web/app/menu/generate/page.tsx` |
| `/menu/recipes` | `apps/web/app/menu/recipes/page.tsx` |
| `/menu/collections` | `apps/web/app/menu/collections/page.tsx` |
| `/menu/collections/[id]` | `apps/web/app/menu/collections/[id]/page.tsx` |
| `/menu/favorites` | `apps/web/app/menu/favorites/page.tsx` |
| `/menu/scenarios` | `apps/web/app/menu/scenarios/page.tsx` |
| `/menu/settings` | `apps/web/app/menu/settings/page.tsx` |
| `/menu/leftovers` | `apps/web/app/menu/leftovers/page.tsx` |
| `/menu/event` | `apps/web/app/menu/event/page.tsx` |
| `/nutritionist` | `apps/web/app/nutritionist/page.tsx` |
| `/nutritionist/chat` | `apps/web/app/nutritionist/chat/page.tsx` |
| `/nutritionist/care` | `apps/web/app/nutritionist/care/page.tsx` |
| `/health` | `apps/web/app/health/page.tsx` |
| `/health/today` | `apps/web/app/health/today/page.tsx` |
| `/health/chat` | `apps/web/app/health/chat/page.tsx` |
| `/health/care` | `apps/web/app/health/care/page.tsx` |
| `/progress` | `apps/web/app/progress/page.tsx` |
| `/notifications` | `apps/web/app/notifications/page.tsx` |
| `/subscription` | `apps/web/app/subscription/page.tsx` |
| `/settings` | `apps/web/app/settings/page.tsx` |
| `/settings/account` | `apps/web/app/settings/account/page.tsx` |
| `/settings/about` | `apps/web/app/settings/about/page.tsx` |
| `/settings/support` | `apps/web/app/settings/support/page.tsx` |
| `/settings/documents` | `apps/web/app/settings/documents/page.tsx` |
| `/settings/delete-data` | `apps/web/app/settings/delete-data/page.tsx` |
| `/admin` | `apps/web/app/admin/page.tsx` |
| `/admin/users` | `apps/web/app/admin/users/page.tsx` |
| `/admin/users/[id]` | `apps/web/app/admin/users/[id]/page.tsx` |
| `/admin/families` | `apps/web/app/admin/families/page.tsx` |
| `/admin/families/[id]` | `apps/web/app/admin/families/[id]/page.tsx` |
| `/admin/subscriptions` | `apps/web/app/admin/subscriptions/page.tsx` |
| `/admin/ams` | `apps/web/app/admin/ams/page.tsx` |
| `/admin/openai` | `apps/web/app/admin/openai/page.tsx` |
| `/admin/errors` | `apps/web/app/admin/errors/page.tsx` |

**Loading states** (`loading.tsx`):

- `apps/web/app/menu/loading.tsx`
- `apps/web/app/pantry/loading.tsx`
- `apps/web/app/shopping/loading.tsx`

---

## Routes (Frontend)

### Next.js file-based routes

Все маршруты выше — file-based App Router (`apps/web/app/**/page.tsx`).

### Next.js API routes

| Method | Route | Файл |
|--------|-------|------|
| GET | `/api/health` | `apps/web/app/api/health/route.ts` |

### Production proxy

В production nginx проксирует backend под префиксом `/api` (см. `deploy/nginx/templates/`).

---

## API Endpoints (FastAPI)

Базовый URL: `http://localhost:8000` (dev) · `https://<domain>/api` (prod через nginx).

### Root & Health

| Method | Path |
|--------|------|
| GET | `/` |
| GET | `/health/live` |
| GET | `/health` |

### `/auth`

| Method | Path |
|--------|------|
| POST | `/auth/telegram` |
| POST | `/auth/dev-login` |

### `/legal`

| Method | Path |
|--------|------|
| GET | `/legal/documents` |
| GET | `/legal/status` |
| POST | `/legal/accept` |
| POST | `/legal/skip-phone` |
| POST | `/legal/delete-data-request` |

### `/users`

| Method | Path |
|--------|------|
| GET | `/users/me/app-context` |
| PATCH | `/users/me/app-context` |

### `/onboarding`

| Method | Path |
|--------|------|
| GET | `/onboarding/me` |
| PUT | `/onboarding/me` |

### `/nutrition-profile`

| Method | Path |
|--------|------|
| GET | `/nutrition-profile/me` |
| PUT | `/nutrition-profile/me` |

### `/families`

| Method | Path |
|--------|------|
| POST | `/families` |
| GET | `/families/me` |
| PATCH | `/families/me` |
| DELETE | `/families/me` |
| POST | `/families/me/leave` |
| POST | `/families/me/transfer-admin` |
| PATCH | `/families/me/allow-admin-edit` |
| POST | `/families/{family_id}/invite-by-phone` |
| POST | `/families/{family_id}/invites/link` |
| POST | `/families/{family_id}/invites` |
| GET | `/families/{family_id}/invites` |
| POST | `/families/{family_id}/members` |
| POST | `/families/{family_id}/members/virtual` |
| PUT | `/families/{family_id}/members/{member_id}/nutrition` |
| PATCH | `/families/{family_id}/members/{member_id}` |
| DELETE | `/families/{family_id}/members/{member_id}` |

### `/menus`

| Method | Path |
|--------|------|
| POST | `/menus/generate` |
| POST | `/menus/replace-dish` |
| POST | `/menus/select` |
| GET | `/menus/selected` |
| GET | `/menus/overview` |
| POST | `/menus/quick-action` |

### `/meal-checkins`

| Method | Path |
|--------|------|
| GET | `/meal-checkins/today` |
| POST | `/meal-checkins` |

### `/meal-leftovers`

| Method | Path |
|--------|------|
| GET | `/meal-leftovers` |
| POST | `/meal-leftovers` |
| PATCH | `/meal-leftovers/{leftover_id}` |
| DELETE | `/meal-leftovers/{leftover_id}` |

### `/shopping-lists`

| Method | Path |
|--------|------|
| GET | `/shopping-lists/me` |
| POST | `/shopping-lists/sync` |
| POST | `/shopping-lists/items` |
| PATCH | `/shopping-lists/items/{item_id}` |
| DELETE | `/shopping-lists/items/{item_id}` |
| PATCH | `/shopping-lists/items/{item_id}/toggle` |

### `/shopping-categories`

| Method | Path |
|--------|------|
| GET | `/shopping-categories` |
| POST | `/shopping-categories` |

### `/pantry`

| Method | Path |
|--------|------|
| GET | `/pantry/me` |
| POST | `/pantry/items` |
| PATCH | `/pantry/items/{item_id}` |
| DELETE | `/pantry/items/{item_id}` |

### `/recipes`

| Method | Path |
|--------|------|
| GET | `/recipes/filters` |
| GET | `/recipes/recommendations` |
| POST | `/recipes` |
| GET | `/recipes` |
| GET | `/recipes/history` |
| GET | `/recipes/from-pantry` |
| GET | `/recipes/scenarios` |
| GET | `/recipes/{recipe_id}` |
| PATCH | `/recipes/{recipe_id}` |
| GET | `/recipes/{recipe_id}/why` |
| POST | `/recipes/{recipe_id}/cooked` |
| GET | `/recipes/{recipe_id}/history` |
| POST | `/recipes/{recipe_id}/rate` |
| POST | `/recipes/{recipe_id}/favorite` |
| GET | `/recipes/{recipe_id}/evaluate` |
| GET | `/recipes/{recipe_id}/family-compatibility` |
| GET | `/recipes/{recipe_id}/improve` |
| POST | `/recipes/{recipe_id}/improve` |
| POST | `/recipes/{recipe_id}/add-to-shopping` |
| POST | `/recipes/{recipe_id}/add-to-menu` |

### `/collections`

| Method | Path |
|--------|------|
| GET | `/collections` |
| POST | `/collections` |
| GET | `/collections/{collection_id}` |
| PATCH | `/collections/{collection_id}` |
| DELETE | `/collections/{collection_id}` |
| POST | `/collections/{collection_id}/recipes` |
| DELETE | `/collections/{collection_id}/recipes/{recipe_id}` |

### `/event-plans`

| Method | Path |
|--------|------|
| POST | `/event-plans` |
| GET | `/event-plans` |
| GET | `/event-plans/{plan_id}` |
| POST | `/event-plans/{plan_id}/create-shopping-list` |

### `/nutritionist`

| Method | Path |
|--------|------|
| POST | `/nutritionist/ask` |
| GET | `/nutritionist/deferred-advice` |
| GET | `/nutritionist/deferred-advice/suppressed-titles` |
| POST | `/nutritionist/deferred-advice` |
| PATCH | `/nutritionist/deferred-advice/{advice_id}` |
| DELETE | `/nutritionist/deferred-advice/{advice_id}` |
| GET | `/nutritionist/water/today` |
| POST | `/nutritionist/water` |

### `/progress`

| Method | Path |
|--------|------|
| GET | `/progress/me` |
| POST | `/progress/me` |
| GET | `/progress/history` |
| POST | `/progress/training` |
| GET | `/progress/training` |
| GET | `/progress/targets` |
| PATCH | `/progress/targets` |
| PATCH | `/progress/settings` |

### `/subscriptions`

| Method | Path |
|--------|------|
| GET | `/subscriptions/me` |
| POST | `/subscriptions/select-plan` |

### `/notifications`

| Method | Path |
|--------|------|
| GET | `/notifications/settings` |
| PUT | `/notifications/settings` |

### `/care`

| Method | Path |
|--------|------|
| GET | `/care/settings` |
| PATCH | `/care/settings` |
| GET | `/care/notifications` |
| GET | `/care/tips` |
| POST | `/care/test-notification` |

### `/telegram` & `/bot`

| Method | Path |
|--------|------|
| POST | `/telegram/webhook` |
| GET | `/telegram/webhook/info` |
| GET | `/telegram/webhook/url` |
| POST | `/bot/webhook` (alias) |

### `/admin`

| Method | Path |
|--------|------|
| GET | `/admin/ping` |
| GET | `/admin/summary` |
| GET | `/admin/users` |
| GET | `/admin/users/{user_id}` |
| DELETE | `/admin/users/{user_id}` |
| POST | `/admin/users/{user_id}/block` |
| POST | `/admin/users/{user_id}/unblock` |
| POST | `/admin/users/{user_id}/reset/onboarding` |
| POST | `/admin/users/{user_id}/reset/phone` |
| POST | `/admin/users/{user_id}/reset/legal` |
| POST | `/admin/users/{user_id}/reset/nutrition` |
| POST | `/admin/users/{user_id}/subscription/grant` |
| POST | `/admin/users/{user_id}/subscription/extend` |
| POST | `/admin/users/{user_id}/subscription/disable` |
| POST | `/admin/users/{user_id}/subscription/change-plan` |
| POST | `/admin/users/{user_id}/ams/add` |
| POST | `/admin/users/{user_id}/ams/remove` |
| POST | `/admin/users/{user_id}/ams/reset` |
| GET | `/admin/families` |
| GET | `/admin/families/{family_id}` |
| PATCH | `/admin/families/{family_id}` |
| POST | `/admin/families/{family_id}/block` |
| POST | `/admin/families/{family_id}/unblock` |
| DELETE | `/admin/families/{family_id}` |
| POST | `/admin/families/{family_id}/transfer-owner` |
| DELETE | `/admin/families/{family_id}/members/{member_id}` |
| POST | `/admin/families/{family_id}/subscription/grant` |
| POST | `/admin/families/{family_id}/subscription/extend` |
| POST | `/admin/families/{family_id}/subscription/disable` |
| POST | `/admin/families/{family_id}/subscription/change-plan` |
| POST | `/admin/families/{family_id}/ams/add` |
| POST | `/admin/families/{family_id}/ams/remove` |
| POST | `/admin/families/{family_id}/ams/reset` |
| GET | `/admin/subscriptions` |
| GET | `/admin/plans` |
| POST | `/admin/subscriptions/grant` |
| POST | `/admin/ams/grant` |
| POST | `/admin/ams/deduct` |
| POST | `/admin/ams/grant-family` |
| GET | `/admin/ams/summary` |
| GET | `/admin/ams/transactions` |
| GET | `/admin/openai` |
| GET | `/admin/errors` |
| GET | `/admin/ai-usage` |
| GET | `/admin/backups` |
| POST | `/admin/backups/create` |

**Роутеры:** `apps/api/app/routers/` (23 файла) · регистрация в `apps/api/app/main.py`

---

## Database Tables (PostgreSQL)

48 таблиц (SQLAlchemy models + `database_migrations.py`):

### Users & Profiles

| Таблица | Model |
|---------|-------|
| `users` | `apps/api/app/models/user.py` |
| `user_profiles` | `apps/api/app/models/user_profile.py` |
| `user_preferences` | `apps/api/app/models/user_preferences.py` |
| `user_notification_settings` | `apps/api/app/models/notification_settings.py` |

### Family

| Таблица | Model |
|---------|-------|
| `families` | `apps/api/app/models/family.py` |
| `family_members` | `apps/api/app/models/family.py` |
| `family_invites` | `apps/api/app/models/family_invite.py` |
| `family_menu_selections` | `apps/api/app/models/menu_selection.py` |
| `family_shopping_lists` | `apps/api/app/models/shopping_list.py` |
| `family_pantry_items` | `apps/api/app/models/pantry.py` |
| `family_recipe_preferences` | `apps/api/app/models/recipe_engine.py` |

### Recipes

| Таблица | Model |
|---------|-------|
| `recipes` | `apps/api/app/models/recipe.py` |
| `recipe_ingredients` | `apps/api/app/models/recipe.py` |
| `recipe_steps` | `apps/api/app/models/recipe.py` |
| `recipe_tags` | `apps/api/app/models/recipe.py` |
| `recipe_allergens` | `apps/api/app/models/recipe.py` |
| `recipe_restrictions` | `apps/api/app/models/recipe.py` |
| `recipe_ratings` | `apps/api/app/models/recipe.py` |
| `recipe_favorites` | `apps/api/app/models/recipe.py` |
| `recipe_import_jobs` | `apps/api/app/models/recipe.py` |
| `recipe_collections` | `apps/api/app/models/recipe_engine.py` |
| `collection_recipes` | `apps/api/app/models/recipe_engine.py` |
| `recipe_history` | `apps/api/app/models/recipe_engine.py` |
| `recipe_scenarios` | `apps/api/app/models/recipe_engine.py` |
| `recipe_explanations` | `apps/api/app/models/recipe_engine.py` |

### Shopping & Pantry

| Таблица | Model |
|---------|-------|
| `shopping_categories` | `apps/api/app/models/shopping_category.py` |

### Meals & Menu

| Таблица | Model |
|---------|-------|
| `meal_checkins` | `apps/api/app/models/meal_checkin.py` |
| `meal_eating_schedules` | `apps/api/app/models/meal_eating_schedule.py` |
| `meal_leftovers` | `apps/api/app/models/meal_leftover.py` |
| `event_plans` | `apps/api/app/models/event_plan.py` |

### Subscriptions & AI

| Таблица | Model |
|---------|-------|
| `subscription_plans` | `apps/api/app/models/subscription.py` |
| `user_subscriptions` | `apps/api/app/models/subscription.py` |
| `ama_wallets` | `apps/api/app/models/subscription.py` |
| `ama_transactions` | `apps/api/app/models/subscription.py` |
| `ai_usage_logs` | `apps/api/app/models/subscription.py` |

### Health & Progress

| Таблица | Model |
|---------|-------|
| `progress_entries` | `apps/api/app/models/progress.py` |
| `training_entries` | `apps/api/app/models/progress.py` |
| `nutrition_targets` | `apps/api/app/models/progress.py` |
| `deferred_nutrition_advice` | `apps/api/app/models/deferred_advice.py` |
| `water_intake_logs` | `apps/api/app/models/water_intake.py` |

### Care

| Таблица | Model |
|---------|-------|
| `care_settings` | `apps/api/app/models/care.py` |
| `care_notifications` | `apps/api/app/models/care.py` |
| `care_events` | `apps/api/app/models/care.py` |

### Admin & Bot

| Таблица | Model |
|---------|-------|
| `admin_sessions` | `apps/api/app/models/admin.py` |
| `admin_login_attempts` | `apps/api/app/models/admin.py` |
| `admin_actions` | `apps/api/app/models/admin.py` |
| `admin_error_logs` | `apps/api/app/models/admin.py` |
| `telegram_bot_sessions` | `apps/api/app/models/bot_session.py` |

**Инициализация схемы:** `apps/api/app/database.py` → `database_migrations.ensure_database_schema()`

---

## Scripts

### NPM (`apps/web/package.json`)

| Script | Команда |
|--------|---------|
| `dev` | `next dev --hostname 0.0.0.0` |
| `build` | `next build` |
| `start` | `next start --hostname 0.0.0.0` |
| `lint` | `next lint` |

### Shell

| Файл | Назначение |
|------|------------|
| `scripts/backup.sh` | Бэкап БД |
| `scripts/restore.sh` | Восстановление БД |
| `apps/api/start.sh` | Старт API в Docker |
| `deploy/init-letsencrypt.sh` | Инициализация Let's Encrypt |
| `deploy/nginx/docker-entrypoint.sh` | Entrypoint nginx |

### Python — `scripts/`

| Файл |
|------|
| `scripts/seed_recipes.py` |
| `scripts/reset_user.py` |
| `scripts/dedupe_shopping_categories.py` |

### Python — `backend/scripts/` (37 файлов)

| Файл | Назначение (кратко) |
|------|---------------------|
| `analyze_povarenok_dataset.py` | Анализ датасета Povarenok |
| `analyze_recipe_dataset.py` | Анализ датасета рецептов |
| `apply_calculated_nutrition_updates.py` | Применение расчётов nutrition |
| `apply_nutrition_backfill.py` | Backfill nutrition |
| `apply_recipe_steps_updates.py` | Обновление шагов рецептов |
| `audit_beverage_nutrition_strategy.py` | Аудит nutrition напитков |
| `audit_nutrition_update_deltas.py` | Аудит дельт nutrition |
| `audit_povarenok_jsonl.py` | Аудит JSONL Povarenok |
| `audit_recipe_duplicates.py` | Аудит дубликатов рецептов |
| `audit_recipe_steps_after_update.py` | Аудит шагов после обновления |
| `audit_recipe_steps_quality.py` | Качество шагов рецептов |
| `audit_recipe_steps_v2.py` | Аудит шагов v2 |
| `audit_remaining_nutrition_gaps.py` | Оставшиеся пробелы nutrition |
| `audit_weak_steps_remediation.py` | Слабые шаги — remediation |
| `build_enrichment_batch.py` | Batch enrichment |
| `build_holiday_kids_steps_batch.py` | Holiday/kids steps batch |
| `build_holiday_kids_steps_update.py` | Holiday/kids steps update |
| `build_remaining_weak_groups.py` | Weak groups batch |
| `build_simple_beverage_updates.py` | Обновления напитков |
| `build_steps_update_from_enrichment.py` | Steps из enrichment |
| `build_verified_nutrition_updates.py` | Verified nutrition updates |
| `calculate_recipe_nutrition_preview.py` | Preview расчёта nutrition |
| `convert_enriched_to_import_json.py` | Enriched → import JSON |
| `convert_nutrition_backfill_to_update_json.py` | Backfill → update JSON |
| `convert_povarenok.py` | Конвертация Povarenok |
| `export_calculated_nutrition_updates.py` | Экспорт nutrition updates |
| `import_recipes.py` | Импорт рецептов |
| `normalize_ingredient_amounts.py` | Нормализация количеств |
| `plan_nutrition_backfill.py` | План backfill nutrition |
| `plan_recipe_dedup.py` | План dedup рецептов |
| `prepare_povarenok_enrichment_input.py` | Input для enrichment |
| `run_enrichment_pilot.py` | Pilot enrichment |
| `run_nutrition_backfill.py` | Запуск nutrition backfill |
| `run_steps_enrichment.py` | Enrichment шагов |
| `select_povarenok_candidates.py` | Отбор кандидатов Povarenok |

---

## Docs

### Корень репозитория

| Файл |
|------|
| `README.md` |
| `MASTER.md` |
| `PROJECT_CONTEXT.md` |
| `TASKS.md` |
| `DEPLOY.md` |

### `docs/`

| Файл |
|------|
| `docs/BUGS.md` |
| `docs/BUTTON_MAP.md` |
| `docs/DEPLOY_SAFE.md` |
| `docs/FINAL_ANALYSIS.md` |
| `docs/NAVIGATION_MAP.md` |
| `docs/PRODUCT_LOGIC.md` |
| `docs/PRODUCT_VISION.md` |
| `docs/PRODUCTION_DEPLOY.md` |
| `docs/RECIPE_ENGINE_API.md` |
| `docs/RECIPE_ENGINE_ENV.md` |
| `docs/RECIPE_ENGINE_V1.md` |
| `docs/RECIPE_IMPORT_PIPELINE.md` |
| `docs/ROADMAP_V1.md` |
| `docs/SCREEN_MAP.md` |
| `docs/TELEGRAM_SETUP.md` |
| `docs/TEST_CHECKLIST.md` |
| `docs/USER_FLOWS.md` |
| `docs/USER_RESET.md` |
| `docs/UX_PROBLEMS.md` |
| `docs/full-audit.md` |
| `docs/CODEBASE_INDEX.md` *(этот файл)* |

---

## Docker

### Compose

| Файл | Назначение |
|------|------------|
| `docker-compose.yml` | Local dev: web, api, postgres, redis |
| `docker-compose.prod.yml` | Production: nginx, certbot, web, api, postgres, redis |

### Dockerfiles

| Файл |
|------|
| `apps/web/Dockerfile` |
| `apps/web/Dockerfile.prod` |
| `apps/api/Dockerfile` |
| `apps/api/Dockerfile.prod` |

### Deploy (nginx / SSL)

| Файл |
|------|
| `deploy/nginx/nginx.conf` |
| `deploy/nginx/docker-entrypoint.sh` |
| `deploy/nginx/templates/app-init.conf.template` |
| `deploy/nginx/templates/app-ssl.conf.template` |
| `deploy/init-letsencrypt.sh` |

---

## Environment Variables

Источники: `.env.example`, `.env.production.example`, `apps/api/.env.example`, `apps/web/.env.example`, `apps/api/app/config.py`.

### Shared / Compose

| Variable | Описание |
|----------|----------|
| `COMPOSE_PROJECT_NAME` | Имя Docker Compose проекта |

### Frontend (Next.js)

| Variable | Описание |
|----------|----------|
| `NEXT_PUBLIC_API_URL` | URL backend API |
| `NEXT_PUBLIC_TELEGRAM_BOT_USERNAME` | Username Telegram-бота |
| `NEXT_PUBLIC_TELEGRAM_APP_SHORT_NAME` | Short name Mini App |

### Backend — Core

| Variable | Config field | Default |
|----------|--------------|---------|
| `BACKEND_CORS_ORIGINS` | `backend_cors_origins` | `http://localhost:3000` |
| `DATABASE_URL` | `database_url` | `postgresql://aifood:aifood@postgres:5432/aifood` |
| `REDIS_URL` | `redis_url` | `redis://redis:6379/0` |
| `ENVIRONMENT` | `environment` | `development` |

### Telegram

| Variable | Config field |
|----------|--------------|
| `TELEGRAM_BOT_TOKEN` | `telegram_bot_token` |
| `TELEGRAM_WEBAPP_URL` | `telegram_webapp_url` |
| `TELEGRAM_WEBHOOK_URL` | `telegram_webhook_url` |
| `TELEGRAM_AUTO_SETUP_WEBHOOK` | `telegram_auto_setup_webhook` |
| `TELEGRAM_MENU_BUTTON_TEXT` | `telegram_menu_button_text` |
| `TELEGRAM_WEBHOOK_SECRET` | `telegram_webhook_secret` |

### OpenAI

| Variable | Config field | Default |
|----------|--------------|---------|
| `OPENAI_API_KEY` | `openai_api_key` | — |
| `OPENAI_MODEL` | `openai_model` | `gpt-4o-mini` |

### Admin

| Variable | Config field |
|----------|--------------|
| `ADMIN_TELEGRAM_IDS` | `admin_telegram_ids` |
| `ADMIN_PIN` | `admin_pin` |
| `ADMIN_PANEL_ENABLED` | `admin_panel_enabled` |
| `BACKUP_ROOT` | `backup_root` |

### Recipe Engine feature flags

| Variable | Config field | Default |
|----------|--------------|---------|
| `RECIPE_ENGINE_V1` | `recipe_engine_v1` | `false` |
| `RECIPE_COLLECTIONS` | `recipe_collections` | `true` |
| `RECIPE_HISTORY` | `recipe_history` | `true` |
| `RECIPE_SCENARIOS` | `recipe_scenarios` | `true` |
| `RECIPE_EXPLAINABILITY` | `recipe_explainability` | `true` |
| `FAMILY_RECIPE_PREFERENCES` | `family_recipe_preferences` | `true` |

### PostgreSQL

| Variable |
|----------|
| `POSTGRES_USER` |
| `POSTGRES_PASSWORD` |
| `POSTGRES_DB` |

### Production-only

| Variable | Описание |
|----------|----------|
| `DOMAIN` | Публичный домен |
| `CERTBOT_EMAIL` | Email для Let's Encrypt |
| `NGINX_TEMPLATE` | `app-init.conf.template` или `app-ssl.conf.template` |

### Env example files

- `.env.example`
- `.env.production.example`
- `apps/api/.env.example`
- `apps/web/.env.example`

---

## Middleware

### Next.js

`middleware.ts` **отсутствует**.

### FastAPI (`apps/api/app/main.py`)

| Middleware | Назначение |
|------------|------------|
| `AdminErrorLoggingMiddleware` | Логирование 5xx в `admin_error_logs` |
| `CORSMiddleware` | CORS по `BACKEND_CORS_ORIGINS` |

### FastAPI Dependencies (`apps/api/app/deps.py`)

| Dependency | Назначение |
|------------|------------|
| `get_current_user` | Auth через `X-Telegram-Init-Data` (Telegram / dev) |
| `get_verified_user` | Legal + phone + block checks |
| `get_app_scope` | Scope по `X-App-Mode` (personal / family) |
| `require_admin_user` | Admin panel: Telegram ID + `X-Admin-Session` |

### Client-side gate (UI)

| Component | Назначение |
|-----------|------------|
| `AppGate` | Обёртка доступа: Telegram, legal, phone |
| `AppProviders` | Провайдеры контекста приложения |
| `ProtectedScreenFallback` | Fallback для защищённых экранов |

---

## Layouts

| Layout | Файл | Описание |
|--------|------|----------|
| Root | `apps/web/app/layout.tsx` | HTML shell, Manrope font, `AppProviders` |
| Admin | `apps/web/app/admin/layout.tsx` | Обёртка `AdminShell` |

### Section layouts (компоненты-обёртки)

| Component | Файл |
|-----------|------|
| `AppShell` | `components/layout/AppShell.tsx` |
| `ScreenLayout` | `components/layout/ScreenLayout.tsx` |
| `MenuSectionLayout` | `components/menu/MenuSectionLayout.tsx` |
| `ShoppingSectionLayout` | `components/shopping/ShoppingSectionLayout.tsx` |
| `SettingsScaffold` | `components/settings/SettingsScaffold.tsx` |
| `AdminShell` | `components/admin/AdminShell.tsx` |
| `SectionHub` | `components/layout/SectionHub.tsx` |

---

## Major UI Components

126 компонентов в `apps/web/components/`. Ключевые по доменам:

### Auth & Onboarding

| Component | Файл |
|-----------|------|
| `AppGate` | `auth/AppGate.tsx` |
| `TelegramRequiredScreen` | `auth/TelegramRequiredScreen.tsx` |
| `LegalConsentScreen` | `auth/LegalConsentScreen.tsx` |
| `PhoneRequiredScreen` | `auth/PhoneRequiredScreen.tsx` |
| `TelegramAuthPanel` | `TelegramAuthPanel.tsx` |
| `OnboardingWizard` | `onboarding/OnboardingWizard.tsx` |
| `OnboardingComplete` | `onboarding/OnboardingComplete.tsx` |

### Home

| Component | Файл |
|-----------|------|
| `PlanAmHome` | `home/PlanAmHome.tsx` |
| `HomeTodayCard` | `home/HomeTodayCard.tsx` |
| `HomeQuickActions` | `home/HomeQuickActions.tsx` |
| `HomeRecommendations` | `home/HomeRecommendations.tsx` |
| `HomeShoppingCard` | `home/HomeShoppingCard.tsx` |
| `HomeFamilySummary` | `home/HomeFamilySummary.tsx` |
| `HomeAskPlanAm` | `home/HomeAskPlanAm.tsx` |

### Menu

| Component | Файл |
|-----------|------|
| `MenuHub` | `menu/MenuHub.tsx` |
| `MenuPlanner` | `menu/MenuPlanner.tsx` |
| `MenuCurrentView` | `menu/MenuCurrentView.tsx` |
| `MenuChooseVariants` | `menu/MenuChooseVariants.tsx` |
| `MenuVariantCard` | `menu/MenuVariantCard.tsx` |
| `MenuDayPicker` | `menu/MenuDayPicker.tsx` |
| `MenuDayOverview` | `menu/MenuDayOverview.tsx` |
| `MenuSettingsPage` | `menu/MenuSettingsPage.tsx` |
| `MealCheckinPanel` | `menu/MealCheckinPanel.tsx` |
| `MealLeftoversPage` | `menu/MealLeftoversPage.tsx` |
| `ReplaceDishModal` | `menu/ReplaceDishModal.tsx` |
| `MenuQuickActionsSheet` | `menu/MenuQuickActionsSheet.tsx` |

### Recipes

| Component | Файл |
|-----------|------|
| `RecipesView` | `recipes/RecipesView.tsx` |
| `RecipeCard` | `recipes/RecipeCard.tsx` |
| `RecipeDetailModal` | `recipes/RecipeDetailModal.tsx` |
| `RecipeDetailMorePanel` | `recipes/RecipeDetailMorePanel.tsx` |
| `RecipeCatalogSections` | `recipes/RecipeCatalogSections.tsx` |
| `RecipeFiltersSheet` | `recipes/RecipeFiltersSheet.tsx` |
| `FromPantrySection` | `recipes/FromPantrySection.tsx` |
| `FavoritesView` | `recipes/FavoritesView.tsx` |
| `CollectionsView` | `recipes/CollectionsView.tsx` |
| `CollectionDetailView` | `recipes/CollectionDetailView.tsx` |
| `ScenarioChips` | `recipes/ScenarioChips.tsx` |

### Shopping & Pantry

| Component | Файл |
|-----------|------|
| `ShoppingListView` | `shopping/ShoppingListView.tsx` |
| `ShoppingItemSheet` | `shopping/ShoppingItemSheet.tsx` |
| `ShoppingCategorySheet` | `shopping/ShoppingCategorySheet.tsx` |
| `CategoryPicker` | `shopping/CategoryPicker.tsx` |
| `PantryDashboard` | `pantry/PantryDashboard.tsx` |
| `PantryItemForm` | `pantry/PantryItemForm.tsx` |
| `PantryItemCard` | `pantry/PantryItemCard.tsx` |

### Family & Profile

| Component | Файл |
|-----------|------|
| `FamilyDashboard` | `family/FamilyDashboard.tsx` |
| `MemberCard` | `family/MemberCard.tsx` |
| `MemberForm` | `family/MemberForm.tsx` |
| `InviteSheet` | `family/InviteSheet.tsx` |
| `AddPersonSheet` | `family/AddPersonSheet.tsx` |
| `VirtualMemberNutritionForm` | `family/VirtualMemberNutritionForm.tsx` |
| `ProfileDashboard` | `profile/ProfileDashboard.tsx` |
| `NutritionProfileForm` | `nutrition-profile/NutritionProfileForm.tsx` |

### Nutritionist & Health

| Component | Файл |
|-----------|------|
| `NutritionistDashboard` | `nutritionist/NutritionistDashboard.tsx` |
| `NutritionistChat` | `nutritionist/NutritionistChat.tsx` |
| `NutritionistAdviceCard` | `nutritionist/NutritionistAdviceCard.tsx` |
| `HealthTodayView` | `nutritionist/HealthTodayView.tsx` |
| `WaterIntakePanel` | `nutritionist/WaterIntakePanel.tsx` |
| `CareSettingsPanel` | `care/CareSettingsPanel.tsx` |
| `CareTelegramLinkCard` | `care/CareTelegramLinkCard.tsx` |

### Progress & Subscription

| Component | Файл |
|-----------|------|
| `ProgressDashboard` | `progress/ProgressDashboard.tsx` |
| `ProgressProLocked` | `progress/ProgressProLocked.tsx` |
| `SubscriptionDashboard` | `subscription/SubscriptionDashboard.tsx` |
| `SubscriptionProvider` | `subscription/SubscriptionProvider.tsx` |
| `AmaConfirmDialog` | `subscription/AmaConfirmDialog.tsx` |

### Admin

| Component | Файл |
|-----------|------|
| `AdminDashboard` | `admin/AdminDashboard.tsx` |
| `AdminUserDetailPage` | `admin/AdminUserDetailPage.tsx` |
| `AdminFamilyDetailPage` | `admin/AdminFamilyDetailPage.tsx` |
| `AdminOpenAiPage` | `admin/AdminOpenAiPage.tsx` |
| `AdminErrorsPage` | `admin/AdminErrorsPage.tsx` |
| `AdminSessionCapture` | `admin/AdminSessionCapture.tsx` |
| `AdminConfirmDialog` | `admin/AdminConfirmDialog.tsx` |

### Layout & UI primitives

| Component | Файл |
|-----------|------|
| `BottomNavigation` | `layout/BottomNavigation.tsx` |
| `BottomNav` | `layout/BottomNav.tsx` |
| `ScreenBackNav` | `layout/ScreenBackNav.tsx` |
| `StickyBottomBar` | `layout/StickyBottomBar.tsx` |
| `SegmentedTabs` | `layout/SegmentedTabs.tsx` |
| `Sheet` | `ui/Sheet.tsx` |
| `ToastProvider` | `ui/ToastProvider.tsx` |
| `HubTile` | `ui/HubTile.tsx` |
| `Skeleton` | `ui/Skeleton.tsx` |
| `PageLoading` | `ui/PageLoading.tsx` |

### App mode & providers

| Component | Файл |
|-----------|------|
| `AppProviders` | `AppProviders.tsx` |
| `TelegramProvider` | `TelegramProvider.tsx` |
| `AppModeProvider` | `app-mode/AppModeProvider.tsx` |
| `ModeSwitcher` | `app-mode/ModeSwitcher.tsx` |
| `ModeBanner` | `app-mode/ModeBanner.tsx` |
| `NotificationSettingsForm` | `notifications/NotificationSettingsForm.tsx` |
| `HealthStatus` | `HealthStatus.tsx` |
| `DevModeBanner` | `dev/DevModeBanner.tsx` |

---

## Быстрые ссылки на entry points

| Entry | Путь |
|-------|------|
| Web root page | `apps/web/app/page.tsx` |
| API main | `apps/api/app/main.py` |
| API config | `apps/api/app/config.py` |
| DB init | `apps/api/app/database.py` |
| Auth deps | `apps/api/app/deps.py` |
| Next config | `apps/web/next.config.mjs` |
