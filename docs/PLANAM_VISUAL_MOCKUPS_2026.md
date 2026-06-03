# PLANAM Visual Mockups 2026

**Дата:** 2026-06-03  
**Формат:** Telegram Mini App · viewport **390×844** (iPhone 14 class) · `max-w-lg` centered  
**Режим:** документация only — код/API/БД не менялись.

**Основа:** [`PLANAM_UX_UI_2026_MASTER_SPEC.md`](PLANAM_UX_UI_2026_MASTER_SPEC.md) · [`PLANAM_DESIGN_SYSTEM_2026.md`](PLANAM_DESIGN_SYSTEM_2026.md) · [`PLANAM_2026_PRODUCT_BLUEPRINT.md`](PLANAM_2026_PRODUCT_BLUEPRINT.md)

**Легенда wireframe:** `┌─┐` экран · `[···]` фото · `▶` primary CTA · `›` row tap · `░░` skeleton

**Вопрос каждого экрана:** *Что пользователь должен сделать дальше?*

---

## Общая оболочка TMA

| Элемент | Spec |
|---------|------|
| Top | Telegram header (системный), без кастомного app bar на Home |
| Bottom | 3 tabs: **План · Дом · Забота** + overflow `⋯` |
| Safe area | `env(safe-area-inset-bottom)` под tab bar |
| Theme | Light / Dark / System ([`PLANAM_DESIGN_SYSTEM_2026.md`](PLANAM_DESIGN_SYSTEM_2026.md) §13) |

```
┌──────────────────────────────────────┐ 390px
│ ░░░ Telegram WebApp chrome ░░░       │
├──────────────────────────────────────┤
│           SCREEN CONTENT             │
│         (scroll if needed)           │
├──────────────────────────────────────┤
│  План    ● Дом ●    Забота      ⋯   │ 64px + safe
└──────────────────────────────────────┘
```

---

## 1. Home (`/`)

### Цель

Ответить: **«Что мне делать сегодня?»** — один следующий шаг, не каталог функций.

### Wireframe (default · Light)

```
┌──────────────────────────────────────┐
│  Среда, 3 июня          [Личный ▾]   │  Hero + ScopeChip
├──────────────────────────────────────┤
│ ┌──────────────────────────────────┐ │
│ │ ▶  Докупить 3 позиции сегодня   │ │  HomeHero · Primary
│ └──────────────────────────────────┘ │
│  Сегодня                             │  Section Title
│ ┌────────┐ ┌────────┐ ┌────────┐ → │  TodayDishRail
│ │ [ФОТО] │ │ [ФОТО] │ │ [ФОТО] │   │  Hero Card 4:3
│ │ Овсянка│ │ Салат  │ │ Рыба   │   │  Card Title + Caption
│ └────────┘ └────────┘ └────────┘   │
│  Покупки  ████████░░  8/12      ›   │  Action Card strip
│  💧 60%  · Лёгкий ужин…         ›   │  Metric chip + Insight
│  [ Чек ]      [ Голос в боте ]       │  Ghost · bot deep link
├──────────────────────────────────────┤
│  План    ● Дом ●    Забота      ⋯   │
└──────────────────────────────────────┘
```

### Компоненты (DS)

| Зона | Card / control |
|------|----------------|
| Header | Typography Hero + `ScopeChip` |
| Hero | `HomeHero` → **Primary** (1 only) |
| Today | **Hero Card** × 3–5 |
| Strip | **Action Card** (shopping XOR pantry) |
| Bottom glance | **Metric** mini + optional **Insight** (max 1 long) |
| Capture | **Ghost** × 2 |

### CTA

| Приоритет | CTA | Куда |
|-----------|-----|------|
| P0 | Настроим питание за 30 сек | Nutrition mini-sheet |
| P1 | Составить план на неделю | `/plan/generate` |
| P2 | Докупить N позиций | `/home/shopping` |
| P3 | Использовать {product} | `/home/pantry` |
| P4 | Отметить: поели? | `MealOutcomeSheet` |
| P5 | Что готовим сегодня | `/plan/today` |

### Данные (существующие API)

| Блок | API |
|------|-----|
| Scope | `GET /users/me/app-context` |
| Hero rule | `GET /menus/overview` *или* bundle: `menus/selected`, `shopping-lists/me`, `pantry/me`, `nutrition-profile/me`, `meal-checkins/today` |
| Today photos | `recipe_id` → `GET /recipes/{id}` → `image_url` |
| Shopping | `GET /shopping-lists/me` |
| Wellness | water + 1 advice (overview / nutritionist) |

### Состояния

| State | Визуал |
|-------|--------|
| **New user** | Hero P0; Today = empty illustration + copy §8 DS |
| **No menu** | Hero P1; skeleton rail placeholder |
| **Family** | Header avatars (max 4); captions «на 4 порции» |
| **Athlete** | Caption «Белок 120/140 г» на rail |
| **Diet** | Badge на углу фото |

### Empty

«План на неделю за минуту» + Primary **Составить меню** — не «Нет данных».

### Loading

Skeleton: Hero bar + 3× photo rect 4:3 + strip row ([`PLANAM_DESIGN_SYSTEM_2026.md`](PLANAM_DESIGN_SYSTEM_2026.md) §9.1).

### PRO

На Home **нет** PRO gate. Только Micro hint «PRO» на progress chip → tap → `/wellness/progress` teaser.

### Dark

Canvas `#1A1917`; фото **без** dim; Hero Primary `sage-400`; strip border subtle.

---

## 2. Онбординг (overlay flow, не route)

### Цель

Довести до **WOW**: первый персональный план с **фото** ≤ 90 с. Не анкета на 6 аккордеонов.

### Wireframe — цепочка

**G1 Welcome (1 swipe)**

```
┌──────────────────────────────────────┐
│         PLANAM                       │  Page Title
│   [illustration: plate + list]       │
│   Питание и покупки                  │  Body
│   без рутины                         │
│              [ Далее ]               │  Primary
└──────────────────────────────────────┘
```

**G2 Кто вы? (chips)**

```
┌──────────────────────────────────────┐
│  Кто планируем питание?              │
│  [ Один ] [ Пара ] [ Семья ] [ Спорт]│  chips
│              [ Далее ]               │
└──────────────────────────────────────┘
```

**G3 Mini nutrition (sheet)**

```
┌──────────────────────────────────────┐
│  ────                                │
│  Цель питания                        │
│  [ Похудеть ] [ Баланс ] [ Спорт ]   │
│  Аллергии (chips)                    │
│  [ Пропустить ограничения ]          │  Ghost
│  [ Составить план ]                  │  Primary → G4
└──────────────────────────────────────┘
```

**G4 Generate + Reveal**

```
┌──────────────────────────────────────┐
│  Готовим ваш план…                   │
│  ░░░ [card] ░░░ [card] ░░░           │  skeleton
└──────────────────────────────────────┘
        ↓
┌──────────────────────────────────────┐
│  Ваш план готов                      │  Hero type
│  ┌────────────────────────────────┐  │
│  │         [ФОТО 16:9]            │  │
│  │  Завтрак · Обед · Ужин         │  │
│  └────────────────────────────────┘  │
│  [ Начать день ]                     │  Primary → /
└──────────────────────────────────────┘
```

### Компоненты

| Step | DS |
|------|-----|
| G1–G2 | Full-screen cream canvas, Primary only |
| G3 | **Bottom Sheet** |
| G4 | Skeleton → **Hero Card** 16:9 stack |

### CTA

Единственный путь вперёд: **Составить план** → **Начать день**.

### API

`PUT /nutrition-profile/me` · `POST /menus/generate` · `POST /menus/select` · `POST /auth/telegram` + gates уже пройдены.

### Empty / Loading / PRO

Loading = skeleton на G4. Empty не применимо. PRO не показывается. Телефон — banner после WOW, не блокер.

---

## 3. Каталог рецептов (`/plan/recipes`)

### Цель

**Что приготовить из того, что люблю?** — визуальная витрина, не таблица.

### Wireframe

```
┌──────────────────────────────────────┐
│  ← Рецепты              [♥] [⚙ filt] │  Page Title + icons
│  ┌──────────────┐ 🔍 Поиск…         │
├──────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐          │
│  │ [ФОТО1:1]│  │ [ФОТО1:1]│          │  2-col grid
│  │ Салат    │  │ Суп      │          │  Card Title
│  │ 20м·320  │  │ 40м·180  │          │  Caption KBJU·time
│  └──────────┘  └──────────┘          │
│  ┌──────────┐  ┌──────────┐          │
│  │ ...      │  │ ...      │          │
├──────────────────────────────────────┤
│  План    ● Дом ●    Забота      ⋯   │
└──────────────────────────────────────┘
```

### Компоненты

- **Hero Card** variant 1:1 (Recipe Photo)
- Sticky search
- Filters → **Sheet** `sheet-filters`

### CTA

Tap card → `/plan/recipes/[id]`. FAB нет. Secondary: ♥ favorite, filter sheet.

### API

`GET /recipes` · `GET /recipes/filters` · `POST /recipes/{id}/favorite`

### Состояния

| State | UI |
|-------|-----|
| Filters active | Micro chips под search |
| Scenario | query `?scenario=` (legacy compat) |

### Empty

«Сохраняйте любимые блюда» / «Измените фильтры» + CTA сбросить фильтры.

### Loading

2×3 skeleton squares 1:1.

### PRO

Explainability / `why` — в detail, не в grid. Badge «PRO» на chip сценария спорта если gated.

---

## 4. Карточка рецепта (`/plan/recipes/[id]`)

### Цель

**Готовлю это блюдо?** — фото, шаги, КБЖУ, действия в покупки/план.

### Wireframe

```
┌──────────────────────────────────────┐
│  ←                            [♥]  │
│ ┌──────────────────────────────────┐ │
│ │        [HERO PHOTO 16:9]       │ │  full bleed
│ └──────────────────────────────────┘ │
│  Паста с креветками                  │  Page Title
│  25 мин · средне · итальянская       │  Caption
│  ┌────┬────┬────┬────┐               │
│  │320 │28 │12 │40 │               │  Metric Card row KBJU
│  └────┴────┴────┴────┘               │
│  Ингредиенты                         │  Section Title
│  • …                                 │  Body list
│  Приготовление                       │
│  1. …                                │
│  2. …                                │
├──────────────────────────────────────┤
│ [В план]  [В покупки]    [⋯ Ещё]     │  sticky · Primary+Ghost
└──────────────────────────────────────┘
```

### Компоненты

- Hero Photo 16:9
- **Metric Card** × 4 macros
- Body steps numbered
- Sticky footer: **Primary** «В план», **Ghost** «В покупки», **Sheet** «Ещё» (AI why — AMS)

### CTA

| Button | API |
|--------|-----|
| В план | `POST /recipes/{id}/add-to-menu` |
| В покупки | `POST /recipes/{id}/add-to-shopping` |
| Ещё | `GET why/evaluate/improve` (AMS) |

### Empty / Loading

Loading: hero skeleton 16:9 + 4 metric bars. Error: illustration L1 + retry.

### PRO

`evaluate` / `improve` в Sheet с AMS preview; free user видит copy «В подписке дешевле».

---

## 5. Дом — Покупки и Запасы

*В nav центр — Home `/`. Подразделы «Дом» = операционные экраны.*

### 5.1 Покупки (`/home/shopping`)

**Цель:** **Что купить?** — закрыть список.

```
┌──────────────────────────────────────┐
│  ←  Покупки                    [+]   │
│  Сегодня · 8 из 12                   │  Caption progress
├──────────────────────────────────────┤
│  ☐ Молоко              1 л      ›   │  Action row
│  ☑ Хлеб                          │  checked → sage
│  ☐ Курица              500 г       │
│  ...                                 │
│                              [+]     │  FAB add → Sheet
├──────────────────────────────────────┤
│  План    ● Дом ●    Забота      ⋯   │
└──────────────────────────────────────┘
```

| | |
|--|--|
| **Компоненты** | Action Card checklist variant; **Sheet** add item |
| **CTA** | Toggle → pantry toast (1× edu); Primary in sheet «Сохранить» |
| **API** | `GET /shopping-lists/me`, PATCH items |
| **Empty** | «Список появится с планом» + Добавить |
| **Loading** | 6 skeleton rows |
| **PRO** | — |

### 5.2 Запасы (`/home/pantry`)

**Цель:** **Что есть дома?** — использовать до expiry.

```
┌──────────────────────────────────────┐
│  ←  Запасы                     [+]   │
│  Скоро истекает                      │  Section (warm accent)
│  ┌────────────────────────────────┐  │
│  │ Молоко · 2 дня            ›   │  │  Action Card warm border
│  └────────────────────────────────┘  │
│  Все продукты                        │
│  • Рис · 1 кг                        │
├──────────────────────────────────────┤
│  План    ● Дом ●    Забота      ⋯   │
└──────────────────────────────────────┘
```

| | |
|--|--|
| **API** | `GET /pantry/me` |
| **CTA** | Tap expiry → recipe from plan или `/plan/today` |
| **Empty** | «Сфотографируйте чек» + bot link |
| **PRO** | — |

---

## 6. Забота (`/wellness`)

### Цель

**Как я себя чувствую и к чему иду?** — один scroll, не два экрана health/today.

### Wireframe

```
┌──────────────────────────────────────┐
│  Забота                              │  Page Title
│  ┌────────────────────────────────┐  │
│  │      (○) 60% вода              │  │  Metric ring
│  │   [ + стакан ]                 │  │  Ghost compact
│  └────────────────────────────────┘  │
│  ┌────────────────────────────────┐  │
│  │ 💡 Лёгкий ужин лучше до 20:00   │  │  Insight Card (1)
│  │ Рекомендация, не назначение    │  │  Micro disclaimer
│  └────────────────────────────────┘  │
│  Цели питания                    ›   │  Action Card
│  Спросить нутрициолога           ›   │  → /wellness/chat
│  ┌────────────────────────────────┐  │
│  │ Прогресс к цели          PRO › │  │  Metric blur if !pro
│  └────────────────────────────────┘  │
├──────────────────────────────────────┤
│  План    ● Дом ●    Забота      ⋯   │
└──────────────────────────────────────┘
```

### CTA

| Row | Destination |
|-----|-------------|
| + вода | `POST /nutritionist/water/*` |
| Цели | `/account/nutrition` |
| Чат | `/wellness/chat` |
| PRO | `/wellness/progress` |

### API

`GET /nutrition-profile/me` · water endpoints · `GET /progress/me` · deferred-advice (single insight rule)

### Empty

«Начните с воды» + Primary стакан.

### Loading

Ring skeleton + insight block.

### PRO

`Progress` block: Metric Card + overlay «Открыть PRO» → `PaywallSheet` outcome copy, не feature list.

---

## 7. Профиль (`/account` — sheet или screen)

### Цель

**Кто я в PLANAM и кого кормим?** — не ежедневный экран.

### Wireframe (AccountSheet from `⋯`)

```
┌──────────────────────────────────────┐
│  ────                                │
│  Анна                                │  Page Title
│  @telegram · Личный режим            │  Caption
├──────────────────────────────────────┤
│  Кого кормим                     ›   │  family / pair / solo
│  Питание и цели                  ›   │
│  Уведомления                     ›   │
│  Подписка и Амы                  ›   │
│  Пригласить близких              ›   │
│  Оформление · Светлая ▾          ›   │  theme
│  Документы                       ›   │
│  [ Выйти / поддержка ]               │  Ghost
└──────────────────────────────────────┘
```

### CTA

Каждый row → sub-route. Scope change → **Sheet** (не новый tab).

### API

`GET /users/me` · `GET /families/me` · `PATCH /users/me/app-context`

### PRO

Семья / virtual members — badge «Семейный тариф» если feature locked (soft link subscription).

---

## 8. Подписка (`/account/subscription`)

### Цель

**Продолжить результат**, не купить список функций.

### Wireframe

```
┌──────────────────────────────────────┐
│  ←  Ваш ритм питания                 │
│  ┌────────────────────────────────┐  │
│  │  За 14 дней:                   │  │  Metric outcome
│  │  2 плана · 34 позиции куплены   │  │
│  └────────────────────────────────┘  │
│  Пробный период · 1 день остался     │  Caption (trial)
│  ┌────────────────────────────────┐  │
│  │  Личный  249 ₽/мес             │  │  selected card
│  │  План без стресса каждый день   │  │
│  └────────────────────────────────┘  │
│  Совместный · Семейный · PRO         │  collapsed rows
│  Амы: 42  [ Докупить ]               │  Metric + Ghost
│  [ Продолжить ]                      │  Primary checkout
└──────────────────────────────────────┘
```

### CTA

**Продолжить** → checkout (будущий провайдер). **Докупить Амы** → pack sheet.

### API

`GET /subscriptions/me` · `POST /subscriptions/select-plan`

### Empty

Новый пользователь после trial — outcome «Начните с плана» + CTA личный тариф.

### Loading

2 outcome metric skeletons.

### PRO

PRO = **layer card** «Видеть прогресс наглядно», не отдельный мир.

---

## 9. Экран «План / Сегодня» (справочно — ключевой второй экран)

*Запрошен в пакете логикой «меню»; визуально обязателен для команды.*

**Route:** `/plan/today`  
**Цель:** Полный фокус на готовке сегодня.

```
┌──────────────────────────────────────┐
│  ←  Сегодня              [Заменить]  │  Ghost
│ ┌──────────────────────────────────┐ │
│ │ [ФОТО 16:9 Завтрак]              │ │
│ │ [ Готовлю ]              [⋯]    │ │  Hero Card
│ └──────────────────────────────────┘ │
│ ┌──────────────────────────────────┐ │
│ │ [ФОТО Обед]                      │ │
│ └──────────────────────────────────┘ │
│  [ Как прошёл приём пищи? ]         │  Secondary → MealOutcomeSheet
├──────────────────────────────────────┤
│  План    ● Дом ●    Забота      ⋯   │
└──────────────────────────────────────┘
```

---

## 10. Сводка mockups → as-is

| 2026 mockup | As-is (не копировать) | Статус |
|-------------|----------------------|--------|
| `/` Home | `PlanAmHome` + HubTiles | **Rebuild** |
| Onboarding overlay | `/onboarding` → nutrition | **Replace** |
| `/plan/recipes` | `/menu/recipes` grid | **Rebuild** |
| `/plan/recipes/[id]` | `RecipeDetailModal` stone mix | **Rebuild** |
| `/home/shopping` | `/shopping` 3 tabs | **Simplify** |
| `/wellness` | `/health` + `/health/today` | **Merge** |
| `/account` | `/profile` + `/settings` | **Consolidate** |
| `/account/subscription` | `SubscriptionDashboard` feature list | **Rewrite copy** |

---

*Визуальные mockups — источник для Figma. Компоненты строго из [`PLANAM_DESIGN_SYSTEM_2026.md`](PLANAM_DESIGN_SYSTEM_2026.md).*
