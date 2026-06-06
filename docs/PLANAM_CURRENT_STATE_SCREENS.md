# PLANAM — карта экранов (текущее состояние)

Дата фиксации: 2026-06-03  
Источник: `apps/web/app/**/page.tsx` (71 маршрут), компоненты-рендереры.

## Контекст продукта

- **Тип:** Telegram Mini App
- **Два UI-контура в коде:** Legacy (`AppShell` + `nav-config.ts`) и UI 2026 (`AppShell2026` + `nav-config-2026.ts`)
- **Переключатель:** `NEXT_PUBLIC_PLANAM_UI_2026=true|false` (`lib/planam/feature-flags.ts`)
- **Production Docker:** `NEXT_PUBLIC_PLANAM_UI_2026=true` (`apps/web/Dockerfile.prod`)
- **При UI 2026=true:** legacy-маршруты `/profile`, `/settings`, `/family`, `/notifications`, `/recipes`, `/menu/recipes` редиректят в 2026-ветку (page-level + middleware)

---

## A. UI 2026 — основные экраны (22 маршрута, 2026-only)

Экраны, защищённые `requirePlanamUi2026OrRedirect` или существующие только в 2026-ветке.

### A1. Дом

| Поле | Значение |
|------|----------|
| **Название** | Дом / Главная |
| **URL** | `/` |
| **Компонент** | `Home2026` (при flag=true) / `PlanAmHome` (при flag=false) |
| **Раздел** | Дом |
| **Задача** | Сводка дня: приветствие, hero-блюдо, быстрые действия, CTA меню и покупок |
| **Ценность** | Единая точка входа, следующий шаг дня |
| **Кто открывает** | Авторизованный пользователь Telegram Mini App |
| **Как попасть** | Стартовый маршрут; кнопка 🏠 в `ShellHeader2026`; deep link `/` |
| **Как уйти** | Bottom nav (Сегодня, Покупки, Здоровье, Профиль); quick actions; CTA «Открыть меню» / «Список покупок»; sheet «Остатки» |

| Поле | Значение |
|------|----------|
| **Название** | Дом (alias) |
| **URL** | `/home` |
| **Компонент** | `redirect("/")` |
| **Раздел** | Дом |
| **Задача** | Алиас на главную |
| **Как попасть** | Прямой URL `/home` |
| **Как уйти** | Редирект на `/` |

### A2. Покупки и запасы (2026)

| Поле | Значение |
|------|----------|
| **Название** | Список покупок |
| **URL** | `/home/shopping` |
| **Компонент** | `Shopping2026` |
| **Раздел** | Покупки (tab) |
| **Задача** | Список покупок по категориям, синхронизация, отметка купленного |
| **Ценность** | Список к покупке из меню и вручную |
| **Как попасть** | Bottom nav «Покупки»; CTA с главной; legacy `/shopping` редирект |
| **Как уйти** | Bottom nav; ссылка «Перейти к запасам» → `/home/pantry`; back header |

| Поле | Значение |
|------|----------|
| **Название** | Запасы |
| **URL** | `/home/pantry` |
| **Компонент** | `Pantry2026` |
| **Раздел** | Дом (не tab) |
| **Задача** | Просмотр и удаление позиций запасов |
| **Как попасть** | Ссылка с `/home/shopping`; legacy `/shopping/pantry` редирект |
| **Как уйти** | Back (returnTo `/home/shopping` при переходе с покупок); header back |

### A3. План (2026)

| Поле | Значение |
|------|----------|
| **Название** | План на неделю |
| **URL** | `/plan` |
| **Компонент** | `PlanWeek2026` |
| **Раздел** | План (tab «Сегодня» active via prefix) |
| **Задача** | Обзор недельного меню по дням |
| **Как попасть** | Subtab «Неделя»; legacy `/menu` редирект |
| **Как уйти** | Subtabs; переход на день/сегодня/рецепты |

| Поле | Значение |
|------|----------|
| **Название** | Сегодня |
| **URL** | `/plan/today` |
| **Компонент** | `PlanToday2026` |
| **Раздел** | План (tab) |
| **Задача** | Меню на выбранный день: приём пищи, замена, удаление, итог дня |
| **Как попасть** | Bottom nav «Сегодня»; CTA с главной; quick action «Меню» |
| **Как уйти** | Bottom nav; subtab; карточка «Рецепт»; replace flow → каталог |

| Поле | Значение |
|------|----------|
| **Название** | Генерация плана |
| **URL** | `/plan/generate` |
| **Компонент** | `PlanGenerate2026` |
| **Раздел** | План |
| **Задача** | Настройка и запуск генерации меню |
| **Как попасть** | Empty state «Сегодня»; семья «Составить меню»; legacy `/menu/generate` |
| **Как уйти** | После генерации → план/сегодня; back |

| Поле | Значение |
|------|----------|
| **Название** | Рецепты (каталог) |
| **URL** | `/plan/recipes` |
| **Компонент** | `RecipeCatalog2026` |
| **Раздел** | План |
| **Задача** | Каталог рецептов, поиск, избранное, replace mode |
| **Как попасть** | Subtab «Рецепты»; replace flow с «Сегодня» |
| **Как уйти** | Карточка рецепта → detail; back |

| Поле | Значение |
|------|----------|
| **Название** | Рецепт (деталь) |
| **URL** | `/plan/recipes/[id]` |
| **Компонент** | `RecipeDetail2026` |
| **Раздел** | План |
| **Задача** | Детали рецепта, в меню, в покупки, замена, избранное |
| **Как попасть** | Каталог; карточка «Рецепт» на «Сегодня» |
| **Как уйти** | «← Каталог»; после «В меню» → `/plan/today`; back |

### A4. Здоровье (2026)

| Поле | Значение |
|------|----------|
| **Название** | Здоровье |
| **URL** | `/wellness` |
| **Компонент** | `WellnessHome2026` |
| **Раздел** | Здоровье (tab) |
| **Задача** | Кольцо дня, метрики, вода, цели, недельная полоска |
| **Как попасть** | Bottom nav; quick action с главной (`returnTo=`) |
| **Как уйти** | Bottom nav; кнопки «Спросить ПланАм», «Отметить приём пищи» |

| Поле | Значение |
|------|----------|
| **Название** | AI помощник |
| **URL** | `/wellness/chat` |
| **Компонент** | `WellnessChat2026` |
| **Раздел** | Здоровье |
| **Задача** | Чат с нутрициологом (AMA-списание) |
| **Как попасть** | Кнопка на `/wellness`; legacy `/health/chat` редирект |
| **Как уйти** | Back header; Telegram back |

### A5. Профиль / Account (2026)

| Поле | Значение |
|------|----------|
| **Название** | Профиль (Account Hub) |
| **URL** | `/account` |
| **Компонент** | `AccountHub2026` |
| **Раздел** | Профиль (tab) |
| **Задача** | Хаб: карточка пользователя, тема, ссылки на подразделы |
| **Как попасть** | Bottom nav «Профиль»; legacy `/profile` редирект |
| **Как уйти** | Карточки hub → подстраницы; bottom nav |

| Поле | Значение |
|------|----------|
| **Название** | Питание |
| **URL** | `/account/nutrition` |
| **Компонент** | `NutritionProfileForm` (embedded) |
| **Раздел** | Профиль |
| **Задача** | Редактирование нутрициологического профиля |
| **Как попасть** | Account hub; wellness empty state |
| **Как уйти** | Back → `/account`; сохранение → returnTo |

| Поле | Значение |
|------|----------|
| **Название** | Семья |
| **URL** | `/account/family` |
| **Компонент** | `FamilyDashboard` (embedded) |
| **Раздел** | Профиль |
| **Задача** | Создание семьи, участники, приглашения |
| **Как попасть** | Account hub |
| **Как уйти** | Back → `/account` |

| Поле | Значение |
|------|----------|
| **Название** | Уведомления |
| **URL** | `/account/notifications` |
| **Компонент** | `NotificationsView` |
| **Раздел** | Профиль |
| **Задача** | Настройки уведомлений и заботы |
| **Как попасть** | Account hub |
| **Как уйти** | Back → `/account` |

| Поле | Значение |
|------|----------|
| **Название** | Настройки |
| **URL** | `/account/settings` |
| **Компонент** | `SettingsHub` (embedded) |
| **Раздел** | Профиль |
| **Задача** | Меню подстраниц настроек |
| **Как попасть** | Account hub |
| **Как уйти** | Пункты меню → подстраницы; back |

| Поле | Значение |
|------|----------|
| **Название** | Аккаунт / Документы / Удалить данные / Поддержка / О приложении |
| **URL** | `/account/settings/account`, `/documents`, `/delete-data`, `/support`, `/about` |
| **Компонент** | Re-export страниц из `/settings/*` |
| **Раздел** | Профиль |
| **Задача** | Соответствующие подразделы настроек |
| **Как попасть** | `/account/settings` |
| **Как уйти** | Back (shell header) → `/account` |

| Поле | Значение |
|------|----------|
| **Название** | Подписка |
| **URL** | `/account/subscription` |
| **Компонент** | `SubscriptionHub2026` |
| **Раздел** | Профиль |
| **Задача** | Тарифы, trial, upgrade |
| **Как попасть** | Account hub; баннер на главной |
| **Как уйти** | Plan cards → checkout; link на Амы |

| Поле | Значение |
|------|----------|
| **Название** | Оформление подписки |
| **URL** | `/account/subscription/checkout` |
| **Компонент** | `PaymentStub2026` |
| **Раздел** | Профиль |
| **Задача** | Stub оплаты подписки |
| **Как попасть** | Subscription hub |
| **Как уйти** | returnTo query; back |

| Поле | Значение |
|------|----------|
| **Название** | Амы |
| **URL** | `/account/ams` |
| **Компонент** | `AmsHub2026` |
| **Раздел** | Профиль |
| **Задача** | Баланс AMA, история |
| **Как попасть** | Account hub |
| **Как уйти** | Back |

---

## B. Legacy-экраны (35 маршрутов, legacy-only или redirect при UI 2026)

### B1. Меню (legacy hub)

| URL | Компонент | Задача |
|-----|-----------|--------|
| `/menu` | `MenuHub` | Хаб меню: обзор, генерация, quick actions |
| `/menu/current` | `MenuCurrentView` | Текущее меню по дням |
| `/menu/generate` | `MenuPlanner` | Мастер генерации меню |
| `/menu/recipes` | `RecipesView` | Каталог рецептов (вкладка меню) |
| `/menu/favorites` | `FavoritesView` | Избранные рецепты |
| `/menu/collections` | `CollectionsView` | Коллекции рецептов |
| `/menu/collections/[id]` | `CollectionDetailView` | Деталь коллекции |
| `/menu/settings` | `MenuSettingsPage` | Настройки меню |
| `/menu/event` | Inline wizard | Планирование события |
| `/menu/scenarios` | redirect → `/menu/recipes` | Совместимость |
| `/menu/leftovers` | redirect → `/shopping/leftovers` | Совместимость |

### B2. Покупки (legacy)

| URL | Компонент | Задача |
|-----|-----------|--------|
| `/shopping` | `ShoppingListView` | Список покупок (legacy UI) |
| `/shopping/pantry` | `PantryDashboard` | Запасы с CRUD |
| `/shopping/leftovers` | `Leftovers2026` или `MealLeftoversPage` | Остатки блюд |
| `/pantry` | redirect → `/shopping/pantry` | Совместимость |

### B3. Рецепты (legacy)

| URL | Компонент | Задача |
|-----|-----------|--------|
| `/recipes` | redirect | → `/plan/recipes` или `/menu/recipes` |
| `/recipes/[id]` | `RecipeDetailLegacy` + `RecipeDetailModal` | Деталь рецепта (модальный UI) |

### B4. Здоровье (legacy)

| URL | Компонент | Задача |
|-----|-----------|--------|
| `/health` | `NutritionistDashboard` | Хаб здоровья |
| `/health/today` | `HealthTodayView` | Здоровье сегодня |
| `/health/chat` | `HealthChatPageClient` | Чат нутрициолога |
| `/health/care` | redirect → `/notifications` | Совместимость |
| `/nutritionist` | redirect → `/health` | Совместимость |
| `/nutritionist/chat` | redirect → `/health/chat` | Совместимость |
| `/nutritionist/care` | redirect → `/health/care` | Совместимость |
| `/progress` | `ProgressDashboard` | Прогресс веса/целей |

### B5. Профиль (legacy)

| URL | Компонент | Задача |
|-----|-----------|--------|
| `/profile` | `ProfileDashboard` | Legacy профиль-хаб |
| `/profile/nutrition` | `NutritionProfileForm` | Профиль питания |
| `/family` | `FamilyDashboard` | Семья |
| `/notifications` | `NotificationsView` | Уведомления |
| `/settings` + 5 подстраниц | `SettingsHub` / scaffold pages | Настройки |
| `/subscription` | `SubscriptionDashboard` | Подписка (legacy) |

### B6. Онбординг

| URL | Компонент | Задача |
|-----|-----------|--------|
| `/onboarding` | `Onboarding2026Flow` или redirect `/profile/nutrition` | Первый запуск / настройка |

---

## C. Admin (9 маршрутов)

| URL | Компонент | Задача |
|-----|-----------|--------|
| `/admin` | `AdminDashboard` (summary) | Сводка |
| `/admin/users` | `AdminDashboard` (users) | Пользователи |
| `/admin/users/[id]` | `AdminUserDetailPage` | Карточка пользователя |
| `/admin/families` | `AdminDashboard` (families) | Семьи |
| `/admin/families/[id]` | `AdminFamilyDetailPage` | Карточка семьи |
| `/admin/subscriptions` | `AdminDashboard` | Подписки |
| `/admin/ams` | `AdminDashboard` | AMA |
| `/admin/openai` | `AdminOpenAiPage` | OpenAI usage |
| `/admin/errors` | `AdminErrorsPage` | Лог ошибок |

**Навигация:** без bottom nav (`HIDDEN_NAV_PREFIXES`).

---

## D. Dev (1 маршрут)

| URL | Компонент | Задача |
|-----|-----------|--------|
| `/dev/planam-2026` | Inline preview page | Превью design system 2026 |

---

## E. Сводка по типам маршрутов

| Категория | Количество page.tsx |
|-----------|---------------------|
| Всего зарегистрированных маршрутов | **71** |
| UI 2026-only (контент) | **22** |
| Legacy-only (контент) | **35** |
| Dual-mode (ветвление по flag) | **14** |
| Чистые redirect (без собственного UI) | **~10** |

**Уникальных экранов с рендеримым UI (без чистых redirect):** **~58**
