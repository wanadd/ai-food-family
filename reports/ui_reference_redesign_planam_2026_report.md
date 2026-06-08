# PLANAM — UI Reference Redesign Report (2026)

**Дата:** 2026-06-08  
**Ветка:** `feat/ui-reference-redesign-planam-2026`  
**База:** `fix/2026-canonical-deep-links-and-phase1-cleanup`  
**Визуальный референс:** прикреплённое фото consumer nutrition app (адаптировано под PLANAM, не pixel-copy)

---

## 1. Executive summary

Выполнен UI/UX redesign ключевых 2026-экранов по визуальному референсу с сохранением архитектуры PLANAM:

- **Bottom nav:** структура без изменений, единственное переименование **«Сегодня» → «Меню»**
- **Home:** компактная главная (hero + 3 статуса + AI-совет), без «простыни»
- **Меню (`/plan/today`):** компактные карточки блюд по приёмам пищи
- **Recipe detail:** consumer layout, CTA «Начать готовить»
- **Shopping:** убран nested scroll
- **Pantry / Leftovers:** улучшены заголовки и copy
- **Wellness:** progress bars по референсу
- **AI loading:** новый `AiProcessLoading2026` для генерации меню

**Не изменялись:** backend/API/БД/auth/admin/payment/Docker/Telegram bot, legacy redirects, routes.

---

## 2. Bottom nav

| Параметр | Было | Стало |
|----------|------|-------|
| Label первой вкладки | «Сегодня» | **«Меню»** |
| Icon | `today` (часы) | `recipes` (тарелка/меню) |
| href | `/plan/today` | без изменений |
| matchPrefixes | `["/plan"]` | без изменений |
| Количество вкладок | 5 | 5 |
| Порядок | Меню · Покупки · ПланАм · Здоровье · Профиль | без изменений |

**Active state «Меню»** работает для: `/plan/today`, `/plan`, `/plan/generate`, `/plan/recipes`, `/plan/recipes/[id]` (через `getActiveTabId2026` + prefix `/plan`).

**Файлы:** `nav-config-2026.ts`, `NavIcon2026.tsx`

---

## 3. Home

**Структура (по референсу):**

```text
Приветствие + дата
Hero meal card + CTA «Готовить»
3 compact status cards (Купить · Запасы · Меню %)
Совет PLANAM (nutritionist_advice)
```

**Удалено с Home (дубли / простыня):**

- `TodayDishRail2026` (полный список блюд → вкладка «Меню»)
- Quick actions row (Покупки / Запасы / Меню)
- Promo «Из того, что есть дома»
- Отдельная кнопка AI чата

**Добавлено:**

- `PlanAmTip2026` — короткий AI-совет из `overview.nutritionist_advice`
- `formatPlanAmDate()` — подзаголовок с датой
- `menuStatusLabel()` — процент заполненности меню на сегодня
- 3-column grid статусов вместо вертикального списка

**Hero CTA:** «Открыть рецепт» → **«Готовить»**

**Файлы:** `Home2026.tsx`, `PlanAmStatusRows2026.tsx`, `PlanAmTip2026.tsx`, `planam-hero-2026.ts`

---

## 4. Экран «Меню» (`/plan/today`)

| Элемент | Изменение |
|---------|-----------|
| Заголовок | **«Меню»** (было: дата как title) |
| Подзаголовок | «Ваш рацион на сегодня · можно заменить любое блюдо» |
| Карточки блюд | Компактный row layout: thumb + meta + кнопка «+» |
| Группировка | По приёмам пищи (без изменений логики) |
| Даты недели | Horizontal chips (без изменений) |

**Файлы:** `PlanToday2026.tsx`, `PlanMealCard2026.tsx`, `PlanTimelineSection2026.tsx`

---

## 5. Recipe detail + cooking

- Primary CTA: **«Начать готовить»** → smooth scroll к `#recipe-cooking-steps`
- Secondary: «В меню», «Заменить», «В покупки»
- Шаги приготовления: крупные номера, короткие карточки, **без фото шагов**
- Empty state для рецептов без steps

**Файл:** `RecipeDetail2026.tsx`

---

## 6. Shopping

- Удалён `max-h-[70vh] overflow-y-auto` — один page scroll
- Checklist layout сохранён (категории, чекбоксы, количество справа)

**Файл:** `Shopping2026.tsx`

---

## 7. Pantry / Leftovers

### Запасы (`Pantry2026`)

- Заголовок **«Запасы»** + subtitle
- CTA «Из того, что есть дома» (вместо «Подобрать из запасов»)

### Из того, что есть дома (`Leftovers2026`)

- Заголовок **«Из того, что есть дома»**
- Секции: «Подбор из запасов» / «После готовки» (meal leftovers)
- Разделение pantry recipes vs meal portions

---

## 8. Wellness

- Новый `WellnessMetricsBars2026` — progress bars (калории, вода, активность)
- Размещён наверху экрана Здоровье
- AI-совет (`WellnessInsight2026`) сохранён

**Файлы:** `WellnessHome2026.tsx`, `WellnessMetricsBars2026.tsx`

---

## 9. AI loading states

Новый компонент `AiProcessLoading2026`:

- 4 этапа с прогресс-баром
- Визуальная тарелка (fallback)
- Тексты: «PLANAM собирает меню», «Подбираем блюда», …

Интегрирован в `OnboardingGenerateStep2026` (используется и в `PlanGenerate2026`).

---

## 10. Account / Subscription (scope)

**Не мигрировали** в этом PR (Phase 2):

- `NutritionProfileForm`
- `NotificationsView` / `CareSettingsPanel`
- `FamilyDashboard`
- `SettingsScaffold`

`SubscriptionHub2026` — без изменений (уже соответствует soft paywall).

---

## 11. Reference alignment

### Взято из референса

| Элемент | Адаптация |
|---------|-----------|
| Home composition | Hero meal + 3 status chips + AI tip |
| Menu list | Compact meal rows по приёмам пищи |
| Recipe layout | Hero image, метрики, ingredients list, cooking CTA |
| Shopping checklist | Категории + чекбоксы |
| Pantry list | Заголовок «Запасы», сроки справа |
| Wellness progress | Progress bars |
| AI generation loading | Staged process screen |

### Адаптировано под PLANAM

- 5 вкладок bottom nav (не 4 как в референсе)
- Центральная вкладка **ПланАм** (Home), не «Menu» в центре
- Canonical routes `/plan/*`, `/home/pantry`, `/home/leftovers`
- Семейный режим, Telegram Mini App, существующие API
- Термины: «Запасы», «Из того, что есть дома»

### Специально НЕ копировалось

- Чужой бренд и точные пиксели
- Bottom nav референса (4 вкладки: Plan/Menu/Health/Profile)
- Пошаговые фото приготовления
- Новый route `/menu`
- Image CDN pipeline
- 6-я вкладка

### Экраны, ещё не полностью как референс

| Экран | Причина |
|-------|---------|
| Account sub-screens | Legacy UI — Phase 2 migration |
| Plan week (`/plan`) | Минимальные изменения в этом PR |
| Recipe catalog | Без redesign в этом PR |
| Onboarding screens | Частично (только AI loading) |
| Admin | Out of scope |

---

## 12. Build

```bash
cd apps/web && npm run build
```

**Результат:** ✅ exit code 0 (73 pages)

---

## 13. Scope confirmation

| Область | Изменено? |
|---------|-----------|
| `apps/web` frontend UI | ✅ |
| backend/API/БД | ❌ |
| auth/admin/payment | ❌ |
| Docker/Nginx/Telegram bot | ❌ |
| legacy redirects | ❌ |
| routes architecture | ❌ |

---

## 14. Phase 2 (осталось)

1. Migrate Nutrition / Notifications / Family / Settings → 2026 DS
2. Recipe catalog visual polish
3. Plan week thumbnails
4. Pantry search + filter chips (UI only)
5. Leftovers AI picker loading state
6. Subscription visual QA vs reference

---

## 15. Files changed

```text
M  apps/web/lib/navigation/nav-config-2026.ts
M  apps/web/lib/home/planam-hero-2026.ts
M  apps/web/components/planam-2026/navigation/NavIcon2026.tsx
M  apps/web/components/home-2026/Home2026.tsx
M  apps/web/components/home-2026/PlanAmStatusRows2026.tsx
A  apps/web/components/home-2026/PlanAmTip2026.tsx
M  apps/web/components/plan-2026/PlanToday2026.tsx
M  apps/web/components/plan-2026/PlanMealCard2026.tsx
M  apps/web/components/plan-2026/PlanTimelineSection2026.tsx
M  apps/web/components/recipes-2026/RecipeDetail2026.tsx
M  apps/web/components/dom-2026/Shopping2026.tsx
M  apps/web/components/dom-2026/Pantry2026.tsx
M  apps/web/components/dom-2026/Leftovers2026.tsx
M  apps/web/components/wellness-2026/WellnessHome2026.tsx
A  apps/web/components/wellness-2026/WellnessMetricsBars2026.tsx
A  apps/web/components/planam-2026/ui/AiProcessLoading2026.tsx
M  apps/web/components/onboarding-2026/OnboardingGenerateStep2026.tsx
A  reports/ui_reference_redesign_planam_2026_report.md
```
