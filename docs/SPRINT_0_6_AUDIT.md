# Аудит реализации PLANAM 2026 — Sprint 0–6

**Дата аудита:** 2026-06-03  
**Ветка:** `sprint-0/planam-2026-foundation`  
**Эталоны:** [`PLANAM_UX_UI_2026_MASTER_SPEC.md`](PLANAM_UX_UI_2026_MASTER_SPEC.md) · [`PLANAM_VISUAL_MOCKUPS_2026.md`](PLANAM_VISUAL_MOCKUPS_2026.md) · [`PLANAM_DESIGN_SYSTEM_2026.md`](PLANAM_DESIGN_SYSTEM_2026.md)

**Метод:** сопоставление кода (`apps/web`, `apps/api`), отчётов `SPRINT_*_COMPLETION_REPORT.md` и целевых § Master Spec / Mockups / DS.

**Условие включения 2026 UI:** `NEXT_PUBLIC_PLANAM_UI_2026=true`. Без флага продукт остаётся на legacy UI — это **ожидаемо**, не баг спринтов 0–6.

---

## Сводная матрица (Sprint × готовность)

| Sprint | Фокус | Оценка vs Spec |
|--------|--------|----------------|
| **0** | Контракт Home, trial, gates, flags | **~90%** backend/архитектура |
| **1** | Design System + Theme + primitives | **~85%** токены и базовые компоненты |
| **2** | Nav + routes + shell + account hub | **~55%** IA есть, контент в основном stubs |
| **3** | Home 2026 | **~65%** ядро есть, mockup-детали частично |
| **4** | Onboarding WOW | **~75%** flow рабочий, wireframe G1–G3 упрощён |
| **5** | Recipes 2026 | **~80%** каталог + detail + меню |
| **6** | Дом: shopping, pantry, outcome | **~70%** цикл есть, polish mockups частично |

**Реализовано user routes с контентом (flag on):** 6 из ~22 целевых (Home, onboarding, account hub, shopping, pantry, recipes + detail).  
**Stubs (`RoutePlaceholder2026`):** `/plan`, `/plan/today`, `/wellness`, `/wellness/chat`, `/wellness/progress`.  
**Отсутствуют как routes:** `/plan/generate`, `/plan/favorites`, `/plan/collections`, `/home/capture`, `/account/nutrition`, `/account/notifications`, `/account/subscription`, и др.

---

## 1. Что реализовано полностью

### 1.1 Sprint 0 — Foundation & Home Contract

| Требование Spec / Roadmap | Реализация |
|---------------------------|------------|
| Trial **3 дня / 50 Амов** (DR-001) | `subscription_catalog.py`, `PLANAM_2026_DECISION_RECORD.md` |
| `GET /menus/overview` + Home Contract | `today_meals[].recipe_id`, `image_url`, `next_action`, `shopping_unchecked_count`, `pantry_expiring_preview` |
| Rule engine next_action P0–P5 | `home_next_action.py` + unit tests |
| Phone gate после WOW (CR3) | `onboarding-gate.ts`, `AppGate.tsx`, `NEXT_PUBLIC_PLANAM_DEFER_PHONE_GATE` |
| Feature flags | `NEXT_PUBLIC_PLANAM_UI_2026`, `NEXT_PUBLIC_PLANAM_ROUTE_REDIRECTS` |
| Parallax запрет в спеках | Зафиксировано в Master Spec (без parallax в 2026) |

### 1.2 Sprint 1 — Design System 2026

| Требование DS §1–3, §9 | Реализация |
|------------------------|------------|
| Light / Dark / System | `ThemeProvider`, `ThemeToggle2026`, `pa-*` CSS vars, `darkMode: 'class'` |
| Типографика pa26-* | `globals.css`: hero, page-title, section-title, card-title, body, caption, micro |
| Палитра sage/cream/graphite/warm | `tailwind.config.ts` + semantic `pa-*` |
| 4 типа карточек (базовые) | `HeroCard2026`, `ActionCard2026`, `InsightCard2026`, `MetricCard2026` |
| Primitives | `Button2026`, `Card2026`, `BottomSheet2026`, `EmptyState2026`, `Skeleton2026` |
| Legacy isolation при flag off | `AppShellBridge`, `ThemeProvider active={false}` |
| Dev preview | `/dev/planam-2026` |

### 1.3 Sprint 2 — Navigation & Route skeleton

| Требование Master Spec §4 | Реализация |
|---------------------------|------------|
| SSOT навигации | `nav-config-2026.ts` |
| Центр = **Дом** (`/`) | `NAV_TABS_2026`, `BottomNavigation2026` |
| Подвкладки План / Дом / Забота | `SectionSubTabs2026`, `PLAN_SUBTABS_2026`, `HOME_SUBTABS_2026` |
| Guard 2026 routes | `requirePlanamUi2026OrRedirect` |
| Карта миграции legacy → 2026 | `route-migration-2026.ts` + `middleware.ts` (opt-in) |
| Account entry | `/account` → `AccountHub2026` |

### 1.4 Sprint 3 — Home 2026

| Требование Mockups §1, Master Spec §3 | Реализация |
|---------------------------------------|------------|
| Один источник данных | `GET /menus/overview` |
| Hero + фото 16:9 + один Primary CTA | `HomeHero2026` ← `next_action` |
| Горизонтальная лента «Сегодня» 4:3 | `RecipeRail2026` + `HeroCard2026` |
| Fallback фото | `MealFallbackPlate2026` |
| Plan snapshot (≤3 чипа) | `buildPlanSnapshot` + `PlanSnapshot2026` |
| AI insight (1 блок, clamp) | `AIInsight2026` |
| Empty / error с CTA | `EmptyState2026`, retry overview |
| Skeleton без full-screen spinner | `Skeleton2026` |
| Redirect shopping/pantry → 2026 | `redirect-path-2026.ts` |
| Dark mode на Home | `pa-*`, `dark:` |

### 1.5 Sprint 4 — Onboarding WOW

| Требование Mockups §2 | Реализация |
|-----------------------|------------|
| Короткий wizard, не длинная анкета | 3 chip-шага + generate + reveal |
| Реальная генерация | `POST /menus/generate`, `POST /menus/select` |
| WOW с фото | `OnboardingWowReveal2026` + overview |
| `markWowComplete()` → Home | `onboarding-gate.ts` |
| Trial card без paywall | `TrialWelcomeCard2026` |
| Только при UI_2026 | `app/onboarding/page.tsx` conditional |

### 1.6 Sprint 5 — Recipe Experience

| Требование Mockups §3–4, Media Arch | Реализация |
|------------------------------------|------------|
| `/plan/recipes` 2-col grid 1:1 | `RecipeCatalog2026`, `RecipeGridCard2026` |
| `image_url` + fallback | API mapper + `RecipeImage2026` |
| `/plan/recipes/[id]` immersive hero 16:9 | `RecipeDetail2026`, header hidden |
| КБЖУ, время, сложность, ингредиенты, шаги | Detail layout |
| Добавить / заменить в меню (sheet) | `MenuSlotSheet2026`, `assignRecipeToMenuSlot` |
| Избранное | `toggleRecipeFavorite` |
| Empty / Skeleton / Dark | `EmptyState2026`, `Skeleton2026` |
| CDN width hints | `recipe-media.ts` |

### 1.7 Sprint 6 — Дом (Shopping → Pantry → Outcome)

| Требование Mockups §5, Master Spec §5.6–5.8 | Реализация |
|----------------------------------------------|------------|
| `/home/shopping` новый UI | `Shopping2026` — группы, progress, toggle, sync |
| `/home/pantry` | `Pantry2026` — секции срок / избыток / запасы |
| Остатки не отдельный route | `LeftoversSheet2026` на Home |
| Meal outcome | `MealOutcomeSheet2026` + `createMealCheckin` / leftovers API |
| Home: next_action + snapshot chips | `PlanSnapshot2026` onClick, `meal_outcome` query |
| Существующие API без новых таблиц | shopping-lists, pantry, meal-checkins, meal-leftovers, from-pantry |

---

## 2. Что реализовано частично

### 2.1 Home 2026 (Sprint 3 + доработки 6)

| Элемент Spec (Mockups §1, Master §3.4) | As-is |
|----------------------------------------|--------|
| **ShoppingStrip** — progress + **3 preview items** + tap | Только chip в snapshot «Купить: N», без строк списка |
| **PantryStrip** — 3 expiry lines | Только chip из `pantry_expiring_preview` (1 продукт) |
| **WellnessChip** — вода + mini ring | Нет на Home |
| **Capture** — «Чек» / «Голос в боте» | Нет |
| **ScopeChip** dropdown / avatars (family) | Текстовый pill scope label, без switcher sheet |
| «Минимум скролла» (1 viewport + 1 жест) | Несколько секций (Hero + strip + snapshot + insight + rail + leftovers) — **больше одного жеста** |
| Next Action strip vs Hero | Strip только для shopping/pantry/meal_outcome/nutrition; generate/open_today только в Hero — **OK по intent**, но не полный Action Card shopping row |
| Photo rail tap | Ведёт на **`/recipes/[id]`**, не `/plan/recipes/[id]` при flag on |

### 2.2 Навигация (Sprint 2)

| Элемент Spec | As-is |
|--------------|--------|
| **3 tabs + ⋯ AccountSheet** | **4 tabs:** План · Дом · Забота · **Профиль** (`/account` как tab, не overflow modal) |
| План default child `/plan/today` | Tab href `/plan` (stub неделя) |
| Grace redirects 6 мес | Карта есть, **выключены** по умолчанию (`ROUTE_REDIRECTS=false`) |
| `/home/capture` sheet | Route **не создан** |

### 2.3 План (Sprints 2–5)

| Route Spec | As-is |
|------------|--------|
| `/plan/today` immersive meals | **Stub** `RoutePlaceholder2026` |
| `/plan` неделя + thumbnails | **Stub** |
| `/plan/generate` WOW wizard overlay | **Нет route**; generate через `/menu/generate` и onboarding |
| `/plan/favorites`, `/plan/collections` | **Нет** (избранное — chip в каталоге) |
| Segmented: Favorites из header рецептов | Не реализовано |

### 2.4 Рецепты (Sprint 5)

| Элемент Mockups §3–4 | As-is |
|----------------------|--------|
| Filters → **Bottom Sheet** | Inline chips (meal, favorites), search; `fetchRecipeFilters` загружается, **filter sheet нет** |
| Detail sticky footer: **В план · В покупки · Ещё** | **В меню · Заменить · ★**; нет `add-to-shopping`, нет AI sheet |
| Metric Card row 4 macros | Grid 2×2 metric chips (близко, не отдельные MetricCard) |
| `POST /recipes/{id}/cooked` | Не в 2026 detail |
| Replace dish **AI** (`replace-dish`) | Slot swap через `assignRecipeToMenuSlot` (осознанный компромисс Sprint 5) |

### 2.5 Дом (Sprint 6)

| Элемент Mockups §5 | As-is |
|--------------------|--------|
| Shopping **FAB +** add item sheet | Только toggle + sync; **нет CRUD позиций** в 2026 UI |
| Shopping row swipe delete | Нет |
| Toast «В запасах» при покупке | Legacy toast pattern не перенесён в 2026 (invalidate cache only) |
| Pantry **FAB +** add/edit sheet | Только **удалить**; нет add/edit form 2026 |
| Pantry «избыток» | **Клиентская эвристика** (кг/л/шт), не доменная модель |
| Meal Outcome **3 кнопки** (съели всё / осталось / пропустили) | Wizard: блюдо → порции 0–6 → checkin |
| Tap expiry → recipe / plan today | Нет прямого CTA с pantry row |

### 2.6 Onboarding (Sprint 4)

| Wireframe G1–G4 | As-is |
|-----------------|--------|
| G1 Welcome story (1 swipe) | **Нет** — сразу chips «Кто» |
| G3 Nutrition **mini sheet** | Шаг 3 inline на странице, не sheet |
| Overlay flow (не route) | Остаётся **`/onboarding` route** |
| 6 шагов progress | 5 content + WOW; нумерация в отчёте «6» с учётом CTA |

### 2.7 Account & Wellness

| Spec | As-is |
|------|--------|
| AccountSheet из **⋯** | Full tab + `/account` hub |
| Account sections → `/account/*` | Ссылки на **legacy** `/profile`, `/subscription`, … |
| `/wellness` единый scroll | **Stub** |
| `/wellness/chat`, `/progress` | **Stub** + `planned: true` в sub-tabs |

### 2.8 Design System

| DS компонент / правило | As-is |
|------------------------|--------|
| **PaywallSheet** единый | **Не реализован** (4 паттерна paywall в legacy) |
| **ScopeChip** компонент | Inline header text |
| Touch 44px везде | В основном соблюдено на кнопках 2026; мелкие chips — погранично |
| Запрет emerald/stone в **новых** экранах | Соблюдено в `planam-2026/*`, `home-2026/*`, `recipes-2026/*`, `dom-2026/*` |
| Strangler legacy | **~47 legacy экранов** без миграции — ожидаемо |

---

## 3. Что отклонилось от спецификации

| # | Spec | Реализация | Severity |
|---|------|------------|----------|
| 1 | Bottom nav **3 + ⋯** (Master §4.1, Mockups оболочка) | **4 tabs** с Профилем | **High** — IA и фокус Hero |
| 2 | `/plan/today` — главный «today» immersive | **Stub**; today на Home rail only | **High** |
| 3 | Recipe detail: **В покупки** sticky | Отсутствует в 2026 detail | **Medium** |
| 4 | Meal Outcome: **3-state sheet** (съели / осталось / пропустили) | Multi-step portions flow | **Medium** — API совместим, UX другой |
| 5 | Replace dish: **AI** `POST /menus/replace-dish` | Manual slot replace | **Medium** — product choice |
| 6 | Onboarding: **overlay**, G1 welcome | Route `/onboarding`, без G1 | **Low–Medium** |
| 7 | `/home/capture` bot deep link | Нет route | **Medium** |
| 8 | Backend `next_action.redirect_path` | Legacy paths (`/shopping`); клиент мапит | **Low** (работает при flag) |
| 9 | Rail/detail links | `/recipes/[id]` вместо `/plan/recipes/[id]` | **Low** (дубль route legacy) |
| 10 | `/plan/generate` wizard 6 steps + PaywallSheet preview | Generate в onboarding + `/menu/generate` | **High** для returning users |
| 11 | Shopping/Pantry **FAB +** sheets | Урезанный CRUD | **Medium** |
| 12 | Home **WellnessChip** + capture | Отсутствуют | **Medium** |
| 13 | Account → unified `/account/notifications` | Legacy `/notifications`, care split | **Medium** |
| 14 | Остатки route `/shopping/leftovers` → outcome only | Sheet OK; legacy page остаётся | **Low** |

---

## 4. Технические долги

### 4.1 Архитектура и rollout

| Долг | Описание |
|------|----------|
| **Dual UI** | Два параллельных UI (legacy + 2026); высокая стоимость поддержки и тестирования |
| **Feature flag gate** | Весь 2026 за `NEXT_PUBLIC_PLANAM_UI_2026`; нет поэтапного rollout по % пользователей |
| **Redirects off** | `NEXT_PUBLIC_PLANAM_ROUTE_REDIRECTS` default false — deep links и bookmarks ведут на legacy |
| **Split recipe URLs** | `/recipes/[id]` vs `/plan/recipes/[id]` — риск непоследовательного shell/header |

### 4.2 Backend / Security (Sprint 0 хвост)

| Долг | Источник |
|------|----------|
| Security **P0-3** webhook, **P0-5** recipes | Sprint 0 report — отложено |
| `redirect_path` в API остаётся legacy | Клиент компенсирует; BFF не обновлён под 2026 paths |

### 4.3 Frontend components

| Долг | Описание |
|------|----------|
| **PaywallSheet2026** | Spec требует единый sheet; AMS/paywall в legacy modals |
| **Route stubs** | `/plan`, `/plan/today`, `/wellness/*` — мертвые зоны при включённом flag |
| **Account hub** | Мост на legacy paths, не `/account/*` tree |
| **Shopping/Pantry 2026** | Нет add/edit sheets; дублирование логики с `ShoppingListView` / `PantryDashboard` |
| **Virtualization** | Не внедрена; при больших списках — риск TMA jank |
| **`fetchRecipeFilters`** | Загружается в каталоге, не используется в UI |
| **HOME_SUBTABS** | Дублирующий пункт `/home` → redirect | 

### 4.4 Тесты

| Долг | Описание |
|------|----------|
| E2E 2026 flows | Нет автоматизированных сценариев Home → shopping → pantry → outcome |
| Visual regression | Нет снимков light/dark для 2026 screens |

---

## 5. UX-компромиссы (осознанные)

| Компромисс | Почему | Trade-off |
|------------|--------|-----------|
| **Flag вместо strangler по route** | Безопасный rollout, legacy не ломается | Пользователь без flag не видит 2026 |
| **Профиль как 4-й tab** | Быстрее Sprint 2, проще discovery настроек | Отклонение от «3 + ⋯»; Hero менее «центричен» |
| **Plan today = stub** | Приоритет Home rail + recipes | «Что готовим» размазано между `/` и placeholder |
| **Meal outcome = порции** | Один POST с `saved_as_leftover` | Ближе к данным, дальше от 3-button mockup |
| **Replace = slot assign** | Переиспользование `addRecipeToMenu` / `selectMenu` | Нет AMS preview / AI replace narrative |
| **Pantry excess = heuristic** | Нет API «избыток» | Полезно для UX, может врать |
| **Shopping без add item** | Scope Sprint 6 = «управлять покупками» через check | Power users идут в legacy `/shopping` |
| **Onboarding на `/onboarding`** | Меньше сложности overlay + gates | Deep link «welcome» отдельно от Home |
| **Next Action strip узкий** | Избежать дубля Hero для generate/open_today | Shopping/pantry менее заметны, чем ShoppingStrip mockup |

---

## 6. Риски до Sprint 7

### 6.1 P0 — блокеры продукта при включении flag

| Риск | Impact | Рекомендация Sprint 7 |
|------|--------|------------------------|
| **`/plan/today` stub** | Нет immersive «готовлю сегодня»; bot «Моё меню» → пустышка | Реализовать Plan Today 2026 или redirect на Home с явным CTA |
| **`/wellness` stub** | Таб «Забота» без ценности | Минимальный wellness scroll (вода + insight + links) |
| **4-tab nav vs spec** | Расфокус, сложнее A/B с mockups | Решение: ⋯ sheet + 3 tabs или обновить spec |
| **Redirects off в prod** | Пользователи с `/shopping`, `/menu/current` не попадают в 2026 | План включения `ROUTE_REDIRECTS` + comms |

### 6.2 P1 — целостность цикла «Дом»

| Риск | Impact | Рекомендация |
|------|--------|--------------|
| Recipe links **`/recipes/[id]`** | Старый modal/shell возможен | Унифицировать на `/plan/recipes/[id]` |
| Нет **add-to-shopping** на detail | Разрыв рецепт → покупки | Кнопка + invalidate shopping cache |
| Shopping **без add** | Пустой список без меню — тупик кроме sync | FAB sheet или CTA «Создать меню» |
| **Meal outcome** только с Home query | С `/plan/today` не вызвать | Триггер global sheet из nav-config event |

### 6.3 P2 — качество и монетизация

| Риск | Impact | Рекомендация |
|------|--------|--------------|
| **PaywallSheet** отсутствует | AI/AMS UX остаётся legacy | Sprint 7+ monetization track |
| **Security P0** открыт | Production risk | Параллельный security sprint |
| **Нет E2E** | Регрессии при merge | Smoke: flag on, overview → shopping → check → pantry |
| **Списки без virtualization** | TMA lag на больших семьях | Порог >80 items — virtualize groups |

### 6.4 Соответствие Mockups — Sprint 7 приоритизация

Рекомендуемый порядок по Master Spec / Mockups:

1. **`/plan/today`** — Hero cards per meal, «Готовлю», meal outcome entry  
2. **`/wellness`** — water ring, 1 insight, links (chat/progress можно stubs с copy)  
3. **Home polish** — ShoppingStrip 3 lines OR merge into one Action Card; WellnessChip; capture links  
4. **Nav** — 3+⋯ или документировать отклонение  
5. **`/plan/generate`** wizard для returning users (не только onboarding)  
6. **Recipe detail** — «В покупки», filter sheet  
7. **Rollout** — включить route redirects в staging  

---

## 7. Соответствие Design System 2026 (чеклист)

| Критерий DS | Статус в коде 2026 |
|-------------|-------------------|
| Токены `pa-*` + `.pa26-*` | ✅ |
| Light/Dark/System | ✅ |
| 4 card types | ✅ (используются) |
| 4 button variants `Button2026` | ✅ |
| BottomSheet2026 | ✅ (меню, остатки, outcome) |
| Empty + Skeleton | ✅ |
| No emerald/stone в новых модулях | ✅ |
| PaywallSheet | ❌ |
| Food photography ratios 4:3 / 16:9 / 1:1 | ✅ (Home, recipes, media lib) |
| Fallback plate L1 | ✅ `MealFallbackPlate2026` |
| Touch 44px | ⚠️ частично |
| Sheet 92vh | ⚠️ `max-h-[85vh]` в BottomSheet2026 |

---

## 8. Карта маршрутов: Spec vs Code (flag on)

| Route (Spec) | Code | UI |
|--------------|------|-----|
| `/` | ✅ | Home2026 |
| `/home/shopping` | ✅ | Shopping2026 |
| `/home/pantry` | ✅ | Pantry2026 |
| `/home/capture` | ❌ | — |
| `/plan` | ⚠️ | Placeholder |
| `/plan/today` | ⚠️ | Placeholder |
| `/plan/generate` | ❌ | legacy `/menu/generate` |
| `/plan/recipes` | ✅ | RecipeCatalog2026 |
| `/plan/recipes/[id]` | ✅ | RecipeDetail2026 |
| `/plan/favorites` | ⚠️ | query `favorites_only` |
| `/plan/collections` | ❌ | legacy |
| `/wellness` | ⚠️ | Placeholder |
| `/wellness/chat` | ⚠️ | Placeholder |
| `/wellness/progress` | ⚠️ | Placeholder |
| `/account` | ✅ | AccountHub2026 (legacy links) |
| `/account/*` | ❌ | legacy `/profile`, … |
| `/onboarding` | ✅ | Onboarding2026 (spec: overlay) |
| `/gate/*` | ✅ | AppGate (existing) |

---

## 9. Вывод

**Sprint 0–6 заложили рабочий фундамент 2026:** контракт Home, дизайн-система, навигационный каркас, Home с фото и next_action, onboarding WOW, каталог/карточка рецептов, операционный цикл Дом (покупки → запасы → outcome) при включённом flag.

**До «полного PLANAM 2026» по Master Spec и Mockups** не хватает прежде всего: **Plan Today**, **Wellness**, **навигации 3+⋯**, **generate wizard для returning users**, polish Home (shopping strip, wellness, capture), унификации URL и **production redirects**.

Отчёты спринтов: [`SPRINT_0_COMPLETION_REPORT.md`](SPRINT_0_COMPLETION_REPORT.md) … [`SPRINT_6_COMPLETION_REPORT.md`](SPRINT_6_COMPLETION_REPORT.md).

---

*Документ для планирования Sprint 7+. При изменении spec — обновить §3 (отклонения) и §6 (риски).*
