# Логика продукта ПланАм

Фактическая бизнес-логика по доменам. Источник — `apps/api/app/services/*.py`, `apps/api/app/models/*.py`, `apps/web/lib/*`, `apps/web/components/*`.

---

## 1. Меню (план питания)

**Что делает.** Формирует три AI-варианта меню (`quick`, `economy`, `balanced`) на N дней с учётом профиля питания, состава семьи, остатков и запасов; пользователь выбирает один — он становится активным планом.

**Использует данные**

- `user_profiles` — цель, аллергии, ограничения, диета, время готовки, бюджет.
- `families`, `family_members` (включая виртуальных) — состав едоков, их nutrition-профили.
- `meal_eating_schedules` — кто где ест по дням.
- `family_pantry_items` — что уже есть.
- `meal_leftovers (status=active)` — что осталось.
- `recipes` + `recipe_ingredients` — каталог для подбора.
- `user_preferences.active_mode` — personal/family.
- `localStorage.planam_plan_mode`, `planam_persons_override`.

**Создаёт**

- `family_menu_selections` (одна запись на user/family; `menu_data` JSONB с `_meta`).
- Через `shopping_list_service.sync_from_menu` — пункты в `family_shopping_lists`.
- `ai_usage_logs`, `ama_transactions` (если списываются Амы).
- Опционально `care_events` (через `maybe_notify_menu_ready`).

**Изменяет**

- `user_subscriptions.menu_generations_used` (инкремент после `commit_menu_generation`).
- `ama_wallets.balance` (если генерация сверх лимита).

**Зависит от**

- AI (OpenAI) — `menu_ai.generate_menus`. Если AI недоступен, используется fallback из `recipe_seed`.
- `subscription.assert_menu_generation_allowed`.
- `menu_context_fingerprint.compute_context_fingerprint` — фиксирует контекст в `_meta`, чтобы понимать «нужно обновить».
- `menu_days.expand_variant_to_plan_days` — достраивает дни, если AI вернул один.

**Влияет на**

- `/menu`, `/menu/current`, `/shopping`, `MealCheckinPanel`, Care и нутрициолог.

---

## 2. Рецепты

**Что делает.** Каталог рецептов (системные + импорт + созданные через AI). Поиск, фильтры, избранное, оценка совместимости, добавление в покупки/меню.

**Использует**

- `recipes`, `recipe_ingredients`, `recipe_steps`, `recipe_tags`, `recipe_allergens`, `recipe_restrictions`.
- `recipe_ratings` — избранное, оценка, число приготовлений.
- `user_profiles` — для совместимости и оценки.

**Создаёт**

- `recipe_ratings` (при tap «В избранное» / «Оценить»).
- `recipe_import_jobs` (импорт из внешних источников — фоновая задача).
- `ai_usage_logs`, `ama_transactions` (для `recipe_analyze`, `recipe_improve`).

**Изменяет**

- `family_shopping_lists.items_json` (при `add-to-shopping`).
- `family_menu_selections.menu_data` (при `add-to-menu` — замена/добавление блюда).

**Зависит от**

- AI для `evaluateRecipe`, `improve`, `family-compatibility`.
- Списания Амов через `subscription.require_ai_action`.

**Влияет на**

- Покупки, меню, нутрициолог (для подсказок).

---

## 3. Покупки

**Что делает.** Управляет списком покупок: добавление вручную, синхронизация с меню, авто-перевод в запасы при чекбоксе.

**Использует**

- `family_shopping_lists.items_json` (массив `ShoppingListItem`).
- `shopping_categories` (системные + пользовательские).
- `family_menu_selections` (через `sync_from_menu`).
- `family_pantry_items` (через `add_or_merge_from_shopping`).

**Создаёт**

- `family_shopping_lists` — одна запись на scope.
- `shopping_categories` (`user_id`/`family_id` для пользовательских).
- `family_pantry_items` (через `pantry_shopping.add_or_merge_from_shopping`).

**Изменяет**

- `items_json` (CRUD, toggle, sync).
- `updated_at` (для поллинга 4 с).
- `family_pantry_items.quantity` (при merge).

**Зависит от**

- `shopping_item_utils.normalize_item` — нормализация название/количества.
- `shopping_categories.infer_category` — fallback категории.
- `amount_parser` — числа/единицы.
- `category-suggest.ts` (клиент) — UX-подсказка.

**Влияет на**

- `/pantry` (через автодобавление).
- `MenuOverview` (отображает «Купить N»).

---

## 4. Запасы

**Что делает.** Учёт продуктов дома; фильтр «скоро заканчиваются»; используется при генерации меню (`pantry_used_rub`, `savings_rub`).

**Использует**

- `family_pantry_items` (CRUD).
- `shopping_categories` — категория и `is_food`.
- `users.id` (manual) или `family.id` (shared).

**Создаёт**

- Позиции из ручного добавления, авто-перевода из покупок, OCR чека.

**Изменяет**

- `quantity`, `expires_at`, `category`, `note`, `source`.

**Зависит от**

- `infer_category` для категорий.
- `amount_parser.format_amount` для отображения.
- `expires_at` (опционально) — расчёт `days_until_expiry`.

**Влияет на**

- Меню (генерация учитывает запасы).
- Главная (KPI «скоро заканчиваются»).
- Care (`pantry` уведомление при критическом списке).

---

## 5. Остатки блюд (meal_leftovers)

**Что делает.** Учёт остатков приготовленных блюд для последующих приёмов пищи и улучшения плана.

**Использует**

- `meal_leftovers` (`dish_name`, `portions_remaining`, `valid_until`, `leftover_status`).
- `meal_checkins.actual_status='saved_as_leftover'` (косвенно).

**Создаёт**

- Записи из UI `/menu/leftovers`, бот FSM (`STATE_LEFTOVER_*`), чекинов («поел дома, но осталось»).

**Изменяет**

- `leftover_status` (active → eaten/frozen/discarded).
- `portions_remaining` (при статусе `eaten`/`discarded` → 0).

**Зависит от**

- `meal_overview.meal_leftovers_count` — отображается в `/menu`.
- Бот FSM для интерактивного ввода.

**Влияет на**

- Генерация меню (передаёт `leftovers_count` в `_meta`).
- Нутрициолог (использует остатки для рекомендаций).
- Покупки (исключает дублирование позиций).

---

## 6. Нутрициолог

**Что делает.** Персональный AI-помощник: дневной баланс КБЖУ, прогресс к цели, совет дня, отложенные рекомендации, чат с AI, вода.

**Использует**

- `user_profiles` (цель, ограничения).
- `family_menu_selections` (плановый КБЖУ, что съел).
- `meal_checkins` (факт).
- `progress_entries` (вес).
- `water_intake_logs` (вода).
- `deferred_nutrition_advice` (отложенное).
- `subscription_overview` (для AI-функций).
- `nutrition_targets` (PRO).

**Создаёт**

- `deferred_nutrition_advice` (при «Не сейчас»).
- `ai_usage_logs`, `ama_transactions` (чат, deep-analysis).
- `water_intake_logs` (стаканы воды).

**Изменяет**

- `deferred_nutrition_advice.status` (deferred → completed/dismissed).
- `ama_wallets.balance`.

**Зависит от**

- `pickMainAdvice` (frontend) — выбирает совет.
- `nutritionist_service` (backend) — формирует `MenuOverview.nutritionist_advice`.
- `advice-why` — объяснение «почему этот совет».
- `goal-progress` — расчёт прогресса.

**Влияет на**

- `/menu` (показывает совет).
- Care (запускает push при `protein` / `water`).

---

## 7. Прогресс

**Что делает.** Журнал веса, замеров, тренировок, расчёт прогресса к цели, family-progress (если разрешено).

**Использует**

- `progress_entries` (вес, замеры).
- `training_entries` (тренировки).
- `user_profiles` (стартовый/целевой вес, цель).
- `nutrition_targets` (PRO).
- `families`/`family_members` (для family progress).
- Privacy-флаги (`hide_for_family`).

**Создаёт**

- Записи веса и тренировок.

**Изменяет**

- Privacy-флаг (PATCH /progress/privacy).
- `progress_overview.goal_progress_percent` (вычисляется на лету).

**Зависит от**

- `progress.calculate_goal_progress` (backend) и `goal-progress.computePercent` (frontend) — независимо считают %, могут расходиться.

**Влияет на**

- Нутрициолог (KPI «прогресс к цели»).
- Главная (опционально).
- Care (push о прогрессе).

---

## 8. Цели

**Что делает.** Определяет диету (`maintain`, `lose`, `gain`, `healthy`, `sport`, `kids`). Является основой для меню, советов и расчёта КБЖУ.

**Использует/создаёт**

- `user_profiles.nutrition_goal`, `goal_details` JSONB.
- `family_members.nutrition_profile.nutrition_goal`.

**Изменяет**

- Меню (контекст), нутрициолог, прогресс.

**Зависит от**

- `goal_details` (PRO: подробности по диетам).

**Влияет на**

- Все домены (меню, рецепты, нутрициолог, прогресс).

---

## 9. Семья

**Что делает.** Совместный режим: меню, покупки, запасы, билиннг общий. Управление участниками.

**Использует**

- `families`, `family_members`, `family_invites`, `user_preferences.active_mode`.
- `meal_eating_schedules` — где кто ест.

**Создаёт**

- Виртуальные участники (`is_virtual=true`).
- Приглашения по телефону / invite-link.
- Сеть Telegram-ботов через `notify_invitee_about_invite`.

**Изменяет**

- `family_members.role`, `allow_admin_profile_edit`, `nutrition_profile`.
- `user_subscriptions.family_id` (для family-billing).

**Зависит от**

- Тарифа: `plan.max_profiles` ограничивает добавление.
- Согласий: legal_accepted для участников.

**Влияет на**

- Меню (контекст), покупки/запасы (общие списки), care (общие уведомления).

---

## 10. Уведомления (cook/buy reminders)

**Что делает.** Шлёт через Telegram bot:

- утреннее «купить» (`buy_reminder_*`),
- «приготовить завтрак/обед/ужин» (`cook_*_*`).

**Использует**

- `user_notification_settings` (`enabled`, `time`, `timezone`, `last_*_sent_date`).

**Создаёт**

- Отправленные TG-сообщения (без записи в БД).

**Изменяет**

- `last_breakfast_sent_date`, `last_lunch_sent_date`, `last_dinner_sent_date`.

**Зависит от**

- `notification_scheduler.run_notification_scheduler` (фоновая задача).
- Timezone в `user_notification_settings` или `care_settings`.

**Влияет на**

- Активность пользователя, удержание.

### 10.b Care-уведомления

**Что делает.** Адаптивные уведомления (water/protein/menu/shopping/pantry/progress/family/pro), уровни `minimal/standard/active`, кулдауны.

**Использует**

- `care_settings`, `care_notifications`, `care_events`.

**Создаёт/изменяет**

- `care_notifications.status`, `sent_at`.
- `care_events.payload`.

**Зависит от**

- Состояния меню, покупок, остатков, прогресса, воды, белка.
- Subscription.features (`pro` уведомления — только PRO).

**Влияет на**

- Engagement.

---

## 11. Тарифы

**Что делает.** Определяет лимиты (генерации меню, Амы, max_profiles), фичи (`features.macros`, `features.weight_progress`, `features.ai_care`).

**Использует**

- `subscription_plans` (seed), `user_subscriptions`, `ai_usage_logs`.

**Создаёт**

- `user_subscriptions` (выбор тарифа).

**Изменяет**

- `menu_generations_used` (инкремент).
- `status` (trial → active → expired).

**Зависит от**

- `subscription_catalog.PLAN_SEEDS`.
- `subscription.assert_menu_generation_allowed`.

**Влияет на**

- Все AI-фичи (`require_ai_action`).
- Размер семьи (`max_profiles`).
- PRO-фичи (макросы, прогресс, ai_care).

---

## 12. Амы (внутренняя валюта)

**Что делает.** Внутренний биллинг для AI-действий. Каждое дорогостоящее AI-действие может списать Амы.

**Использует**

- `ama_wallets`, `ama_transactions`, `ai_usage_logs`.
- `AMA_COSTS` — словарь стоимостей.

**Создаёт**

- Записи `ama_transactions.type='spend'/'topup'`.
- `ai_usage_logs.ams_spent`.

**Изменяет**

- `ama_wallets.balance`.

**Зависит от**

- `subscription.require_ai_action` — проверка и списание.
- `subscription.is_family_billing` — определяет, чьим кошельком платить.

**Влияет на**

- Любая AI-фича: чат нутрициолога, замена блюда, OCR, voice, recipe analyze/improve, deep nutrition, ai_report, event_plan_ai, bot_parse_text.

---

## 13. Telegram Bot

**Что делает.** Главный канал «entry point» и быстрых действий: регистрация, приглашения, текст/voice/photo → покупки/запасы/остатки, реактивные уведомления, deep-link в TMA.

**Использует**

- `telegram_bot_sessions` (FSM: leftover, pending_confirm, etc.).
- `users.phone_number`, `family_invites`.
- AI (`bot_input._parse_with_ai`, `voice_input.transcribe_for_user`, `receipt_ocr.parse_receipt_image`).

**Создаёт**

- `meal_leftovers`, `family_shopping_lists.items_json`, `family_pantry_items` (через bot_pending).

**Изменяет**

- `users.phone_number`, `users.accepted_*`.
- `family_invites.status`.

**Зависит от**

- Telegram Bot API (`https://api.telegram.org/bot{token}/...`).
- AI для voice/receipt/text-parse.

**Влияет на**

- Все основные сущности через webapp deep-link и FSM.

---

## 14. Admin Panel

**Что делает.** Управление пользователями, семьями, подписками, Амами, OpenAI, просмотр ошибок.

**Использует**

- `admin_sessions`, `admin_actions`, `admin_login_attempts`, `admin_error_logs`.
- `users`, `families`, `user_subscriptions`, `ama_wallets`, `ai_usage_logs`.

**Создаёт**

- `admin_sessions` (PIN), `admin_actions` (audit log), `admin_error_logs` (через middleware).

**Изменяет**

- `users.is_blocked`, `is_deleted`, `phone_skipped`.
- `families.is_blocked`.
- `user_subscriptions.plan_code`.
- `ama_wallets.balance`.

**Зависит от**

- `ADMIN_TELEGRAM_IDS` в `settings`.
- PIN-сессии (token).

**Влияет на**

- Все домены — может править данные пользователя.

---

## 15. Схема связей модулей

```
                    ┌─────────────────────┐
                    │   user_profiles     │
                    │  (цель, диета, …)   │
                    └──────┬──────────────┘
                           │ owns
   ┌───────────────────────┴───────────────────────┐
   │                       │                       │
┌──┴───┐             ┌─────┴──────┐         ┌──────┴──────┐
│ Menu │◀──reads─────│ Pantry     │◀───────│ Leftovers   │
│      │             │ Shopping   │         └─────────────┘
│ Plan │──writes────▶│ list/sync  │
└──┬───┘             └─────┬──────┘
   │  selects               │ checks
   ▼                        ▼
┌────────────────┐  ┌────────────────────┐
│ Meal checkins  │  │ Subscription / AMA │
│ (факт)          │  │ require_ai_action  │
└────────┬───────┘  └─────────┬──────────┘
         │                    │ gate
         ▼                    ▼
┌────────────────────────────────┐
│        Nutritionist            │
│ advice + deferred + chat       │
│ deep-analysis (AI)             │
└────────┬───────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│        Progress             │
│ weight, training, target    │
└──────────┬──────────────────┘
           │
           ▼
┌─────────────────────────────┐
│    Care / Notifications     │
│ push reminders + scheduler  │
└──────────┬──────────────────┘
           ▼
┌─────────────────────────────┐
│        Telegram Bot         │
│ webhook + FSM + AI parse    │
│ entry point, quick add      │
└─────────────────────────────┘

┌───────────────┐
│   Family      │ ──┐  scope provider для всех ресурсов
│  + invites    │   │
└─────┬─────────┘   │
      ▼             │
┌──────────────┐    │
│ Admin panel  │ ◀──┘ управление всеми сущностями
└──────────────┘
```

**Ключевые перекрёстные зависимости**

1. Меню ↔ Покупки ↔ Запасы — треугольник синхронизации.
2. Подписка/Амы — поперечный gate-слой для AI.
3. Семья — scope, влияющий на меню/покупки/запасы/билинг.
4. Telegram bot — параллельный канал ко всем основным сущностям через FSM.
5. Care/Notifications — потребитель состояния всех других доменов.

---

## 16. Ключевые инварианты и edge cases

- **Один scope = один shopping_list.** Уникальный индекс на `user_id` (personal) и `family_id` (family).
- **Меню хранится в одной записи на scope.** При выборе нового — переписывается, sync_from_menu заменяет items_json.
- **Pantry авто-создание срабатывает только при `checked=true` и категории `is_food`.**
- **Family billing**: тариф `shared`/`family`/`pro` уже привязывает Амы к семье; personal-mode участник не может тратить.
- **Trial**: 14 дней + 20 генераций + 200 Амов.
- **Deferred advice**: уникальный индекс `(user_id, advice_key)` где `family_id IS NULL`.
- **Meal checkin**: `family_member_id` обязательный в family-режиме, в personal — `NULL`.
- **Multi-day**: `_meta.plan_days` хранит длительность; UI решает по `menuHasMultipleDays`.
- **Leftover status** при `eaten/discarded` обнуляет `portions_remaining`.
- **Voice/OCR/чат** — без Амов не работает; ошибка приходит после транскрипции (нельзя «дешёво» проверить).
- **`care_settings.timezone`** независим от `user_notification_settings.timezone`.
- **Onboarding** хранится локально + на сервере; локальное приоритетнее, если шаг новее.
