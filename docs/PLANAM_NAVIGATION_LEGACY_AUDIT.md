# PLANAM — Navigation & Legacy UI Audit

Дата: 2026-06-05  
Ветка: `sprint-0/planam-2026-foundation`  
Коммит аудита: (после `docs: audit navigation and legacy UI routes`)

## 1. Краткое резюме

В проде с `NEXT_PUBLIC_PLANAM_UI_2026=true` пользователь видит **оболочку UI 2026** (`AppShell2026`), но значительная часть глубоких экранов всё ещё рендерит **legacy-компоненты** (`ScreenLayout`, cream/stone стили). Главные причины провалов:

1. **Account Hub 2026** (`/account`) ссылается на legacy-маршруты (`/profile`, `/family`, `/settings`, `/notifications`) без 2026-экранов.
2. **Middleware-редиректы выключены по умолчанию** — `NEXT_PUBLIC_PLANAM_ROUTE_REDIRECTS` не `true`, поэтому `/profile` не перенаправляется на `/account`.
3. **Две параллельные системы навигации** — `nav-config.ts` (5 вкладок legacy) и `nav-config-2026.ts` (4 вкладки 2026); часть ссылок в коде всё ещё hardcoded на `/menu`, `/shopping`, `/recipes`.
4. **Кнопка «Назад»** смешивает `router.back()`, статические fallback и `router.push(href)` — без учёта контекста перехода (`returnTo`, `replaceSlot`).
5. **Три словаря категорий покупок** (backend `infer_category`, frontend `category-suggest`, DB `SYSTEM_CATEGORIES`) — расхождение slug и порядок keyword matching дают ошибки вроде «Яйцо куриное → Мясо».

**Рекомендуемая bottom nav:** Сегодня · Покупки · Здоровье · Профиль. Главная `/` — dashboard без отдельной вкладки (доступ через логотип / первый запуск / deep link).

---

## 2. Таблица маршрутов

| Маршрут | Файл page | Компонент | UI | Bottom nav / ссылки | Дубль | Целевой маршрут UI 2026 |
|---------|-----------|-----------|-----|---------------------|-------|-------------------------|
| `/` | `app/page.tsx` | `Home2026` / `PlanAmHome` | 2026 / Legacy | Вкладка «Главная» | `PlanAmHome` | `/` (dashboard, не вкладка) |
| `/home` | `app/home/page.tsx` | redirect → `/` | 2026 guard | matchPrefixes home | `/` | redirect `/` |
| `/plan` | `app/plan/page.tsx` | `PlanWeek2026` | 2026 only | Subtab «Неделя» | `/menu` (legacy) | `/plan` |
| `/plan/today` | `app/plan/today/page.tsx` | `PlanToday2026` | 2026 only | Вкладка «Сегодня» | `/menu/current` | `/plan/today` |
| `/plan/recipes` | `app/plan/recipes/page.tsx` | `RecipeCatalog2026` | 2026 only | Subtab, replace flow | `/menu/recipes`, `/recipes` | `/plan/recipes` |
| `/plan/recipes/[id]` | `app/plan/recipes/[id]/page.tsx` | `RecipeDetail2026` | 2026 only | Plan cards, catalog | `/recipes/[id]` | `/plan/recipes/[id]` |
| `/plan/generate` | `app/plan/generate/page.tsx` | `PlanGenerate2026` | 2026 only | CTA меню | `/menu/generate` | `/plan/generate` |
| `/shopping` | `app/shopping/page.tsx` | redirect → `/home/shopping` | redirect | Legacy tab «Покупки» | `/home/shopping` | `/home/shopping` |
| `/home/shopping` | `app/home/shopping/page.tsx` | `Shopping2026` | 2026 only | Вкладка «Покупки» | `/shopping` | `/home/shopping` |
| `/shopping/pantry` | `app/shopping/pantry/page.tsx` | redirect → `/home/pantry` | redirect | Legacy subtab | `/home/pantry` | `/home/pantry` |
| `/home/pantry` | `app/home/pantry/page.tsx` | `Pantry2026` | 2026 only | Home subtab (1 item) | `/shopping/pantry` | `/home/pantry` |
| `/shopping/leftovers` | `app/shopping/leftovers/page.tsx` | `Leftovers2026` / legacy | Dual | Home sheet + legacy links | Sheet на `/` | Sheet или `/wellness` context |
| `/wellness` | `app/wellness/page.tsx` | `WellnessHome2026` | 2026 only | Home quick action | `/health` | `/wellness` (+ bottom nav) |
| `/wellness/chat` | `app/wellness/chat/page.tsx` | `WellnessChat2026` | 2026 | Кнопка на wellness | `/health/chat` | `/wellness/chat` |
| `/health` | `app/health/page.tsx` | redirect → `/wellness` | redirect | Legacy tab | `/wellness` | redirect |
| `/health/today` | `app/health/today/page.tsx` | redirect → `/wellness` | redirect | Legacy | `/wellness` | redirect |
| `/health/chat` | `app/health/chat/page.tsx` | legacy chat | Legacy | Legacy | `/wellness/chat` | redirect |
| `/profile` | `app/profile/page.tsx` | `ProfileDashboard` | **Legacy UI в 2026 shell** | Account hub, legacy tab | `/account` | `/account` или `/account/profile` |
| `/profile/nutrition` | `app/profile/nutrition/page.tsx` | `NutritionProfileForm` | **Legacy ScreenLayout** | Profile, Wellness | — | `/account/nutrition` (2026) |
| `/account` | `app/account/page.tsx` | `AccountHub2026` | 2026 only | Вкладка «Профиль» | `/profile` | `/account` |
| `/account/subscription` | `app/account/subscription/page.tsx` | `SubscriptionHub2026` | 2026 only | Account hub | `/subscription` | `/account/subscription` |
| `/account/ams` | `app/account/ams/page.tsx` | `AmsHub2026` | 2026 only | Account hub | — | `/account/ams` |
| `/settings` | `app/settings/page.tsx` | `SettingsHub` | **Legacy ScreenLayout** | Account hub | `/account` (migration) | `/account/settings` или sheet |
| `/settings/*` | `app/settings/*/page.tsx` | `SettingsScaffold` + legacy | **Legacy** | Settings hub | — | 2026 settings nested |
| `/notifications` | `app/notifications/page.tsx` | legacy `ScreenLayout` | **Legacy** | Account hub, Profile | — | `/account/notifications` |
| `/subscription` | `app/subscription/page.tsx` | redirect → `/account/subscription` | redirect | ProfileDashboard | `/account/subscription` | redirect |
| `/family` | `app/family/page.tsx` | `FamilyDashboard` | **Legacy** | Account hub, Profile | — | `/account/family` (2026) |
| `/progress` | `app/progress/page.tsx` | redirect → `/wellness` | redirect | ProfileDashboard | `/wellness` | redirect / merge |
| `/menu` | `app/menu/page.tsx` | redirect → `/plan` | redirect | Legacy tab | `/plan` | redirect |
| `/menu/current` | `app/menu/current/page.tsx` | redirect → `/plan/today` | redirect | Legacy | `/plan/today` | redirect |
| `/menu/generate` | `app/menu/generate/page.tsx` | redirect → `/plan/generate` | redirect | Legacy | `/plan/generate` | redirect |
| `/menu/recipes` | `app/menu/recipes/page.tsx` | `RecipesView` | **Legacy, НЕТ redirect при UI_2026** | Legacy tab, `/recipes` redirect | `/plan/recipes` | **redirect `/plan/recipes`** |
| `/menu/*` (остальное) | `app/menu/**` | разные legacy | Legacy | Legacy nav | — | redirect или guard |
| `/recipes` | `app/recipes/page.tsx` | redirect → `/menu/recipes` | **Ведёт в legacy** | Старые ссылки | `/plan/recipes` | redirect `/plan/recipes` |
| `/recipes/[id]` | `app/recipes/[id]/page.tsx` | `RecipeDetailModal` legacy | **Legacy** | Старые deep links | `/plan/recipes/[id]` | redirect `/plan/recipes/[id]` |

**Флаги:**

- Shell: `AppShellBridge.tsx` — при `NEXT_PUBLIC_PLANAM_UI_2026=true` всегда `AppShell2026`.
- Redirects: `middleware.ts` активен только при `NEXT_PUBLIC_PLANAM_ROUTE_REDIRECTS=true` (по умолчанию **выкл**).
- Per-page redirects: многие legacy URL редиректятся в `page.tsx` при UI_2026, но не все (`/menu/recipes`, `/profile`, `/settings`, `/family`, `/notifications`).

---

## 3. Таблица legacy-провалов (UI 2026 → Legacy)

| Откуда | Куда сейчас | Почему legacy | Куда должно | Файл |
|--------|-------------|---------------|-------------|------|
| `/account` → Профиль | `/profile` → `ProfileDashboard` | Hub ссылается на legacy; нет redirect | `/account` (inline) или `/account/profile` 2026 | `nav-config-2026.ts:126`, `AccountHub2026.tsx` |
| `/account` → Настройки | `/settings` → `SettingsHub` | Legacy `ScreenLayout`, cream UI | `/account/settings` 2026 или modal | `nav-config-2026.ts:161` |
| `/account` → Семья | `/family` → `FamilyDashboard` | Legacy компонент | `/account/family` 2026 | `nav-config-2026.ts:133` |
| `/account` → Уведомления | `/notifications` | Legacy `ScreenLayout` | `/account/notifications` 2026 | `nav-config-2026.ts:154` |
| `/account` → Питание (косвенно) | `/profile/nutrition` | Wellness/Profile ссылаются на legacy form | `/account/nutrition` 2026 | `WellnessHome2026.tsx:231`, `WellnessGoalCard2026.tsx:24` |
| `/profile` (legacy dashboard) | `/subscription` | Ссылка в `PROFILE_MENU` | `/account/subscription` (redirect есть) | `ProfileDashboard.tsx:20` |
| `/profile` | `/progress` | Legacy ссылка | `/wellness` | `ProfileDashboard.tsx:21` |
| `/profile` | `/settings` | Gear icon | `/account` settings block | `ProfileDashboard.tsx:29` |
| Главная → Остатки | `LeftoversSheet2026` (sheet) | OK в контексте; альтернатива `/shopping/leftovers` — full page legacy mix | Sheet из home | `HomeQuickActions2026.tsx:44` |
| Главная → Здоровье | `/wellness` | 2026 OK; не в bottom nav | `/wellness` + tab | `HomeQuickActions2026.tsx:54` |
| Главная → Меню | `/plan/today` | 2026 OK | OK | `HomeQuickActions2026.tsx:33` |
| Сегодня → Рецепт | `/plan/recipes/[id]` | 2026 OK | OK | `plan-paths.ts:45`, `PlanMealCard2026.tsx:127` |
| Сегодня → Заменить | `/plan/recipes?replaceSlot=...` | 2026 OK | OK | `PlanToday2026.tsx:255` |
| Рецепт → В меню | `MenuSlotSheet2026` | 2026 sheet OK | OK | `RecipeDetail2026.tsx` |
| Рецепт → В покупки | API call | 2026 OK | OK | `RecipeDetail2026.tsx` |
| Deep link `/recipes` | `/menu/recipes` → `RecipesView` | **Нет UI_2026 redirect** | `/plan/recipes` | `app/recipes/page.tsx:6` |
| Deep link `/menu/recipes` | `RecipesView` в 2026 shell | **Нет page redirect** | `/plan/recipes` | `app/menu/recipes/page.tsx` |
| Deep link `/recipes/[id]` | Legacy modal | Legacy UI | `/plan/recipes/[id]` | `app/recipes/[id]/page.tsx` |
| Middleware off | Прямой заход на `/profile`, `/settings` | `ROUTE_REDIRECTS` false | Auto redirect или 2026 pages | `middleware.ts:7-8` |

---

## 4. Таблица проблем кнопки «Назад»

| Сценарий | Сейчас | Должно быть | Файл | Рекомендация |
|----------|--------|-------------|------|--------------|
| Главная → Остатки (sheet) | Закрытие sheet | Главная | `LeftoversSheet2026` | OK; не router.back |
| Главная → Здоровье → Назад | `router.back()` или fallback `/` | Главная | `back-navigation-2026.ts:39-40` | Добавить `returnTo=/` в push; `/wellness` в MAIN_TAB? |
| Сегодня → Рецепт → Назад | Telegram: `router.back()`; UI: «← Каталог» → `/plan/recipes` | Сегодня | `RecipeDetail2026.tsx:199`, `useTelegramBackButton2026.ts` | «← Каталог» не учитывает entry point; нужен `returnTo` |
| Сегодня → Заменить → Каталог → Назад | Fallback `/plan/today` | Сегодня | `getBackFallback2026` | OK без history; с history — может уйти не туда |
| Заменить → Каталог → Рецепт → Назад | «← Каталог» с `replaceSlot` query | Каталог replace | `RecipeDetail2026.tsx` | OK для Link |
| Профиль (`/account`) → Настройки → Назад | Shell: fallback `/account`; ScreenLayout back: **`/profile`** | Профиль `/account` | `SettingsScaffold.tsx:53`, `ScreenBackNav.tsx:40` | Унифицировать на `/account` |
| Профиль → Подписка → Назад | Fallback `/account` | `/account` | `getBackFallback2026` | OK |
| `/profile` (legacy) → Назад | Shell «Профиль» + нет back в ScreenLayout | `/account` | `ProfileDashboard.tsx` | Убрать legacy route или redirect |
| `/settings/account` → Назад | Link «← Настройки» → `/settings` | `/account` | `SettingsScaffold.tsx:37` | Обновить back target |
| `/notifications` → Назад | «← Профиль» → `/profile` | `/account` | `notifications/page.tsx:36` | Заменить href |
| Nutrition form | `returnTo` param support | Контекст вызова | `NutritionProfileForm.tsx`, `return-to.ts` | Расширить на 2026 paths |

**Реализации back в коде:**

| Механизм | Файлы |
|----------|-------|
| `router.back()` | `useTelegramBackButton2026.ts`, `BottomBackButton.tsx` |
| Fallback push | `getBackFallback2026`, `back-navigation-2026.ts` |
| `router.push(href)` | `ScreenBackNav.tsx`, legacy ScreenLayout backs |
| Telegram BackButton | `useTelegramBackButton2026.ts` |
| «← Каталог» | `RecipeDetail2026.tsx` |
| «← Назад» | `ScreenBack2026.tsx` |

**Корневая проблема:** нет единого `returnTo` / navigation stack; `router.back()` зависит от полной browser history (вкладки, внешние переходы).

---

## 5. Таблица дублей заголовков

| Маршрут | Где дублируется | Оставить | Убрать |
|---------|-----------------|----------|--------|
| `/profile` | `ShellHeader2026` «Профиль» + `ScreenLayout` title «Профиль» | Один в shell | `ScreenLayout` header в legacy pages |
| `/settings` | Shell «Настройки» + `SettingsHub` title «Настройки» | Shell или in-page, не оба | `SettingsHub` h1 |
| `/settings/account` | Shell «Настройки» (prefix match) + scaffold «Аккаунт» | «Аккаунт» in-page | Shell title для leaf routes |
| `/notifications` | Shell «Уведомления» + ScreenLayout «Уведомления» | Shell | ScreenLayout title |
| `/family` | Shell «Семья» + возможный заголовок в dashboard | Shell | In-page duplicate |
| `/plan/today` | Shell «Сегодня» + subtab chip «Сегодня» | Subtabs ИЛИ shell title | Одно из двух |
| `/plan/recipes` | Shell «Рецепты» + subtab «Рецепты» | Subtabs | Shell title на plan routes |
| `/wellness` | Нет shell (скрыт) + local h1 «Здоровье» | Local h1 | OK |
| `/account` | Shell «Профиль» + hub cards без h1 | Shell | OK |

---

## 6. Bottom Navigation

### Текущее состояние (UI 2026)

| Вкладка | Маршрут | id |
|---------|---------|-----|
| Сегодня | `/plan/today` | `plan` |
| Покупки | `/home/shopping` | `shopping` |
| **Главная** (центр) | `/` | `home` |
| Профиль | `/account` | `account` |

Файл: `lib/navigation/nav-config-2026.ts` → `NAV_TABS_2026`.

### Проблемы

1. **Здоровье убрано** из bottom nav (перенесено на главную) — в проде пользователи не находят раздел.
2. **Вкладка «Главная»** дублирует entry в сценарии «Сегодня / Покупки / Здоровье».
3. **Legacy 5-tab nav** (`nav-config.ts`) всё ещё в репо — риск при `UI_2026=false` и путаница в документации.
4. **`/wellness`** не подсвечивает вкладку ( `getActiveTabId2026` → `null`).
5. **Subtabs** на `/plan/*` добавляют второй уровень навигации поверх bottom nav.

### Рекомендованная структура

| Вкладка | Маршрут |
|---------|---------|
| Сегодня | `/plan/today` |
| Покупки | `/home/shopping` |
| Здоровье | `/wellness` |
| Профиль | `/account` |

**Главная `/`:** компактный dashboard без вкладки; открытие через:
- первый экран после онбординга (опционально),
- tap на логотип / «ПланАм» в header,
- deep link `/?home=1`.

---

## 7. Таблица проблем категорий покупок

### Где определяется категория

| Слой | Файл | Когда |
|------|------|-------|
| Backend inference | `apps/api/app/services/shopping_categories.py` → `infer_category()` | Рецепт → покупки, sync menu, pantry |
| Backend DB taxonomy | `apps/api/app/services/shopping_category_service.py` → `SYSTEM_CATEGORIES` | UI groups, manual items |
| Frontend suggest | `apps/web/lib/shopping/category-suggest.ts` | Ручной ввод в legacy shopping/pantry forms |
| UI grouping | `apps/web/lib/dom/shopping-groups.ts` | Отображение в `Shopping2026` |

### Prod-тест (фактический `infer_category`)

| Продукт | Сейчас | Ожидание MVP | Причина ошибки |
|---------|--------|--------------|----------------|
| Яйцо куриное | **мясо** | Яйца | Keyword `курин` в блоке «мясо» раньше «яйца» |
| Яйцо | яйца | Яйца | OK backend; в UI может быть «Другое» если slug не в DB group |
| Мука | бакалея | Бакалея | OK (ранее было «крупы» в client suggest) |
| Ванилин | продукты | Специи и соусы | Нет keyword |
| Уцхо-сунели | продукты | Специи и соусы | Нет keyword |
| Хмели-сунели | продукты | Специи и соусы | Нет keyword |
| Шафран | продукты | Специи и соусы | Нет keyword |
| Томатная паста | **овощи** | Специи и соусы | `томат` в овощах раньше соусов |

### Системные проблемы

1. **Три несовместимых набора slug** (`мясо` vs `мясо_птица`, `овощи` vs `овощи_зелень`).
2. **Порядок keyword matching** — первое совпадение побеждает (яйцо + курица).
3. **Fallback `продукты`** отображается как generic bucket; пользователь видит «Продукты»/«Другое».
4. **Client `category-suggest.ts`** ставит `мука` в `крупы_макароны` — расхождение с backend `бакалея`.
5. **Нет нормализации** составных названий («яйцо куриное» → сначала проверять «яйц»).

### Целевая MVP-схема категорий

| Slug | Label |
|------|-------|
| `овощи_зелень` | Овощи и зелень |
| `фрукты` | Фрукты и ягоды |
| `мясо_птица` | Мясо и птица |
| `рыба_морепродукты` | Рыба и морепродукты |
| `молочные` | Молочное |
| `яйца` | Яйца |
| `крупы_макароны` | Крупы и макароны |
| `бакалея` | Бакалея |
| `специи_соусы` | Специи и соусы |
| `хлеб_выпечка` | Хлеб и выпечка |
| `напитки` | Напитки |
| `заморозка` | Заморозка |
| `другое` | Другое |

Единый mapper: `infer_category` → canonical slug → `SYSTEM_CATEGORIES`.

---

## 8. Рекомендованная целевая структура навигации

```text
Bottom nav:  Сегодня | Покупки | Здоровье | Профиль

/dashboard (/)        — компактная сводка, не вкладка
/plan/today           — план дня
/plan/recipes         — каталог
/plan/recipes/[id]    — рецепт (immersive)
/home/shopping        — покупки
/home/pantry          — запасы (sub-nav или из покупок)
/wellness             — здоровье
/wellness/chat        — AI (nested)
/account              — hub профиля
/account/subscription
/account/settings/*   — вместо /settings
/account/family
/account/notifications
/account/nutrition

Legacy (/menu, /profile, /settings, /recipes) → 301/redirect при UI_2026
```

---

## 9. План исправлений

### P0 (блокеры UX в проде)

1. **Account Hub** — убрать ссылки на `/profile`, `/settings`, `/family`, `/notifications`; заменить на 2026 routes или включить `ROUTE_REDIRECTS=true` в prod.
2. **Redirect `/menu/recipes` и `/recipes`** → `/plan/recipes` при UI_2026 (page-level, не только middleware).
3. **Back navigation** — ввести `returnTo` на все nested transitions; заменить `/profile` в legacy backs на `/account`.
4. **Категории: «Яйцо куриное»** — приоритет «яйц» над «курин»; единый slug mapper к `SYSTEM_CATEGORIES`.
5. **Bottom nav** — вернуть «Здоровье», убрать отдельную вкладку «Главная» (по продуктовому решению).

### P1

1. Дубли заголовков — отключить `ScreenLayout` header на маршрутах с `ShellHeader2026`.
2. Миграция `/profile/nutrition` → `/account/nutrition` (2026 form).
3. `/settings/*` → nested under `/account` с 2026 стилями.
4. Расширить keyword dictionary (специи, грузинские приправы, ваниль).
5. Включить `NEXT_PUBLIC_PLANAM_ROUTE_REDIRECTS=true` в prod docker env.

### P2

1. Удалить/архивировать неиспользуемые legacy hub components из hot path.
2. `Leftovers` — только sheet с главной/сегодня, убрать `/shopping/leftovers` как standalone.
3. E2E navigation tests (back stack, redirects).
4. Синхронизировать `category-suggest.ts` с backend canonical slugs.

---

## 10. Файлы для следующего этапа

### Navigation & routing

- `apps/web/lib/navigation/nav-config-2026.ts`
- `apps/web/lib/navigation/route-migration-2026.ts`
- `apps/web/lib/navigation/back-navigation-2026.ts`
- `apps/web/middleware.ts`
- `apps/web/components/planam-2026/navigation/*`
- `apps/web/components/planam-2026/account/AccountHub2026.tsx`
- `apps/web/app/profile/page.tsx`
- `apps/web/app/settings/**`
- `apps/web/app/menu/recipes/page.tsx`
- `apps/web/app/recipes/page.tsx`
- `apps/web/app/recipes/[id]/page.tsx`
- `apps/web/components/layout/ScreenLayout.tsx`
- `apps/web/components/settings/SettingsScaffold.tsx`
- `apps/web/lib/navigation/return-to.ts`

### Shopping categories

- `apps/api/app/services/shopping_categories.py`
- `apps/api/app/services/shopping_category_service.py`
- `apps/web/lib/shopping/category-suggest.ts`
- `apps/web/lib/shopping/labels.ts`
- `apps/api/tests/test_shopping_infer_category.py`

### Home / wellness

- `apps/web/components/home-2026/HomeQuickActions2026.tsx`
- `apps/web/components/wellness-2026/WellnessHome2026.tsx`
- `apps/web/components/wellness-2026/WellnessGoalCard2026.tsx`

---

## QA при аудите

| Проверка | Результат |
|----------|-----------|
| Статический анализ маршрутов `app/**` | 62 page.tsx |
| Grep navigation patterns | router.push, Link, redirect, back |
| `infer_category` prod samples | см. §7 |
| Код не изменялся | только отчёт |
