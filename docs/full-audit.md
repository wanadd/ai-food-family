# Полный аудит проекта ПланАм

Документ сформирован по состоянию репозитория `ai-food-family`. Описывает текущее состояние без изменений кода: экраны Telegram Mini App, навигацию, бизнес-логику, состояния, Telegram bot, таблицы БД, известные проблемы, кнопки, тарифы и предложения по упрощению.

> Стек: Next.js 14 (App Router, `apps/web`) + FastAPI / SQLAlchemy / PostgreSQL (`apps/api`) + Telegram bot (через webhook FastAPI, `apps/api/app/services/telegram_bot.py`).

---

## 1. Экраны приложения

Все экраны Telegram Mini App находятся в `apps/web/app/**/page.tsx` и оборачиваются `AppGate` → `AppModeProvider` → `AppShell` (`BottomNavigation` показывается для всех маршрутов, кроме `/onboarding` и `/admin/*`).

### 1.1 Главная — `/`

| Параметр | Значение |
|---|---|
| Файл | `apps/web/app/page.tsx` → `components/home/PlanAmHome.tsx` |
| Назначение | Сводка плана дня, перекрёстная навигация в основные разделы |
| Компоненты | `PlanAmHome`, `ProfileIcon` (внутренний SVG) |
| API | `GET /menus/selected`, `GET /shopping/list`, `GET /pantry` |
| Данные | Меню на сегодня (по `MenuVariant.meals`), `Купить N`, `Из запасов N`, число активных запасов, "скоро заканчиваются" |
| Кнопки | `→ Профиль` (`/profile`), `Открыть план` (`/menu`), `Открыть покупки` (`/shopping`), `Открыть` запасы (`/pantry`), `Составить план` (`/menu`) — при пустом плане |

### 1.2 Меню (хаб) — `/menu`

| Параметр | Значение |
|---|---|
| Файл | `app/menu/page.tsx` → `components/menu/MenuHub.tsx` |
| Назначение | Сводка плана, "ПланАм рекомендует", быстрые действия, ссылки в подэкраны |
| Компоненты | `MenuHub`, `ScreenLayout`, `ProtectedScreenFallback`, `PageLoading` |
| API | `GET /menus/overview`, `POST /menus/overview/quick-action` |
| Данные | `plan_summary` (цель, персоны, стоимость, экономия), `nutritionist_advice`, `today_meals`, `home_attendance`, `settings_summary`, `meal_leftovers_count` |
| Кнопки | `Составить меню` (`/menu/generate`), `Обновить меню`, быстрые действия (`cheaper`, `more_pantry`, `more_protein`, `less_cooking_time`, `replace_dish`), `Подробнее →` / `Открыть все дни →` (`/menu/current`), `Изменить на сегодня →` (`/menu/settings`), `Текущее меню` (`/menu/current`), `Остатки блюд` (`/menu/leftovers`), `Рецепты` (`/recipes`), `Повторить` / `На главную` (`/`) |

### 1.3 Мастер генерации — `/menu/generate`

| Параметр | Значение |
|---|---|
| Файл | `app/menu/generate/page.tsx` → `components/menu/MenuPlanner.tsx` (+ `MenuWizardSteps`, `MenuChooseVariants`, `MenuVariantCard`, `StickyBottomBar`) |
| Назначение | 4–5 шагов мастера, генерация трёх вариантов меню, выбор варианта |
| Компоненты | `MenuPlanner`, `MenuWizardSteps`, `MenuChooseVariants`, `MenuVariantCard`, `MenuPlannerSection`, `StickyBottomBar` |
| API | `GET /nutrition/profile`, `GET /menus/selected`, `GET /pantry`, `POST /menus/generate`, `POST /menus/select` |
| Данные | Выбор цели, персон (только family), дней, бюджета, режима, чеклист "что учтёт ПланАм", три варианта |
| Кнопки | `← Меню`, `← Назад к настройкам`, `Продолжить` / `Сгенерировать меню`, `Назад`, `Выбрать вариант` (через `MenuVariantCard`), `← Назад к выбору`, `Тариф и Амы →` (`/subscription`), статус-плашки `Учтено / Не заполнено / Добавить` |

### 1.4 Текущий план — `/menu/current`

| Параметр | Значение |
|---|---|
| Файл | `app/menu/current/page.tsx` → `components/menu/MenuCurrentView.tsx` |
| Назначение | Просмотр выбранного меню по дням, замена блюд, чекины приёмов пищи |
| Компоненты | `MenuCurrentView`, `MenuVariantCard`, `MenuDayPicker`, `MealCheckinPanel`, `ReplaceDishModal` |
| API | `GET /menus/selected`, `POST /menus/replace-dish`, `POST /menus/select`, `GET /meal-checkins/today`, `POST /meal-checkins` |
| Данные | Меню, дни (`plan_days`, `days[]`), блюда по `meal_type`, статус чекина, член семьи |
| Кнопки | `← Меню`, `Настроить план` (`/menu`), переключатели дней, `Заменить блюдо`, опции чекина (`ate_home`, `ate_work`, `ate_cafe`, `ate_restaurant`, `ate_delivery`, `ate_other`), `Остатки блюд` (`/menu/leftovers`) |

### 1.5 Остатки блюд — `/menu/leftovers`

| Параметр | Значение |
|---|---|
| Файл | `app/menu/leftovers/page.tsx` → `components/menu/MealLeftoversPage.tsx` |
| Назначение | Учёт остатков: добавление, статусы (`active`, `eaten`, `frozen`, `expired`), удаление |
| Компоненты | `MealLeftoversPage` |
| API | `GET /meal-leftovers`, `POST /meal-leftovers`, `PATCH /meal-leftovers/{id}`, `DELETE /meal-leftovers/{id}` |
| Данные | Название блюда, порции, срок, статус, кто добавил |
| Кнопки | `+ Добавить`, статусы (`Доедено`, `В морозилку`, `Испорчено`), `Удалить`, `Сохранить`, `↑ К покупкам`, `← Меню` |

### 1.6 Настройки меню — `/menu/settings`

| Параметр | Значение |
|---|---|
| Файл | `app/menu/settings/page.tsx` → `components/menu/MenuSettingsPage.tsx` |
| Назначение | Override персон, режим плана, локальное сохранение |
| Компоненты | `MenuSettingsPage`, `StickyBottomBar` |
| API | — (только `localStorage`) |
| Данные | `planMode`, `personsOverride` |
| Кнопки | Чекбокс override, кнопки персон, режимов плана, `Сохранить` |

### 1.7 Меню → Рецепты (редирект) — `/menu/recipes`

| Параметр | Значение |
|---|---|
| Файл | `app/menu/recipes/page.tsx` |
| Назначение | `next/navigation.redirect("/recipes")` |
| Кнопки | — |

### 1.8 Событие — `/menu/event`

| Параметр | Значение |
|---|---|
| Файл | `app/menu/event/page.tsx` |
| Назначение | План на застолье/мероприятие (черновик, без входов из UI) |
| API | `POST /event-plans`, `POST /event-plans/{id}/shopping` |
| Кнопки | Заполнение формы, `Сгенерировать`, `Добавить в покупки`, `← Меню` |

### 1.9 Покупки — `/shopping`

| Параметр | Значение |
|---|---|
| Файл | `app/shopping/page.tsx` → `components/shopping/ShoppingListView.tsx` |
| Назначение | Список покупок: категории, чек/анчек, синхронизация с пантри, добавление товаров и категорий |
| Компоненты | `ShoppingListView`, `ShoppingCategorySection`, `ShoppingItemSheet`, `ShoppingCategorySheet`, `CategoryPicker`, `BotQuickInputHint`, `ModeBanner` |
| API | `GET /shopping/list`, `POST /shopping/items`, `PATCH /shopping/items/{id}`, `DELETE /shopping/items/{id}`, `PATCH /shopping/items/{id}/toggle`, `POST /shopping/sync`, `GET/POST /shopping/categories` |
| Данные | Список товаров (`name`, `category`, `quantity`, `unit`, `checked`, `checked_by_name`), пользовательские категории |
| Кнопки | `+ Добавить`, `Категория`, чекбокс товара, `Изменить`, `Удалить`, `Синхронизировать`, поиск, `Скрыть купленные`, развернуть/свернуть категорию, `← На главную` |

### 1.10 Запасы — `/pantry`

| Параметр | Значение |
|---|---|
| Файл | `app/pantry/page.tsx` → `components/pantry/PantryDashboard.tsx` |
| Назначение | Запасы дома, фильтры, добавление/редактирование |
| Компоненты | `PantryDashboard`, `PantryCategorySection`, `PantryItemRow`, `PantryItemForm`, `BotQuickInputHint`, `ModeBanner` |
| API | `GET /pantry`, `POST /pantry`, `PATCH /pantry/{id}`, `DELETE /pantry/{id}` |
| Данные | Активные позиции, `expires_at`, `days_until_expiry`, `source` (manual/shopping_list), категории |
| Кнопки | `+ Добавить`, фильтры (`Все / Скоро / Недавно / Из покупок / Вручную`), `Сохранить`, `Удалить`, `↑ К покупкам` |

### 1.11 Рецепты — `/recipes`

| Параметр | Значение |
|---|---|
| Файл | `app/recipes/page.tsx` → `components/recipes/RecipeCatalog.tsx` (+ секции) |
| Назначение | Каталог рецептов, поиск, чипы приёмов пищи, секции |
| API | `GET /recipes`, `GET /recipes/filters`, `POST /recipes/{id}/favorite` |
| Кнопки | Поиск, чипы (`Завтрак`, `Обед`, `Ужин`, `Перекус`), `Показать ещё`, `В избранное`, переход к карточке (`/recipes/[id]`) |

### 1.12 Карточка рецепта — `/recipes/[id]`

| Файл | `app/recipes/[id]/page.tsx` → `components/recipes/RecipeDetailModal.tsx` |
| API | `GET /recipes/{id}`, `POST /recipes/{id}/favorite`, `POST /recipes/{id}/add-to-shopping`, `GET /recipes/{id}/evaluate`, `GET /recipes/{id}/family-compatibility`, `GET /recipes/{id}/improve`, `POST /recipes/{id}/add-to-menu` |
| Кнопки | `← Каталог`, `В избранное`, `В покупки`, `В меню`, `Улучшить`, `Совместимость` |

### 1.13 Нутрициолог — `/nutritionist`

| Параметр | Значение |
|---|---|
| Файл | `app/nutritionist/page.tsx` → `components/nutritionist/NutritionistDashboard.tsx` |
| Назначение | План и факт КБЖУ, прогресс цели, вода, советы, отложенные рекомендации, быстрые действия |
| Компоненты | `NutritionistDashboard`, `NutritionistAdviceCard`, `WaterIntakePanel`, `CareTelegramLinkCard` |
| API | `GET /nutrition/profile`, `GET /menus/selected`, `GET /pantry`, `GET /progress/overview`, `GET /subscription/overview`, `GET /nutritionist/water/today`, `POST /nutritionist/water`, `GET/POST/PATCH/DELETE /nutritionist/deferred-advice`, `GET /nutritionist/deferred-advice/suppressed-titles` |
| Кнопки | `Открыть профиль`, `Добавить вес`, `Добавить тренировку`, `Изменить цель`, `Спросить нутрициолога` (`/nutritionist/chat`), `Добавить в меню`, `Найти рецепт`, `Добавить в покупки`, `Не сейчас` (отложить совет), `Выполнить` / `Вернуть` / `Удалить` для отложенных, `+ стакан воды`, `Отметить, где поели →` |

### 1.14 Чат с нутрициологом — `/nutritionist/chat`

| Файл | `app/nutritionist/chat/page.tsx` → `components/nutritionist/NutritionistChat.tsx` |
| API | `POST /nutritionist/ask`, `GET /subscription/overview` |
| Кнопки | `Спросить` (списание AMA), `← Нутрициолог`, `/subscription` |

### 1.15 Забота (care) — `/nutritionist/care` и `/settings/care`

| Файл | `app/nutritionist/care/page.tsx`, `app/settings/care/page.tsx` → `components/care/CareSettingsPanel.tsx` |
| API | `GET /care/settings`, `PATCH /care/settings`, `POST /care/settings/test` |
| Кнопки | Режимы (`minimal`, `standard`, `active`), переключатели типов уведомлений (`water`, `protein`, `menu`, `shopping`, `pantry`, `progress`, `family`, `pro`), `Отправить тест`, `Сохранить` |

### 1.16 Профиль — `/profile`

| Файл | `app/profile/page.tsx` → `components/profile/ProfileDashboard.tsx` |
| Кнопки | `→ Настройки`, `Питание` (`/profile/nutrition`), `Семья` (`/family`), `Подписка` (`/subscription`), `Прогресс` (`/progress`), `Уведомления` (`/notifications`), `О приложении` (`/settings/about`), переключатель режима (личный/семейный) |

### 1.17 Питание (профиль) — `/profile/nutrition`

| Файл | `app/profile/nutrition/page.tsx` → `components/nutrition-profile/NutritionProfileForm.tsx` |
| API | `GET /nutrition/profile`, `POST /nutrition/profile` |
| Кнопки | Аккордеоны секций, чипы целей/диет/аллергий, поля веса/роста/возраста, `Сохранить` (`router.replace(returnTo)`) |

### 1.18 Прогресс — `/progress`

| Файл | `app/progress/page.tsx` → `components/progress/ProgressDashboard.tsx` |
| API | `GET /progress/overview`, `POST /progress/entries`, `POST /progress/trainings`, `PATCH /progress/privacy` |
| Кнопки | `+ Добавить вес`, `+ Добавить тренировку`, `Скрыть для семьи / Показать`, поля формы, `Сохранить`, `Отмена` |

### 1.19 Подписка — `/subscription`

| Файл | `app/subscription/page.tsx` → `components/subscription/SubscriptionDashboard.tsx` |
| API | `GET /subscription/overview`, `POST /subscription/select` |
| Кнопки | По каждому тарифу `Выбрать`, ссылка `← Профиль` |

### 1.20 Семья — `/family`

| Файл | `app/family/page.tsx` → `components/family/FamilyDashboard.tsx` |
| API | `GET /families/me`, `POST /families`, `PATCH /families/{id}`, `POST /families/{id}/members`, `PATCH /families/{id}/members/{member_id}`, `DELETE /families/{id}/members/{member_id}`, `POST /families/{id}/invites`, `POST /families/{id}/virtual-members`, `PATCH /families/me/allow-admin-edit` |
| Компоненты | `FamilyDashboard`, `MemberCard`, `MemberForm`, `AddPersonSheet`, `InviteSheet`, `FamilyManageSheet`, `VirtualMemberNutritionForm`, `RoleBadge` |
| Кнопки | `+ Добавить участника`, `Пригласить`, `Виртуальный участник`, `Редактировать`, `Удалить`, `Передать админа`, `Открыть профиль питания`, `Сохранить`, `Отмена`, переключатель `allow_admin_profile_edit` |

### 1.21 Уведомления — `/notifications`

| Файл | `app/notifications/page.tsx` → `components/notifications/NotificationSettingsForm.tsx` |
| API | `GET /notifications/settings`, `PATCH /notifications/settings` |
| Кнопки | Переключатели (покупки / завтрак / обед / ужин), поля времени, выбор `timezone`, `Сохранить` |

### 1.22 Настройки — `/settings`

| Файл | `app/settings/page.tsx` |
| Кнопки | `/settings/account`, `/settings/care`, `/settings/units`, `/settings/documents`, `/settings/delete-data`, `/settings/privacy`, `/settings/language`, `/settings/support`, `/settings/about` |

### 1.23 Поднастройки

| Маршрут | Файл | Назначение |
|---|---|---|
| `/settings/account` | `app/settings/account/page.tsx` | Данные Telegram, ссылка на бот |
| `/settings/care` | см. 1.15 | Дублирует `/nutritionist/care` |
| `/settings/units` | `SettingsPlaceholder` | Заглушка |
| `/settings/documents` | `app/settings/documents/page.tsx` | Документы / правовые |
| `/settings/delete-data` | `app/settings/delete-data/page.tsx` | Запрос удаления данных |
| `/settings/privacy` | `SettingsPlaceholder` | Заглушка |
| `/settings/language` | `SettingsPlaceholder` | Заглушка |
| `/settings/support` | `app/settings/support/page.tsx` | Ссылка в Telegram бот, на `/notifications` |
| `/settings/about` | `app/settings/about/page.tsx` | О приложении |

### 1.24 Онбординг — `/onboarding`

| Файл | `app/onboarding/page.tsx` → `components/onboarding/OnboardingWizard.tsx` |
| API | `POST /onboarding/answers`, `GET /onboarding/state` |
| Кнопки | Чипы выборок, текстовые поля, `Далее`, `Назад`, `Завершить`, `Пропустить` |

### 1.25 Админка — `/admin/*`

| Маршрут | Компонент | Назначение |
|---|---|---|
| `/admin` | `AdminDashboard` | Сводка, табы: пользователи, семьи, подписки, Амы |
| `/admin/users` / `/admin/users/[id]` | `AdminUsersList` / `AdminUserDetailPage` | Поиск, блок/разблок, выдача подписки/Амов |
| `/admin/families` / `/admin/families/[id]` | `AdminFamiliesList` / `AdminFamilyDetailPage` | Семьи, выдача Амов на семью |
| `/admin/subscriptions` | `AdminSubscriptionsPage` | Тарифы, активные подписки |
| `/admin/ams` | `AdminAmsPage` | Транзакции, балансы |
| `/admin/errors` | `AdminErrorsPage` | Серверные ошибки |
| `/admin/openai` | `AdminOpenAiPage` | Конфигурация AI, лог использования |
| API | `GET/POST /admin/*` (см. `apps/api/app/routers/admin.py`) |

---

## 2. Навигация приложения

Нижняя панель (`components/layout/BottomNavigation.tsx`):

```
Нутрициолог · Меню · ПланАм · Покупки · Запасы
```

Вход в Профиль — через иконку в шапке главной (`/`). Полное дерево с учётом всех вложенных экранов:

```
Главная (/)
├── Меню (/menu)
│   ├── /menu/generate         мастер
│   ├── /menu/current          текущий план + дни
│   ├── /menu/leftovers        остатки блюд
│   ├── /menu/settings         настройки меню (override)
│   ├── /menu/recipes          → редирект на /recipes
│   └── /menu/event            событие (не в UI)
├── Покупки (/shopping)
├── Запасы (/pantry)
├── Нутрициолог (/nutritionist)
│   ├── /nutritionist/chat
│   └── /nutritionist/care
└── Профиль (/profile)
    ├── /profile/nutrition     профиль питания
    ├── /family                семья
    ├── /subscription          тариф + Амы
    ├── /progress              вес, тренировки, цель
    ├── /notifications         буду готовить / куплю
    ├── /settings              хаб настроек
    │   ├── /settings/account
    │   ├── /settings/care     (дубль /nutritionist/care)
    │   ├── /settings/units    (stub)
    │   ├── /settings/documents
    │   ├── /settings/delete-data
    │   ├── /settings/privacy  (stub)
    │   ├── /settings/language (stub)
    │   ├── /settings/support
    │   └── /settings/about
    └── /recipes               (доступен также из /menu и /nutritionist)
        └── /recipes/[id]

Отдельные потоки:
/onboarding                    мастер первичных вопросов
/admin/**                      админка (без нижней панели)
```

---

## 3. Бизнес-логика

### 3.1 Создание меню

`apps/api/app/services/menu.py::generate_menus_for_scope`:

1. UI собирает payload `MenuGenerateRequest`: `nutrition_goal`, `plan_days`, `persons_count`, `plan_mode`, опционально `drink_mode`, `allow_alcohol`.
2. `build_menu_context` собирает контекст: профиль питания, семья, остатки, запасы, виртуальные участники.
3. `subscription.assert_menu_generation_allowed` проверяет лимит тарифа; при необходимости — списывает Амы (`menu_generation_extra`).
4. `menu_ai.generate_menus` обращается к OpenAI: возвращает три варианта (`quick`, `economy`, `balanced`).
5. Если AI вернул один день, а `plan_days > 1` — `menu_days.expand_variant_to_plan_days` достраивает дни из БД рецептов (`day_label`, `date_iso`).
6. `subscription.commit_menu_generation` инкрементит `menu_generations_used` и пишет `ai_usage_logs`.
7. После `POST /menus/select` (`menu.select_menu`) сохраняется `FamilyMenuSelection` (личный — по `user_id`, семейный — по `family_id`).
8. `shopping_list_service.sync_from_menu` синхронизирует список покупок и в фоне может уведомить через care (`care_service.maybe_notify_menu_ready`).
9. На фронте — редирект `/menu/current?saved=1` с баннером «Меню сохранено».

### 3.2 Список покупок

`apps/api/app/services/shopping_list.py`:

1. Хранится в `family_shopping_lists` (одна запись на user/family, `items_json` — массив). Категории — `shopping_categories` (системные + пользовательские).
2. После генерации меню `sync_from_menu` мерджит ингредиенты в `items_json` (через `shopping_item_utils.item_from_menu_ingredient` и `_sort_items`).
3. Фронт `ShoppingListView` поллит каждые 4 с (`updated_at` как кеш-ключ). `POST /shopping/items` использует `suggestCategorySlug` (клиент) + `normalize_category` (сервер).
4. При `PATCH /shopping/items/{id}/toggle(checked=true)` товар автоматически дублируется в запасы через `pantry_shopping.add_or_merge_from_shopping` (если категория `is_food`).

### 3.3 Запасы

`apps/api/app/services/pantry.py`:

1. Таблица `family_pantry_items` (привязка к `user_id` или `family_id`). Поля: `name`, `quantity`, `unit`, `category`, `source` (`manual` / `shopping_list`), `expires_at`, `note`.
2. `infer_category` подставляет категорию по имени.
3. `pantry_shopping.add_or_merge_from_shopping` ищет существующую позицию (`find_matching_pantry_item`) и складывает количества (через `amount_parser`).
4. Срок хранения: при отсутствии `expires_at` показываем `999`; иначе высчитываем дни до истечения, `is_expired = days < 0`.

### 3.4 Остатки блюд

`apps/api/app/services/meal_leftovers.py`:

1. Таблица `meal_leftovers`: `dish_name`, `portions_remaining`, `valid_until`, `note`, `leftover_status` (`active`, `eaten`, `frozen`, `expired`).
2. Создание — через UI `/menu/leftovers`, Telegram bot (`MENU_QUICK_ADD → 🍲 Остатки блюда`) или из чекина со статусом `saved_as_leftover`.
3. `meal_overview` использует количество активных остатков (`meal_leftovers_count`) в обзоре меню.

### 3.5 Нутрициолог

`apps/api/app/services/nutritionist.py` + `services/deferred_advice.py`:

1. Совет формируется на основе профиля питания, остатков, запасов, цели и факта дня — `pickMainAdvice` (фронт) + `nutritionist_service` (бэкенд для `MenuOverview.nutritionist_advice`).
2. Отложенные советы хранятся в `deferred_nutrition_advice` со статусами `deferred` / `completed` / `dismissed`. Кнопки UI:
   - `Вернуть` → `DELETE` (запись удаляется, совет может появиться снова).
   - `Выполнить` → `PATCH status=completed` (хранится, скрывается из активных через `suppressed-titles`).
   - `Удалить` → `PATCH status=dismissed`.
3. Чат: `POST /nutritionist/ask` списывает Амы (`nutritionist_ask`), пишет лог в `ai_usage_logs`.
4. Вода: `water_intake_logs` по `(user_id, log_date)`, сумма за сегодня учитывается в KPI.

### 3.6 Прогресс

`apps/api/app/services/progress.py`:

1. Таблицы `progress_entries` (вес, замеры) и `training_entries` (тип, длительность, интенсивность).
2. `goal_progress_percent`: для `lose` — `(start − current) / (start − target)`; для `gain` — обратная формула; для `maintain`/`healthy` — `50 + (start − current) * 10`.
3. PRO-фичи (`macros`, `weight_progress`) гейтятся через `subscription.user_has_pro`.
4. UI после сохранения веса/тренировки остаётся на `/progress`, обновляет данные `await load()`.

### 3.7 Семья

`apps/api/app/services/family.py` + `family_invites.py`:

1. Таблицы `families`, `family_members` (роль `admin` / `adult` / `child`, `is_virtual`, `nutrition_profile`).
2. Приглашение по телефону — `FamilyInvite` со статусом `pending` / `accepted` / `declined`. Альтернатива — invite-link с deep-link `start=invite_<token>` (для Telegram, у кого ещё нет аккаунта).
3. Виртуальные участники — без user_id, добавляются админом. Поле `allow_admin_profile_edit` управляет, может ли админ редактировать профиль участника.
4. Режимы `personal` / `family` хранятся в `user_preferences.active_mode`, переключение влияет на scope всех ресурсов.

### 3.8 Уведомления

Два параллельных потока:

1. **Cook/Buy reminders** (`user_notification_settings`, `notifications.py`): фиксированные времена `cook_breakfast_time`, `cook_lunch_time`, `cook_dinner_time`, `buy_reminder_time`. Шедулер `notification_scheduler.py` отправляет через Telegram bot.
2. **Care system** (`care_settings`, `care_notifications`, `care_events`, `care.py`): уровни `minimal` / `standard` / `active`, типы (`water`, `protein`, `menu`, `shopping`, `pantry`, `progress`, `family`, `pro`), кулдауны на каждый тип. Шедулер генерирует и рассылает уведомления, ведёт `last_*_sent_date`.

### 3.9 Тарифы

`apps/api/app/services/subscription.py` + `subscription_catalog.py`:

1. План в `subscription_plans` (seed `PLAN_SEEDS`). Активная подписка пользователя — `user_subscriptions` (`status`, `trial_ends_at`, `current_period_ends_at`, `menu_generations_used`).
2. Trial — 14 дней, до 20 генераций, 200 Амов.
3. `assert_menu_generation_allowed` проверяет лимит; превышение → `HTTPException` с кодом `menu_generation_limit` и опцией оплаты Амами.
4. PRO-функции открываются через `features.macros` / `features.weight_progress` и т. п.

### 3.10 Амы (внутренняя валюта)

1. Кошелёк — `ama_wallets` (на пользователя или семью). Транзакции — `ama_transactions` (`type` = `topup` / `spend`, `reason`).
2. Стоимости в `AMA_COSTS` (см. таблицу в разделе 9).
3. Любое AI-действие проходит через `subscription.require_ai_action(action, ama_cost)` — списывает Амы при превышении лимитов плана. `log_ai_usage` пишет в `ai_usage_logs`.

---

## 4. Состояния приложения

### 4.1 Данные в базе (PostgreSQL)

Полный список таблиц — см. раздел 6. Основные группы:

- **Пользователи и доступ**: `users`, `user_preferences`, `user_profiles`, `admin_sessions`, `admin_actions`, `admin_login_attempts`, `admin_error_logs`.
- **Семья**: `families`, `family_members`, `family_invites`, `meal_eating_schedules`.
- **План и меню**: `family_menu_selections`, `family_shopping_lists`, `family_pantry_items`, `shopping_categories`, `meal_leftovers`, `meal_checkins`, `event_plans`.
- **Рецепты**: `recipes`, `recipe_ingredients`, `recipe_steps`, `recipe_tags`, `recipe_allergens`, `recipe_restrictions`, `recipe_ratings`, `recipe_import_jobs`.
- **Подписки и Амы**: `subscription_plans`, `user_subscriptions`, `ama_wallets`, `ama_transactions`, `ai_usage_logs`.
- **Прогресс и нутрициолог**: `progress_entries`, `training_entries`, `nutrition_targets`, `deferred_nutrition_advice`, `water_intake_logs`.
- **Уведомления / care**: `user_notification_settings`, `care_settings`, `care_notifications`, `care_events`.
- **Telegram bot**: `telegram_bot_sessions`.

### 4.2 Локальное хранилище (browser/Telegram)

`localStorage`:
- `planam_app_mode` — выбранный режим (`personal` / `family`).
- `planam_plan_mode` — режим плана меню.
- `planam_persons_override` — переопределение числа персон.
- `planam_deferred_advice` — устаревший кэш отложенных советов (мигрируется в API при загрузке нутрициолога).
- `planam_dev_init_data` — dev-режим без Telegram.

Кэш React-state хранится в провайдерах (`TelegramProvider`, `AppModeProvider`) и страничных компонентах.

### 4.3 Данные из API

Запросы идут через `apiFetch` / `apiGet` (`lib/api-client.ts`) с заголовками `X-Telegram-Init-Data` и `X-App-Mode`. Базовый URL — `lib/api-base.ts::getApiBaseUrl()` (`NEXT_PUBLIC_API_URL` или fallback `https://planam.ru/api`).

Главные эндпоинты:
- `/auth/telegram`, `/auth/dev-login`
- `/users/me`, `/users/app-context`, `/users/app-mode`
- `/onboarding/state`, `/onboarding/answers`
- `/nutrition/profile`
- `/menus/generate`, `/menus/replace-dish`, `/menus/select`, `/menus/selected`, `/menus/overview`, `/menus/overview/quick-action`
- `/meal-checkins/today`, `/meal-checkins`
- `/meal-leftovers`
- `/shopping/list`, `/shopping/items`, `/shopping/items/{id}`, `/shopping/items/{id}/toggle`, `/shopping/sync`, `/shopping/categories`
- `/pantry`
- `/recipes`, `/recipes/{id}`, `/recipes/{id}/favorite`, `/recipes/{id}/add-to-shopping`, `/recipes/{id}/evaluate`, `/recipes/{id}/improve`, `/recipes/{id}/family-compatibility`, `/recipes/{id}/add-to-menu`, `/recipes/filters`
- `/nutritionist/ask`, `/nutritionist/water`, `/nutritionist/water/today`, `/nutritionist/deferred-advice` (CRUD + suppressed-titles)
- `/progress/overview`, `/progress/entries`, `/progress/trainings`, `/progress/privacy`
- `/notifications/settings`
- `/care/settings`, `/care/settings/test`
- `/families/me`, `/families/{id}/members`, `/families/{id}/invites`, `/families/{id}/virtual-members`, `/families/me/allow-admin-edit`
- `/subscription/overview`, `/subscription/select`
- `/event-plans`, `/event-plans/{id}/shopping`
- `/admin/*`
- `/telegram/webhook`, `/bot/webhook`, `/telegram/webhook/info`, `/telegram/webhook/url`
- `/legal/documents`

---

## 5. Telegram Bot

Webhook принимается FastAPI: `POST /telegram/webhook` и алиас `POST /bot/webhook` (`apps/api/app/routers/telegram_bot.py`). Логика — `apps/api/app/services/telegram_bot.py`.

### 5.1 Команды

| Команда | Где обрабатывается | Что делает |
|---|---|---|
| `/start` | `handle_start` | Регистрация пользователя, маршрутизация (legal → phone → main menu); поддерживает deep-link `?start=invite_<token>` и `?start=invite` |
| `/help` | блок «commands» в `process_telegram_update` | Шлёт `BOT_COMMANDS_HELP` и главное меню |
| `/invite +79001234567` | `handle_invite_command` | Создаёт `FamilyInvite` (только админ семьи) |
| `/admin` | `admin_bot.handle_admin_command` | Вход в админ-режим (выдача PIN-сессии) |

Кнопки нижнего reply-меню (`bot_menu.py`):

| Кнопка | Действие |
|---|---|
| 🏠 Сегодня | `build_today_summary` — сводка дня |
| 🍽 Моё меню | `web_app /menu` |
| 🛒 Покупки | `web_app /shopping` |
| 📦 Запасы | `web_app /pantry` |
| 🥗 Нутрициолог | `web_app /nutritionist` |
| ⚡ Быстро добавить | inline-меню (`quick:voice_hint`, `quick:receipt_hint`, `web_app /shopping`, `web_app /pantry`, `quick:leftover`) |
| 👨‍👩‍👧 Семья | `web_app /family` |
| ⚙ Настройки | `web_app /settings` + `/settings/documents` |

Inline-callback'и:

| `callback_data` | Действие |
|---|---|
| `quick:voice_hint` / `quick:receipt_hint` / `quick:leftover` / `quick:back` | подсказки и сценарий остатков |
| `accept_family_invite:<id>` / `decline_family_invite:<id>` | приём/отклонение приглашения |
| `create_family_invite_link` | генерация invite-link для админа семьи |
| `legal_*` (см. `bot_registration.handle_legal_callback`) | согласие/отказ от документов |
| `phone:skip` | пропуск телефона |
| `pending:*` (см. `bot_pending`) | подтверждение распознанных голосом/чеком товаров |

### 5.2 Сценарии общения

#### 5.2.1 Первый запуск

1. **Начало.** `/start` без payload.
2. **Шаги.** Создание `User`, проверка `legal_consent` → отправка документов; согласие → запрос номера (`request_contact`); получение → пометка `phone_number`, отправка пакета pending-приглашений; редирект в Mini App (inline кнопка `Открыть ПланАм`).
3. **Завершение.** `send_registration_complete` → главное reply-меню.
4. **Ошибки.** Отказ от документов → `Доступ временно ограничен`. Несоответствие телефона приглашению → `show_invite_mismatch`.

#### 5.2.2 Deep-link приглашение

1. **Начало.** `/start invite_<token>` (или `?startapp=`).
2. **Шаги.** Если есть legal+phone → `process_deep_link_invite` → подтверждение/отказ. Иначе сохраняется в `bot_session.invite_token`, запрашиваются документы/телефон.
3. **Завершение.** `accept_family_invite` → запись `FamilyMember`, уведомление приглашающего.
4. **Ошибки.** Истёкшая ссылка → «Приглашение не найдено или уже обработано». Несоответствие телефона — мисматч.

#### 5.2.3 Быстрое добавление текстом

1. **Начало.** Любой текст после регистрации.
2. **Шаги.** `bot_input.process_text_message` → `parse_message`. Если паттерн не распознан — `_parse_with_ai` (списывает `bot_parse_text` Амы). При успехе формируется `pending`-список → пользователь подтверждает callback'ом.
3. **Завершение.** `pantry.add_item` / `shopping.add_item` / `meal_leftovers.create_leftover`.
4. **Ошибки.** AI выключен или Амы кончились → сообщение «Уточните список текстом», главное меню.

#### 5.2.4 Голосовое сообщение

1. **Начало.** `voice` в апдейте.
2. **Шаги.** `download_telegram_file` → `voice_input.transcribe_for_user` (Whisper / fallback заглушка). Распознанный текст идёт через `_parse_with_ai`.
3. **Завершение.** Pending-подтверждение (как в 5.2.3) или leftover-сценарий.
4. **Ошибки.** Ошибка загрузки/распознавания → `VOICE_STUB`; нет Амов → `Не хватает Амов`.

#### 5.2.5 Фото чека

1. **Начало.** `photo` в апдейте.
2. **Шаги.** `download_telegram_file` → `receipt_ocr.parse_receipt_image` (через AI, списывает `ocr_receipt`). Получив строки чека — складывает в pending.
3. **Завершение.** Пользователь подтверждает позиции → добавление в покупки/запасы.
4. **Ошибки.** OCR не справился → `RECEIPT_STUB_MESSAGE`. Нет Амов → подсказка с web-app кнопкой.

#### 5.2.6 Сценарий остатков (`quick:leftover`)

1. **Начало.** Callback `quick:leftover` → состояние `STATE_LEFTOVER_DISH`.
2. **Шаги.** Бот спрашивает «Что осталось?» → запоминает; «Сколько порций?» → читает число.
3. **Завершение.** `meal_leftovers.create_leftover` → подтверждение «Сохранено».
4. **Ошибки.** Слишком короткое название («Укажите название блюда»), не число / вне диапазона 1–50 («Введите число порций»).

#### 5.2.7 Приглашение в семью (админ)

1. **Начало.** Команда `/invite +79...` или кнопка «Пригласить в семью».
2. **Шаги.** Проверка прав (`FamilyRole.ADMIN`). Если по номеру — `create_invite`, иначе `create_link_invite`. Бот отправляет inline-кнопку «Принять / Отклонить» приглашаемому (если он уже зарегистрирован) или ссылку для пересылки.
3. **Завершение.** `accept_family_invite` создаёт `FamilyMember`; уведомление обоим.
4. **Ошибки.** Не админ → «Приглашать может только администратор». Лимит профилей по тарифу → ошибка из `family_invites.create_invite`.

#### 5.2.8 «Сегодня»

1. **Начало.** Кнопка `🏠 Сегодня`.
2. **Шаги.** `build_today_summary`: меню, остаток покупок, заканчивающиеся продукты, прогресс цели.
3. **Завершение.** Сообщение со сводкой + reply-меню.
4. **Ошибки.** Если данных нет — выводится прочерк («приёмов пищи: —»).

### 5.3 Блокировки и ошибки

- `is_blocked` или `is_deleted` пользователь → «Доступ временно ограничен».
- Блокировка семьи → то же.
- Любая ошибка в `process_telegram_update` логируется и не пробрасывается наверх (бот возвращает `{ok: true}`).

---

## 6. Таблицы базы данных

Реализованы через SQLAlchemy ORM (`apps/api/app/models/*.py`) + `database_migrations.py` (idempotent `CREATE TABLE IF NOT EXISTS`).

### 6.1 Пользователи и доступ

**`users`** — учётка Telegram.
- Поля: `id`, `telegram_id` (uniq), `username`, `first_name`, `last_name`, `language_code`, `phone_number`, `photo_url`, `accepted_terms`, `accepted_privacy`, `accepted_personal_data`, `legal_accepted_at`, `legal_documents_version`, `phone_skipped`, `is_blocked`, `blocked_at`, `blocked_reason`, `is_deleted`, `deleted_at`, `deleted_by_admin_id`, `created_at`, `updated_at`.
- Связи: `profile` (1:1), `family_membership` (1:1), `notification_settings` (1:1), `preferences` (1:1), `recipe_favorites` (1:N).

**`user_profiles`** — детальный профиль питания.
- `user_id` (uniq), `age`, `gender`, `height_cm`, `weight_kg`, `nutrition_goal`, `activity_level`, `medical_restrictions`, `banned_foods`, `dish_complexity`, `pro_data` (JSONB), `goal_details` (JSONB).

**`user_preferences`** — активный режим (personal/family).
- `user_id` (uniq), `active_mode`, `updated_at`.

**`user_notification_settings`** — расписание уведомлений.
- `user_id`, `buy_reminder_enabled/time`, `cook_reminder_enabled/time`, `cook_breakfast_*`, `cook_lunch_*`, `cook_dinner_*`, `last_*_sent_date`, `timezone`.

**`admin_sessions` / `admin_login_attempts` / `admin_actions` / `admin_error_logs`** — админка.

### 6.2 Семья

**`families`** — `id`, `name`, `is_blocked`, `blocked_*`.
**`family_members`** — `family_id`, `user_id` (nullable), `display_name`, `role`, `goals`, `restrictions`, `is_virtual`, `virtual_kind`, `allow_admin_profile_edit`, `nutrition_profile` (JSONB).
**`family_invites`** — `family_id`, `invited_phone_normalized`, `invited_user_id`, `invited_by_user_id`, `status`, `invite_token` (uniq).
**`meal_eating_schedules`** — расписание «где ест» член семьи (`family_member_id` uniq, `schedule_json`).

### 6.3 План, покупки, запасы

**`family_menu_selections`** — выбранное меню (personal: `user_id`, family: `family_id`); `variant`, `menu_data` (JSONB), `selected_at`.
**`family_shopping_lists`** — `items_json` (массив товаров), `updated_at`; уникальный индекс на `user_id` для личных списков.
**`family_pantry_items`** — позиции запасов; `source` (`manual` / `shopping_list`), `category`, `expires_at`, `note`.
**`shopping_categories`** — пользовательские категории; `slug`, `is_food`, `is_system`, scope.
**`meal_leftovers`** — остатки; `dish_name`, `portions_remaining`, `valid_until`, `leftover_status`, `added_by_user_id`.
**`meal_checkins`** — чекины приёмов (`meal_type`, `planned_date`, `actual_status`, `actual_*` КБЖУ, `family_member_id`, `recipe_id`).
**`event_plans`** — план застолья (`guests_count`, `theme`, `drink_menu_mode`, `plan_data` JSONB).

### 6.4 Рецепты

**`recipes`** — `title`, `meal_type`, `cuisine`, `cooking_time_minutes`, `calories_per_serving`, `protein_g/fat_g/carbs_g`, `is_drink`, `is_alcoholic`, `suitable_for_*`, `is_active`.
**`recipe_ingredients`**, **`recipe_steps`**, **`recipe_tags`**, **`recipe_allergens`**, **`recipe_restrictions`**, **`recipe_ratings`**, **`recipe_import_jobs`**.

### 6.5 Подписки и Амы

**`subscription_plans`** — `code`, `name`, `price_rub`, `max_profiles`, `monthly_menu_generations`, `monthly_ams`, `features` (JSONB), `sort_order`.
**`user_subscriptions`** — `plan_code`, `status`, `trial_ends_at`, `current_period_ends_at`, `menu_generations_used`, `metadata_json`.
**`ama_wallets`** — кошелёк (`user_id` или `family_id`), `balance`.
**`ama_transactions`** — `wallet_id`, `amount`, `type` (`topup`/`spend`), `reason`, `metadata_json`.
**`ai_usage_logs`** — каждый AI-запрос (`action_type`, `ams_spent`, `model`, `input_tokens`, `output_tokens`).

### 6.6 Прогресс, нутрициолог, забота

**`progress_entries`** — вес и замеры (`weight_kg`, `body_fat_percent`, `waist_cm`, `chest_cm`, `hips_cm`, `recorded_at`).
**`training_entries`** — `training_type`, `duration_minutes`, `intensity`, `calories_burned`, `training_date`.
**`nutrition_targets`** — цели КБЖУ/воды на пользователя.
**`deferred_nutrition_advice`** — отложенные советы (`advice_key`, `status`).
**`water_intake_logs`** — стаканы воды (`amount_ml`, `log_date`).
**`care_settings`** — уровень и каналы (water/protein/menu/shopping/pantry/progress/family/pro).
**`care_notifications`** — отправленные/запланированные.
**`care_events`** — события для тюнинга.

### 6.7 Прочее

**`telegram_bot_sessions`** — состояние FSM (state, invite_token, payload_json).

---

## 7. Список известных проблем

### 7.1 Дублирование экранов и маршрутов

- **`/settings/care` ≡ `/nutritionist/care`** — оба монтируют один `CareSettingsPanel`. Два разных входа, одинаковая страница.
- **`/menu/recipes`** — теперь `redirect("/recipes")`, маршрут оставлен только для обратной совместимости.
- **`/settings/units` / `/settings/privacy` / `/settings/language`** — заглушки на одном `SettingsPlaceholder`; не несут уникальной функциональности.
- **`/menu/event`** — экран реализован (`apps/web/app/menu/event/page.tsx`, `apps/api/app/routers/event_plans.py`), но входа из основного UI нет.

### 7.2 Неиспользуемые/осиротевшие компоненты

- `components/HealthStatus.tsx` — отдельный health-индикатор, нигде не импортируется в страницах.
- `components/TelegramAuthPanel.tsx` — компонент авторизации, не подключён (используется `TelegramRequiredScreen`).
- `components/auth/PhoneRequiredScreen.tsx` — реальный экран, но он не выводит UI выбора (только информационный блок). На бэке шаг есть, на фронте он визуально дублирует `LegalConsentScreen` / `TelegramRequiredScreen` логически.
- `components/bot/BotQuickInputHint.tsx` — отображается в `Shopping` и `Pantry`, но текст одинаковый, можно вынести.
- `apps/api/app/services/menu_ai_legacy.py` — старый клиент, помечен legacy.

### 7.3 Дублирование функций

- **Категория товаров** определяется и на клиенте (`lib/shopping/category-suggest.ts`), и на сервере (`shopping_categories.normalize_category`). При расхождении словарей возможен mismatch.
- **Прогресс цели** считается дважды: бэкенд (`progress.calculate_goal_progress`) и клиент (`lib/nutritionist/goal-progress.ts::computePercent`). UI берёт серверное значение при наличии, иначе считает сам — расхождение возможно при разных формулах для `sport`/`healthy`.
- **Главный совет** формируется и бэкендом (`MenuOverview.nutritionist_advice`), и фронтом (`pickMainAdvice` в `NutritionistDashboard`). При различных источниках данных совет на `/menu` и `/nutritionist` может отличаться.
- **План дня (Сегодня)** в нескольких местах: главная, `/menu`, `bot_today.build_today_summary` — разные форматы и поля.

### 7.4 Лишние состояния

- `wizardGoal: MenuGoalId | null` в `MenuPlanner` + повторная инициализация из профиля питания. При смене профиля состояние может расходиться, пока не обновится load().
- `personsCount` хранится в localStorage (`planam_persons_override`) и в `wizardGoal`-связанной логике одновременно. При семейном режиме UI игнорирует override, но сохранённое значение остаётся.
- `bot_session` хранит `invite_token` отдельно от `payload_json` — два пути для одного состояния FSM.
- `localStorage.planam_deferred_advice` остался от первой версии — мигрируется в API при загрузке, но никогда не очищается, если миграция падает.

### 7.5 UX-проблемы

- **Нижняя панель не показывает Профиль** — вход только через иконку в шапке `/`. На остальных экранах попасть в профиль можно лишь через главную.
- **«Сегодня» появляется в нескольких местах** — на главной, на `/menu`, в боте; данные иногда отличаются (особенно если меню многодневное).
- **«Где поели» (чекины)** — единственная точка входа `/menu/current`; пользователь, начиная день, может не открыть план и пропустить отметку.
- **Многодневный план** — переключатель есть только на `/menu/current`. На главной и в `/menu` показывается только день 1.
- **«Изменить на сегодня» (`/menu/settings`)** — название неточное: это не настройки текущего дня, а override параметров мастера, сохранённый в localStorage.
- **`/menu/leftovers`** — нет пагинации и сортировки; при большом числе остатков UI становится длинным.
- **`/nutritionist`** — три ссылки на похожие действия (`Изменить цель`, `Добавить вес`, `Добавить тренировку`) ведут на разные экраны через `returnTo`-параметр, что часто запутывает пользователя.
- **`/admin/*`** — нет нижней панели и нет ссылки на админку в основном UI (по дизайну, но в Telegram приходится использовать `/admin` бота).
- **Профиль питания** длинный, разбит на аккордеоны, но на главной нет CTA «дозаполнить»; пользователю нужно знать о пробелах.
- **`Sticky bottom bar`** — на узких экранах перекрывает контент при наличии нижней навигации (используется `paddingBottom: calc(4.75rem + safe-area + 5.25rem)`, нужно проверять на мобильных). 

### 7.6 Технические долги

- Не все события `care_events` логируются (зависит от исключений в шедулере).
- В `service/notifications.py` нет нормализации `timezone` при сохранении; передаётся IANA-строкой без проверки.
- `apps/api/app/services/menu_ai_legacy.py` помечен как `legacy`, но всё ещё импортируется в нескольких вспомогательных модулях (не критично, но мёртвая ветка).
- Тесты в `apps/api/tests` существуют, но покрытие неполное (например, нет тестов на multi-day plan и `meal_checkins.family_member_id`).

---

## 8. Список всех кнопок проекта

> «Действие» — отправляемый API-запрос или переход. «Обработчик» — основной handler в коде. «Результат» — что видит пользователь.

### 8.1 Главная (`/`)

| Кнопка | Действие | Обработчик | Результат |
|---|---|---|---|
| Профиль (иконка) | переход `/profile` | `<Link>` | Экран профиля |
| Открыть план | переход `/menu` | `<Link>` | Хаб меню |
| Открыть покупки | переход `/shopping` | `<Link>` | Покупки |
| Открыть (запасы) | переход `/pantry` | `<Link>` | Запасы |
| Составить план | переход `/menu` | `<Link>` | Хаб меню (пустое состояние) |

### 8.2 `/menu`

| Кнопка | Действие | Обработчик | Результат |
|---|---|---|---|
| Составить меню | переход `/menu/generate` | `<Link>` | Мастер |
| Обновить меню | переход `/menu/generate` | `<Link>` | Мастер |
| Сделать дешевле / Использовать запасы / Больше белка / Меньше времени на готовку / Заменить блюдо | `POST /menus/overview/quick-action` | `handleQuickAction` | Сообщение или редирект (`replace_dish` → `/menu/current?replace=1`) |
| Подробнее → / Открыть все дни → | переход `/menu/current` | `<Link>` | Текущий план |
| Изменить на сегодня → | переход `/menu/settings` | `<Link>` | Override параметров |
| Изменить → (внутри Settings summary) | переход `/menu/settings` | `<Link>` | То же |
| Настройки меню (раскрыть) | toggle local state | `setSettingsOpen` | Раскрытие блока |
| Остатки блюд | переход `/menu/leftovers` | `<Link>` | Список остатков |
| Рецепты | переход `/recipes` | `<Link>` | Каталог |
| Текущее меню → | переход `/menu/current` | `<Link>` | Текущий план |
| Повторить | повторный `load()` | `void load()` | Перезагрузка обзора |
| На главную | переход `/` | `<Link>` | Главная |

### 8.3 `/menu/generate`

| Кнопка | Действие | Обработчик | Результат |
|---|---|---|---|
| ← Меню | переход `/menu` | `<Link>` | Хаб |
| ← Назад к настройкам | смена фазы | `setPhase('setup')` | Возврат к мастеру |
| Чипы цели | `setWizardGoal` | onClick | Выбор цели |
| Чипы персон (1–8) | `setPersonsCount` | onClick | Изменение `effectivePersons` |
| Чипы дней | `setWizardDays` | onClick | Период |
| Чипы бюджета | `setWizardBudget` | onClick | Бюджет |
| Чипы режима плана | `changePlanMode` → `savePlanMode` | onClick | Сохранение в `localStorage` |
| Назад | `setWizardStep(s-1)` | onClick | Предыдущий шаг |
| Продолжить / Сгенерировать меню | `handleWizardContinue` → `POST /menus/generate` | `handleGenerate` | Список из 3 вариантов |
| Выбрать вариант | `POST /menus/select` | `handleSelect` → `router.push('/menu/current?saved=1')` | Сохранение и редирект |
| ← Назад к выбору | `setPreviewMenu(null)` | onClick | Возврат к списку |
| Тариф и Амы → | переход `/subscription` | `<Link>` | Тариф |

### 8.4 `/menu/current`

| Кнопка | Действие |
|---|---|
| ← Меню | `/menu` |
| Настроить план | `/menu` |
| Чипы дней | `setDayIndex` |
| Заменить блюдо | модалка `ReplaceDishModal` → `POST /menus/replace-dish` + `POST /menus/select` |
| Чекины (поел дома / работа / кафе / ресторан / доставка / другое) | `POST /meal-checkins` |
| Член семьи (family) | `setMemberId` |
| Остатки блюд | `/menu/leftovers` |

### 8.5 `/menu/leftovers`

| Кнопка | Действие |
|---|---|
| ← Меню | `/menu` |
| + Добавить | форма создания |
| Сохранить | `POST /meal-leftovers` |
| Статусы (Доедено / В морозилку / Испорчено) | `PATCH /meal-leftovers/{id}` (`leftover_status`) |
| Удалить | `DELETE /meal-leftovers/{id}` |
| ↑ К покупкам | `/shopping` |

### 8.6 `/menu/settings`

| Кнопка | Действие |
|---|---|
| Чекбокс override | toggle local state |
| Чипы персон | `setPersonsOverride` |
| Чипы режимов плана | `setPlanMode` |
| Сохранить | `savePlanMode` + `savePersonsOverride` |
| Обновить меню | `/menu/generate` |

### 8.7 `/shopping`

| Кнопка | Действие |
|---|---|
| + Добавить | открыть `ShoppingItemSheet` |
| Сохранить | `POST /shopping/items` или `PATCH /shopping/items/{id}` |
| Чекбокс товара | `PATCH /shopping/items/{id}/toggle` |
| Изменить / Удалить | редактирование / `DELETE` |
| Категория (выбор) | `CategoryPicker` |
| + Категория | `POST /shopping/categories` |
| Синхронизировать | `POST /shopping/sync` |
| Скрыть купленные | toggle local state |
| Развернуть / Свернуть категорию | toggle local state |
| Поиск | local filter |

### 8.8 `/pantry`

| Кнопка | Действие |
|---|---|
| + Добавить | `PantryItemForm` |
| Сохранить | `POST /pantry` или `PATCH /pantry/{id}` |
| Фильтры (Все / Скоро / Недавно / Из покупок / Вручную) | `setFilter` |
| Удалить | `DELETE /pantry/{id}` |
| ↑ К покупкам | `/shopping` |

### 8.9 `/recipes`

| Кнопка | Действие |
|---|---|
| Поиск | debounce → `GET /recipes?q=` |
| Чипы (Завтрак/Обед/Ужин/Перекус) | смена фильтра |
| Показать ещё | пагинация |
| В избранное | `POST /recipes/{id}/favorite` |
| Карточка | `router.push('/recipes/{id}')` |
| Скролл наверх (FAB) | `window.scrollTo` |

### 8.10 `/recipes/[id]`

| Кнопка | Действие |
|---|---|
| ← Каталог | `/recipes` |
| В избранное | `POST /recipes/{id}/favorite` |
| В покупки | `POST /recipes/{id}/add-to-shopping` |
| В меню | `POST /recipes/{id}/add-to-menu` |
| Улучшить | `GET /recipes/{id}/improve` |
| Совместимость | `GET /recipes/{id}/family-compatibility` |
| Оценить | `GET /recipes/{id}/evaluate` |

### 8.11 `/nutritionist`

| Кнопка | Действие |
|---|---|
| Открыть профиль | `/profile/nutrition?returnTo=/nutritionist` |
| Спросить нутрициолога | `/nutritionist/chat` |
| Добавить вес | `/progress?focus=weight&returnTo=/nutritionist` |
| Добавить тренировку | `/progress?focus=training&returnTo=/nutritionist` |
| Изменить цель | `/profile/nutrition?returnTo=/nutritionist` |
| Добавить в меню (совет) | `/menu/generate?returnTo=/nutritionist` |
| Найти рецепт | `/recipes?search=<hint>` |
| Добавить в покупки | `/shopping?add=<hint>` |
| Не сейчас (совет) | `POST /nutritionist/deferred-advice` |
| Выполнить (отложенный) | `PATCH /nutritionist/deferred-advice/{id}` `completed` |
| Вернуть (отложенный) | `DELETE /nutritionist/deferred-advice/{id}` |
| Удалить (отложенный) | `PATCH /nutritionist/deferred-advice/{id}` `dismissed` |
| + стакан воды | `POST /nutritionist/water` |
| Отметить, где поели → | `/menu/current` |

### 8.12 `/nutritionist/chat`

| Кнопка | Действие |
|---|---|
| Отправить | `POST /nutritionist/ask` |
| ← Нутрициолог | `/nutritionist` |
| Перейти к тарифу | `/subscription` |

### 8.13 `/nutritionist/care` и `/settings/care`

| Кнопка | Действие |
|---|---|
| Режим (`minimal` / `standard` / `active`) | `PATCH /care/settings` |
| Переключатели типов | `PATCH /care/settings` |
| Отправить тест | `POST /care/settings/test` |

### 8.14 `/profile`

| Кнопка | Действие |
|---|---|
| → Настройки | `/settings` |
| Питание | `/profile/nutrition` |
| Семья | `/family` |
| Подписка | `/subscription` |
| Прогресс | `/progress` |
| Уведомления | `/notifications` |
| О приложении | `/settings/about` |
| Переключатель режима | `POST /users/app-mode` |

### 8.15 `/profile/nutrition`

| Кнопка | Действие |
|---|---|
| Аккордеоны секций | toggle local state |
| Чипы (цели, диеты, аллергии) | `patch(...)` |
| Поля веса/роста/возраста | `NumberInput` → state |
| Сохранить | `POST /nutrition/profile` → `router.replace(returnTo)` |

### 8.16 `/progress`

| Кнопка | Действие |
|---|---|
| + Добавить вес | open form |
| + Добавить тренировку | open form |
| Сохранить (вес) | `POST /progress/entries` |
| Сохранить (тренировка) | `POST /progress/trainings` |
| Скрыть / Показать (семье) | `PATCH /progress/privacy` |
| Отмена | close form |

### 8.17 `/subscription`

| Кнопка | Действие |
|---|---|
| Выбрать (по тарифу) | `POST /subscription/select` |
| ← Профиль | `/profile` |

### 8.18 `/family`

| Кнопка | Действие |
|---|---|
| + Добавить участника | `AddPersonSheet` |
| Пригласить | `POST /families/{id}/invites` |
| Виртуальный участник | `POST /families/{id}/virtual-members` |
| Редактировать | `MemberForm` |
| Сохранить | `PATCH /families/{id}/members/{member_id}` |
| Удалить | `DELETE /families/{id}/members/{member_id}` |
| Передать админа | `FamilyManageSheet` |
| Открыть профиль питания | `/profile/nutrition?member=...` |
| Переключатель `allow_admin_profile_edit` | `PATCH /families/me/allow-admin-edit` |

### 8.19 `/notifications`

| Кнопка | Действие |
|---|---|
| Переключатели | local state |
| Поля времени | local state |
| Выбор timezone | local state |
| Сохранить | `PATCH /notifications/settings` |

### 8.20 `/onboarding`

| Кнопка | Действие |
|---|---|
| Чипы выборок | local state |
| Далее / Назад | `setStep` |
| Завершить | `POST /onboarding/answers` |
| Пропустить | `POST /onboarding/answers` (skip) |

### 8.21 `/admin/*`

(см. подробнее в `apps/web/components/admin/*`)

| Кнопка | Действие |
|---|---|
| Поиск пользователей | `GET /admin/users?q=` |
| Заблокировать / Разблокировать | `POST /admin/users/{id}/block` / `/unblock` |
| Удалить | `POST /admin/users/{id}/delete` |
| Выдать подписку | `POST /admin/users/{id}/subscription` |
| Выдать Амов | `POST /admin/users/{id}/ams` |
| Выдать Амов семье | `POST /admin/families/{id}/ams` |
| Обновить | `await load()` |

---

## 9. Тарифы и ограничения

Seed `PLAN_SEEDS` (`apps/api/app/services/subscription_catalog.py`):

| Код | Название | Цена | Профили | Меню / мес. | Амы / мес. | Ключевые фичи |
|---|---|---:|---:|---:|---:|---|
| `trial` | Пробный | 0 ₽ | 1 | 20 | 200 | shopping, pantry, notifications, nutrition_profile, nutritionist_basic, ocr/voice limited. Длительность — 14 дней (`TRIAL_DAYS`). |
| `personal` | Личный | 249 ₽ | 1 | 50 | 200 | как trial, без family/macros |
| `shared` | Совместный | 399 ₽ | 3 | 60 | 300 | + family_mode, shared_lists |
| `family` | Семейный | 599 ₽ | 6 | 70 | 400 | + family_roles, virtual_members, family_notifications |
| `pro` | ПланАм PRO | 999 ₽ | 15 | безлимит | 500 | + macros, weight_progress, sport_goals, auto_planning, ocr/voice без лимита, ai_care, finance_analytics |

Стоимости AI-действий в Амах (`AMA_COSTS`):

| Действие | Амов |
|---|---:|
| `nutritionist_ask` | 2 |
| `menu_generation_extra` (сверх лимита плана) | 5 |
| `menu_replace_dish` | 3 |
| `ocr_receipt` | 4 |
| `voice_command` | 3 |
| `deep_nutrition_analysis` | 8 |
| `menu_rebuild` | 5 |
| `ai_report` | 10 |
| `recipe_analyze` | 2 |
| `recipe_improve` | 3 |
| `bot_parse_text` | 1 |
| `event_plan_ai` | 8 |

Прочие ограничения:

- **Trial**: 14 дней, 20 генераций меню.
- **Lock логика** (`subscription.assert_menu_generation_allowed`): по достижении лимита бросает `HTTPException` с `code=menu_generation_limit` и флагом `can_pay_with_ams`.
- **PRO-функции** (`features.macros`, `features.weight_progress`, `features.macros`, `features.sport_goals`, `features.ai_care`, `features.finance_analytics`) гейтятся в `require_pro`.
- **AI-фичи** в Trial/Personal/Shared/Family — `ocr_receipts: "limited"`, `voice_commands: "limited"` (доступны, но списывают Амы и могут быть ограничены по дням).
- **Family-приглашения**: число активных участников ≤ `plan.max_profiles` (включая виртуальных).

---

## 10. Предложения по упрощению интерфейса

Без изменения функциональности можно сократить когнитивную нагрузку:

1. **Унифицировать «Сегодня».** Один источник правды для блока: `MenuOverview.today_meals` + `meal_checkins`. На главной показывать не `menu.meals[0]`, а данные на дату с фронтового хелпера `mealsForDayIndex`.
2. **Слить `/settings/care` и `/nutritionist/care`.** Оставить один маршрут, второй — редирект (как уже сделано для `/menu/recipes`).
3. **Удалить заглушечные настройки.** `/settings/units`, `/settings/privacy`, `/settings/language` — спрятать в expander «В разработке» или объединить в один раздел «Скоро».
4. **Сжать профиль.** Объединить «Профиль / Питание / Прогресс / Уведомления» в один раздел `Профиль` с табами, оставив `/family` и `/subscription` отдельно.
5. **Сократить шаги мастера.** В личном режиме шага «количество человек» уже нет; для семейного режима можно подставлять `members_count` по умолчанию и не показывать шаг, если он не отличается. «Бюджет» и «Режим плана» — объединить в один шаг.
6. **Один список рецептов.** Убрать осиротевший маршрут `/menu/recipes` после периода обратной совместимости.
7. **Перенести `Профиль` в нижнюю панель.** Сейчас входа в профиль на остальных экранах нет — пользователю приходится возвращаться на главную. Можно заменить вкладку «ПланАм» (главная) на «Профиль» + сделать главную доступной через лого в шапке.
8. **Объединить чекины и заметку «Где поели».** Сделать панель чекинов в `/menu` (а не только в `/menu/current`), чтобы не уводить пользователя глубже.
9. **Сократить «Быстрые действия» на `/menu`.** Сейчас 5 кнопок; «Заменить блюдо» дублирует функцию из карточки блюда в `/menu/current`. Можно оставить 3 ключевые (`cheaper`, `more_pantry`, `more_protein`).
10. **Уведомления.** Объединить экраны `/notifications` (cook/buy) и `/nutritionist/care` (тон уведомлений) в один — там сейчас разные ментальные модели, но один пользовательский запрос «настроить, когда писать».
11. **Сократить меню действий с советом.** Кнопки `Не сейчас` (отложить) + `Вернуть` дублируются. Можно оставить только `Выполнить` / `Не сейчас` (как тоггл).
12. **Унифицировать форму CRUD.** Запасы, покупки и остатки используют разные паттерны (sheet, инлайн-форма, отдельная страница). Один компонент `EntitySheet` сократил бы код и UX-разницу.
13. **Один источник «прогресс к цели».** Серверная формула должна быть единственным источником; клиентский расчёт оставить как fallback при пустом ответе.
14. **Скрыть PRO-блоки до апсейла.** Сейчас в `NutritionistDashboard` показываются разделы, доступные только PRO; для не-PRO пользователей выводить компактный блок с CTA на `/subscription`.
15. **Сократить кнопки «Профиль» / «← Меню» в шапках.** Их теперь много (`ScreenLayout`, отдельные `Link`), стоит унифицировать через `ScreenBackNav`.

---

> Дата отчёта: 25.05.2026. Источник: репозиторий `ai-food-family`, ветка `main`. Все ссылки на код — относительные пути от корня проекта.
