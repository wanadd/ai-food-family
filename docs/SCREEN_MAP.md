# Карта экранов ПланАм

Аудит пользовательских экранов Telegram Mini App. Данные собраны из репозитория `ai-food-family` **без изменений кода** (2026-06-03).

**Источники:** `apps/web/app/**/page.tsx`, `apps/web/components/**`, `apps/web/lib/navigation/nav-config.ts`, клиентские API-модули `apps/web/lib/**/api.ts`.

---

## Навигация

### Нижняя панель (5 вкладок)

| Вкладка | Маршрут | Активна также на |
|---------|---------|------------------|
| Меню | `/menu` | `/menu/*`, `/recipes/*` |
| Покупки | `/shopping` | `/shopping/*`, `/pantry/*` |
| ПланАм | `/` | `/` |
| Здоровье | `/health` | `/health/*`, `/nutritionist/*` |
| Профиль | `/profile` | `/profile/*`, `/family`, `/progress`, `/subscription`, `/notifications`, `/settings/*` |

Скрыта на: `/onboarding*`, `/admin*`.

### Внутренние вкладки

**Меню:** `/menu` · `/menu/recipes` · `/menu/favorites` · `/menu/collections`

**Покупки:** `/shopping` · `/shopping/pantry` · `/shopping/leftovers`

---

## Условные обозначения

| Колонка | Описание |
|---------|----------|
| **Тип** | `route` — URL; `redirect` — только перенаправление; `gate` — блокирующий оверлей до маршрута |
| **API** | Реальные пути backend (`GET /menus/overview`, не legacy-имена из старых docs) |
| **Модалки** | Sheet / dialog / inline-form поверх экрана |

---

## Основная таблица экранов

### Главная и меню

| Route | Page / Component | Назначение | API endpoints | Основные кнопки | Модальные окна | Переходы |
|-------|------------------|------------|---------------|-----------------|----------------|----------|
| `/` | `page.tsx` → `PlanAmHome` | AI-хаб: приветствие, «что сегодня», быстрый вход в меню / покупки / чат | `GET /menus/selected`, `GET /shopping-lists/me` | Открыть меню · Что купить · Спросить ПланАм | — | `/menu`, `/shopping`, `/health/chat` |
| `/menu` | `MenuHub` | Хаб «Моё меню»: сегодня в плане, открыть план, быстрые действия | `GET /menus/overview`, `POST /menus/quick-action`, `GET /subscriptions/me` | Составить меню (empty) · Открыть план · Настроить меню · Повторить / На главную (error) | `MenuQuickActionsSheet` · `AmaConfirmDialog` | `/menu/generate`, `/menu/current`, `/menu/settings`, `/`, `/subscription` (402), redirect из quick-action |
| `/menu/generate` | `MenuPlanner` | Мастер генерации меню (шаги + выбор варианта) | `GET /nutrition-profile/me`, `GET /menus/selected`, `GET /pantry/me`, `POST /menus/generate`, `POST /menus/select` | ← Меню · Назад/Продолжить по шагам · Сгенерировать · Выбрать вариант · Открыть план | Полноэкранный preview варианта · `AmaConfirmDialog` | `/menu`, `/menu/current?saved=1`, `/subscription`, `/` (error) |
| `/menu/current` | `MenuCurrentView` | Текущий план по дням, замена блюд, чекины | `GET /menus/selected`, `POST /menus/replace-dish`, `POST /menus/select`, `GET /meal-checkins/today`, `POST /meal-checkins` | ← Меню · Чипы дней · Заменить блюдо · Где поели (чекин) · Остатки блюд → | `ReplaceDishModal` · `MenuDayOverview` → `Sheet` (деталь блюда) · `AmaConfirmDialog` | `/menu`, `/shopping/leftovers`, `/recipes/[id]` (из Sheet) |
| `/menu/settings` | `MenuSettingsPage` | Локальные override персон и режима плана (`localStorage`) | — | Override toggle · Чипы персон/режима · Сохранить · Обновить меню → | — | `/menu/generate`, `/menu` |
| `/menu/recipes` | `MenuSectionLayout` + `RecipesView` | Каталог рецептов (поиск, сценарии, фильтры в URL) | `GET /recipes`, `GET /recipes/filters`, `GET /recipes/scenarios`, `POST /recipes/{id}/favorite` | Поиск · Сценарии · Фильтры · Карточка рецепта · Избранное · Составить меню → | `RecipeFiltersSheet` · `ScenarioChips` → Sheet «Ещё подборки» | `/recipes/[id]`, `/menu/generate` |
| `/menu/favorites` | `MenuSectionLayout` + `FavoritesView` | Избранные рецепты | `GET /recipes` (favorite filter), `POST /recipes/{id}/favorite` | Карточки · Перейти в каталог → | — | `/recipes/[id]`, `/menu/recipes` |
| `/menu/collections` | `MenuSectionLayout` + `CollectionsView` | Список коллекций, создание | `GET /collections`, `POST /collections` | Создать коллекцию · Открыть коллекцию | — | `/menu/collections/[id]` |
| `/menu/collections/[id]` | `CollectionDetailView` | Рецепты в коллекции | `GET /collections/{id}` | ← Коллекции · Карточки рецептов | — | `/menu/collections`, `/recipes/[id]` |
| `/menu/event` | inline wizard в `page.tsx` | План застолья / события (черновик) | `POST /event-plans`, `POST /event-plans/{id}/create-shopping-list` | Тип события · Гости · Бюджет · Сгенерировать · Добавить в покупки · ← Меню | — | `/menu`, `/shopping` |

### Покупки и запасы

| Route | Page / Component | Назначение | API endpoints | Основные кнопки | Модальные окна | Переходы |
|-------|------------------|------------|---------------|-----------------|----------------|----------|
| `/shopping` | `ShoppingListView` | Список покупок семьи | `GET /shopping-lists/me`, `POST /shopping-lists/items`, `PATCH /shopping-lists/items/{id}`, `DELETE /shopping-lists/items/{id}`, `PATCH …/toggle`, `POST /shopping-lists/sync`, `GET/POST /shopping-categories` | + Товар · + Категория · Чекбокс · Синхронизировать с меню · Поиск · Скрыть купленные · К меню → | `ShoppingItemSheet` · `ShoppingCategorySheet` · `CategoryPicker` (dropdown) | `/menu`, `/shopping/pantry`, `/shopping/leftovers` (sub-tabs) |
| `/shopping/pantry` | `PantryDashboard` | Запасы продуктов | `GET /pantry/me`, `POST /pantry/items`, `PATCH /pantry/items/{id}`, `DELETE /pantry/items/{id}`, `GET /shopping-categories` | + Добавить · Фильтры · Сохранить/Удалить · ↑ К покупкам | `PantryItemForm` (Sheet) | `/shopping` |
| `/shopping/leftovers` | `MealLeftoversPage` | Остатки приготовленных блюд | `GET /meal-leftovers`, `POST /meal-leftovers`, `PATCH /meal-leftovers/{id}`, `DELETE /meal-leftovers/{id}` | Добавить остаток · Статус · Удалить · Отметить приёмы → | — | `/menu/current`, sub-tabs |

### Здоровье

| Route | Page / Component | Назначение | API endpoints | Основные кнопки | Модальные окна | Переходы |
|-------|------------------|------------|---------------|-----------------|----------------|----------|
| `/health` | `NutritionistDashboard` | Лёгкий хаб здоровья (без сетевых запросов, cache-only совет) | — (read cache: profile, menu, pantry) | Сегодня · Цели · Прогресс · AI-рекомендации | — | `/health/today`, `/profile/nutrition?returnTo=…`, `/progress?returnTo=…`, `/health/chat` |
| `/health/today` | `HealthTodayView` | КБЖУ, вода, совет дня, отложенные рекомендации | `GET /nutrition-profile/me`, `GET /menus/selected`, `GET /pantry/me`, `GET /progress/me`, `GET/POST/PATCH/DELETE /nutritionist/deferred-advice`, `GET …/suppressed-titles`, `GET/POST /nutritionist/water/*` | Заполнить профиль · + вода · Не сейчас / CTA советов · Отметить где поели · AI-чат → | — | `/profile/nutrition`, `/menu/current`, `/menu/generate`, `/menu/recipes`, `/shopping`, `/progress`, `/health/chat` |
| `/health/chat` | `ScreenLayout` + `NutritionistChat` | Чат с AI-нутрициологом (Амы) | `POST /nutritionist/ask`, `GET /subscriptions/me`, `GET /nutrition-profile/me`, `GET /menus/selected` | ← Здоровье · Спросить · Перейти к тарифу | `AmaConfirmDialog` | `/health`, `/subscription` |

### Рецепты

| Route | Page / Component | Назначение | API endpoints | Основные кнопки | Модальные окна | Переходы |
|-------|------------------|------------|---------------|-----------------|----------------|----------|
| `/recipes/[id]` | `RecipeDetailModal` | Деталь рецепта: ингредиенты, оценка, AI-анализ | `GET /recipes/{id}`, `POST /recipes/{id}/favorite`, `POST /recipes/{id}/add-to-shopping`, `POST /recipes/{id}/add-to-menu`, `POST /recipes/{id}/cooked`, `GET /recipes/{id}/why`, `GET /recipes/{id}/evaluate`, `GET /recipes/{id}/improve`, `GET /recipes/{id}/family-compatibility`, `GET/POST /collections/*` | ← Каталог · В избранное · В покупки · В меню · Ещё (AI) · Я приготовил · 👍/❤️/👎 | `Sheet` «Ещё» · `AmaConfirmDialog` (evaluate/improve) | `/menu/recipes` |

### Профиль и семья

| Route | Page / Component | Назначение | API endpoints | Основные кнопки | Модальные окна | Переходы |
|-------|------------------|------------|---------------|-----------------|----------------|----------|
| `/profile` | `ProfileDashboard` | Хаб профиля, режим personal/family | `GET /nutrition-profile/me`, `PATCH /users/me/app-context` | ⚙️ Настройки · Профиль питания · Пункты меню (6) · Переключатель режима | — | `/settings`, `/profile/nutrition`, `/family`, `/subscription`, `/progress`, `/notifications`, `/settings/about` |
| `/profile/nutrition` | `NutritionProfileForm` | Цели, аллергии, ограничения, PRO-поля | `GET /nutrition-profile/me`, `PUT /nutrition-profile/me` | Аккордеоны секций · Сохранить | Inline-секции (accordion) | `returnTo` или `/profile` |
| `/family` | `FamilyDashboard` | Семья: участники, приглашения, виртуальные | `GET/POST/PATCH/DELETE /families/*`, invites, members, nutrition | Создать семью · + Человек · Управление · Редактировать/Удалить · Составить меню → | `AddPersonSheet` · `InviteSheet` · `FamilyManageSheet` · `VirtualMemberNutritionForm` | `/profile`, `/`, `/menu/generate`, `/profile/nutrition` |
| `/progress` | `ProgressDashboard` | Вес, замеры, тренировки, приватность | `GET /progress/me`, `POST /progress/me`, `POST /progress/training`, `PATCH /progress/settings` | ← Назад · Добавить вес/тренировку · Сохранить · Скрыть от семьи | Inline-формы веса/тренировки · `ProgressProLocked` | `returnTo` (default `/profile`), `/subscription` |
| `/subscription` | `SubscriptionDashboard` | Тариф, баланс Амов, выбор плана | `GET /subscriptions/me`, `POST /subscriptions/select-plan` | ← Профиль · Выбрать тариф · Купить Амы (заглушка) | — | `/profile` |
| `/notifications` | `CareSettingsPanel` + `NotificationSettingsForm` | Care-уведомления + расписание готовки/покупок | `GET/PATCH /care/settings`, `POST /care/test-notification`, `GET/PUT /notifications/settings` | Уровень care · Переключатели · Тихие часы · Тест · Время покупок/приёмов · Календарь (.ics) | — | `/profile`, `/` |

### Настройки

| Route | Page / Component | Назначение | API endpoints | Основные кнопки | Модальные окна | Переходы |
|-------|------------------|------------|---------------|-----------------|----------------|----------|
| `/settings` | `SettingsHub` + items | Хаб настроек | — | Аккаунт · Документы · Удалить данные · Поддержка · О приложении | — | `/settings/*` |
| `/settings/account` | `SettingsScaffold` + inline | Telegram-аккаунт, API health | `GET /health` (display) | ← Настройки · Открыть бота | — | `/settings`, external t.me |
| `/settings/documents` | `SettingsScaffold` + inline | Юридические документы | `GET /legal/documents` | Accordion · Открыть на сайте | — | `/settings` |
| `/settings/delete-data` | `SettingsScaffold` + inline | Запрос удаления данных | `POST /legal/delete-data-request` | Checkbox · Отправить запрос | — | `/settings` |
| `/settings/support` | `SettingsScaffold` + inline | FAQ, контакты | — | Открыть бот · Уведомления → | — | `/settings`, `/notifications`, external t.me |
| `/settings/about` | `SettingsScaffold` + inline | Версия, миссия | — | ← Настройки | — | `/settings` |

### Auth gates (не URL, блокируют `AppGate`)

| Route | Component | Назначение | API endpoints | Основные кнопки | Модалки | Переходы |
|-------|-----------|------------|---------------|-----------------|---------|----------|
| *(gate)* | `TelegramRequiredScreen` | Нет Telegram auth | `POST /auth/telegram`, `POST /auth/dev-login` | Dev login (dev only) | — | после auth → целевой route |
| *(gate)* | `LegalConsentScreen` | Нет принятия документов | `GET /legal/documents`, `POST /legal/accept` | Принять · Ссылки на docs | — | → приложение |
| *(gate)* | `PhoneRequiredScreen` | Нет телефона | `POST /legal/skip-phone` (via contact in bot) | Пропустить (если legal ok) | — | → приложение |

### Админка (`/admin/*`, без нижней панели)

| Route | Page / Component | Назначение | API endpoints | Основные кнопки | Модалки | Переходы |
|-------|------------------|------------|---------------|-----------------|---------|----------|
| `/admin` | `AdminDashboard` (summary) | Сводка | `GET /admin/ping`, `GET /admin/summary`, users/families/subscriptions/ams | Табы навигации · Grant actions | `AdminConfirmDialog` | `/admin/*` |
| `/admin/users` | `AdminDashboard` (users tab) | Список пользователей | `GET /admin/users` | Поиск · Открыть карточку | — | `/admin/users/[id]` |
| `/admin/users/[id]` | `AdminUserDetailPage` | Карточка пользователя | `GET /admin/users/{id}`, block/unblock/reset/subscription/ams | Block · Reset · Grant · Delete | `AdminConfirmDialog` | `/admin/users` |
| `/admin/families` | `AdminDashboard` (families) | Список семей | `GET /admin/families` | Поиск · Детали | — | `/admin/families/[id]` |
| `/admin/families/[id]` | `AdminFamilyDetailPage` | Карточка семьи | `GET /admin/families/{id}`, subscription/ams/members | Block · Grant · Transfer · Remove member | `AdminConfirmDialog` | `/admin/families` |
| `/admin/subscriptions` | `AdminDashboard` (subscriptions) | Подписки | `GET /admin/subscriptions`, `GET /admin/plans` | Фильтры · Grant | — | `/admin/users/[id]` |
| `/admin/ams` | `AdminDashboard` (ams) | Балансы Амов | `GET /admin/ams/summary`, `GET /admin/ams/transactions` | Grant · Deduct | — | — |
| `/admin/openai` | `AdminOpenAiPage` | Статистика OpenAI | `GET /admin/openai`, `GET /admin/ai-usage` | — | — | — |
| `/admin/errors` | `AdminErrorsPage` | Лог ошибок | `GET /admin/errors` | Фильтры | — | — |

**Доступ к админке:** Telegram `/admin` + PIN → `X-Admin-Session`; прямой URL без сессии показывает «Нет доступа».

---

## Redirect-маршруты (legacy aliases)

| Route | Redirect | Тип |
|-------|----------|-----|
| `/recipes` | → `/menu/recipes` | legacy catalog URL |
| `/pantry` | → `/shopping/pantry` | legacy standalone pantry |
| `/menu/leftovers` | → `/shopping/leftovers` | legacy under menu |
| `/menu/scenarios` | → `/menu/recipes` | scenario = URL filter |
| `/nutritionist` | → `/health` | rebrand |
| `/nutritionist/chat` | → `/health/chat` | rebrand |
| `/nutritionist/care` | → `/health/care` → `/notifications` | care merged |
| `/health/care` | → `/notifications` | care merged |
| `/onboarding` | → `/profile/nutrition` | wizard retired |

---

## Аудит: проблемные экраны

### Orphan screens (есть route, нет входа из UI)

| Route | Компонент | Проблема |
|-------|-----------|----------|
| `/menu/event` | inline wizard | **Нет ссылок** в `MenuHub`, sub-tabs, bot web_app (grep по repo). Доступен только по прямому URL. Backend `POST /event-plans` реализован. |

### Dead screens / dead flows (маршрут или UI больше не используется)

| Объект | Статус |
|--------|--------|
| `/onboarding` | Redirect на `/profile/nutrition`; компонент `OnboardingWizard` **нигде не монтируется** |
| `OnboardingComplete`, 9-шаговый flow | Код есть, экран недостижим |
| `/settings/units`, `/settings/privacy`, `/settings/language`, `/settings/care` | **Страниц не существует** (упоминались в старых docs) |
| Home sub-components: `HomeQuickActions`, `HomeTodayCard`, `HomeShoppingCard`, `HomeRecommendations`, `HomeFamilySummary`, `HomeAskPlanAm` | **Не импортируются** после рефакторинга `PlanAmHome` (ONE SCREEN UX) |

### Unreachable screens (нужен особый доступ)

| Route | Как попасть |
|-------|-------------|
| `/admin/*` | Telegram bot `/admin` + PIN + `AdminSessionCapture`; не в нижней навигации |
| `/menu/event` | Только прямой URL / закладка |
| Auth gates | Блокируют всё приложение до выполнения условия |

### Legacy screens (старые URL, сохранены как redirect)

| Legacy | Актуальный | Примечание |
|--------|------------|------------|
| `/nutritionist`, `/nutritionist/chat`, `/nutritionist/care` | `/health/*`, `/notifications` | Rebrand «Нутрициолог» → «Здоровье» |
| `/recipes` | `/menu/recipes` | Каталог переехал во вкладку Меню |
| `/pantry`, `/menu/leftovers` | `/shopping/pantry`, `/shopping/leftovers` | Этап 3: единый раздел Покупки |
| `/onboarding` | `/profile/nutrition` | Мастер первого запуска заменён формой профиля |

### Screens with duplicated functionality

| Дублирование | Экраны | Суть |
|--------------|--------|------|
| **Care vs notifications** | `/notifications` | На одном экране `CareSettingsPanel` (care API) и `NotificationSettingsForm` (notifications API) — две модели напоминаний |
| **Health hub vs Health today** | `/health`, `/health/today` | `/health` — лёгкий cache-only хаб; `/health/today` — полный бывший dashboard нутрициолога (KPI, вода, deferred advice) |
| **Профиль vs Настройки** | `/profile`, `/settings` | «О приложении» в профиле (`/settings/about`) дублирует пункт в `/settings`; шестерёнка ↔ хаб настроек |
| **Menu settings vs Generate wizard** | `/menu/settings`, `/menu/generate` | Персоны и режим плана настраиваются и локально (`/menu/settings`), и в мастере генерации |
| **Quick actions** | `/menu` (`MenuQuickActionsSheet`) | Те же 5 действий описаны в `QUICK_ACTIONS` для MenuHub; `HomeQuickActions` (главная) **мертв**, но дублировал бы логику |
| **Recipe detail back** | `/recipes/[id]` | Деталь общая для всего app; back всегда на `/menu/recipes` (не на favorites/collections) |
| **Progress KPI** | `/health/today`, `/progress` | Прогресс к цели показывается в «Сегодня» и на `/progress` |

---

## Сводка

| Метрика | Значение |
|---------|----------|
| `page.tsx` всего | **47** |
| Рендерят контент | **38** |
| Только `redirect()` | **9** |
| Auth gates (не routes) | **3** |
| Админских экранов | **9** |
| Orphan (без UI-входа) | **1** (`/menu/event`) |
| Dead wizard | **1** (`OnboardingWizard` + `/onboarding` redirect) |
| Legacy redirects | **9** |
| Sheet/modal паттернов (основные) | `MenuQuickActionsSheet`, `ReplaceDishModal`, `AmaConfirmDialog`, `ShoppingItemSheet`, `ShoppingCategorySheet`, `PantryItemForm`, `RecipeFiltersSheet`, family sheets (×4), `RecipeDetailModal` → Sheet «Ещё» |

---

## Дерево навигации (актуальное)

```
/  ПланАм
├── /menu  (+ sub-tabs)
│   ├── /menu/generate
│   ├── /menu/current  ─ ReplaceDishModal, MealCheckin
│   ├── /menu/settings
│   ├── /menu/recipes  ─ RecipeFiltersSheet
│   ├── /menu/favorites
│   ├── /menu/collections
│   │   └── /menu/collections/[id]
│   └── /menu/event  ⚠ orphan
│
├── /shopping  (+ sub-tabs)
│   ├── ShoppingItemSheet, ShoppingCategorySheet
│   ├── /shopping/pantry  ─ PantryItemForm
│   └── /shopping/leftovers
│
├── /health
│   ├── /health/today
│   └── /health/chat  ─ AmaConfirmDialog
│
├── /recipes/[id]  (деталь, вне sub-tab URL)
│
└── /profile
    ├── /profile/nutrition
    ├── /family  ─ AddPersonSheet, InviteSheet, FamilyManageSheet
    ├── /subscription
    ├── /progress
    ├── /notifications  (care + notification settings)
    └── /settings
        ├── /settings/account
        ├── /settings/documents
        ├── /settings/delete-data
        ├── /settings/support
        └── /settings/about

Вне основной навигации:
/onboarding → redirect /profile/nutrition
/admin/*  (9 экранов)
Legacy redirects: /recipes, /pantry, /menu/leftovers, /menu/scenarios,
                  /nutritionist*, /health/care
```
