# Sprint 3 — Completion Report (Home 2026)

**Дата:** 2026-06-03  
**Ветка:** `sprint-0/planam-2026-foundation`  
**Спринт:** Home 2026 — главный экран продукта

---

## Executive summary

Реализован **Home 2026** на `/` при `NEXT_PUBLIC_PLANAM_UI_2026=true`: Hero с фото блюда, `next_action`, сводка плана (≤3), AI insight (≤2 строки), горизонтальная Photo Rail из `today_meals` с `recipe_id` / `image_url`. Данные — **`GET /menus/overview`** (Home Contract Sprint 0). При `flag=false` — без изменений **`PlanAmHome`**.

---

## API

| Endpoint | Использование |
|----------|----------------|
| `GET /menus/overview` | Единственный источник данных Home 2026 |

### Поля Home Contract (Sprint 0)

| Поле | UI |
|------|-----|
| `plan_summary.has_selected_menu` | Hero / Rail empty vs content |
| `today_meals[]` | Hero dish + Photo Rail |
| `today_meals[].recipe_id` | Tap → `/recipes/[id]` |
| `today_meals[].image_url` | Hero + rail photos |
| `next_action` | Hero CTA + NextAction strip |
| `shopping_unchecked_count` | Plan snapshot «Купить: N» |
| `pantry_expiring_preview` | Snapshot + urgent ring on Hero |
| `nutritionist_advice` | AI Insight (line-clamp 2) |
| `pro_coverage` | Snapshot «План: N%» (PRO) |
| `selected_menu.menu.meals` | `prep_time_minutes`, `calories_estimate` для meta |

Клиент: `fetchMenuOverview()` + cache `menu-overview:{mode}`.

---

## Структура Home (5 зон)

| Зона | Компонент | Поведение |
|------|-----------|-----------|
| Header | в `Home2026` | Дата, приветствие, scope chip |
| 1 Hero | `HomeHero2026` | 16:9 фото, название, время/ккал, **один** Primary CTA = `next_action` |
| 2 Next Action | `NextActionCard2026` | Только для shopping / pantry / meal_outcome / nutrition — без дубля generate/open_today |
| 3 Plan Snapshot | `PlanSnapshot2026` | До 3 чипов из реальных полей |
| 4 AI Insight | `AIInsight2026` | `InsightCard2026`, max 2 lines |
| 5 Photo Rail | `RecipeRail2026` | Horizontal `HeroCard2026` 4:3 |

---

## Новые файлы

```
apps/web/components/home-2026/Home2026.tsx
apps/web/components/home-2026/HomeHero2026.tsx
apps/web/components/home-2026/NextActionCard2026.tsx
apps/web/components/home-2026/PlanSnapshot2026.tsx
apps/web/components/home-2026/AIInsight2026.tsx
apps/web/components/home-2026/RecipeRail2026.tsx
apps/web/components/home-2026/MealFallbackPlate2026.tsx
apps/web/components/home-2026/index.ts
apps/web/lib/home/home-2026-data.ts
apps/web/lib/home/redirect-path-2026.ts
```

### Изменённые

```
apps/web/app/page.tsx
apps/web/lib/menu/overview-types.ts
apps/web/components/planam-2026/layout/ShellHeader2026.tsx  (скрыт на /)
```

---

## Fallback состояния

| Состояние | UI | CTA |
|-----------|-----|-----|
| Loading | `Skeleton2026` Hero + rail + snapshot | — |
| API error | `EmptyState2026` «Обновить» | retry overview |
| Нет меню | Hero без блюда, «Создать первое меню» | `next_action` → generate |
| Новый пользователь (`isNewUser`) | Мягкий copy в Hero / Rail empty | «Создать меню» |
| Нет `image_url` | `MealFallbackPlate2026` по `meal_type` | — |
| Нет блюд в rail | `EmptyState2026` + CTA | `/menu/generate` |
| Shopping count = 0 | Нет snapshot «Купить», нет shopping strip | API не отдаёт shopping action |
| Нет insight body | Зона 4 скрыта | — |
| Snapshot < 3 items | Показываются только доступные метрики | — |

**Запрещённые тексты:** «Нет данных» без CTA — не используются.

---

## Redirect paths (2026)

`lib/home/redirect-path-2026.ts` при flag on:

| Legacy | 2026 |
|--------|------|
| `/menu/current` | `/plan/today` |
| `/shopping` | `/home/shopping` |
| `/shopping/pantry` | `/home/pantry` |
| `/menu/generate` | `/menu/generate` (wizard пока legacy) |

---

## Feature flag

```env
NEXT_PUBLIC_PLANAM_UI_2026=true
```

- `true` → `Home2026` на `/`
- `false` → `PlanAmHome` (legacy HubTile home)

---

## Screenshot checklist (ручная проверка)

Снять в TMA / браузере **390×844**, Light + Dark:

| # | Состояние | Как получить |
|---|-----------|--------------|
| 1 | Home с меню + фото rail | Пользователь с selected menu и `image_url` |
| 2 | Home Hero shopping CTA | `shopping_unchecked_count > 0` |
| 3 | Home без меню | Новый / без selected menu |
| 4 | Home loading | Throttle network |
| 5 | Home error | Offline → «Обновить» |
| 6 | Home fallback plate | Блюдо без `image_url` |
| 7 | Home dark mode | Theme → Тёмная |
| 8 | Legacy Home | `UI_2026=false` |

---

## QA

| Проверка | Результат |
|----------|-----------|
| `npx tsc --noEmit` | ✅ |
| `npm run lint` | ✅ (pre-existing ProfileDashboard) |
| `npm run build` | ✅ `/` bundle 10.6 kB |

---

## Риски

| Риск | Деталь |
|------|--------|
| Низкое покрытие `image_url` | Частый L1 fallback plate |
| Ккал/время только из `selected_menu` | Если нет в JSON — meta без ккал |
| Дубль CTA Hero vs strip | Снижен: strip только для contextual actions |
| `/menu/generate` не в `/plan` | До Sprint 4 wizard |
| Overview latency | Один запрос; cache session |

---

## Готовность к Sprint 4 (Onboarding + Trial UX)

| Рекомендация | Приоритет |
|--------------|-----------|
| WOW overlay G1–G5 после первого меню | P0 |
| `markWowComplete()` + defer phone (CR3 wiring) | P0 |
| Hero P0 `complete_nutrition` → mini-sheet вместо full `/profile/nutrition` | P1 |
| `/plan/generate` route + redirect from legacy | P1 |
| Capture actions (чек / голос) Ghost row на Home | P2 |
| Scope chip → tap opens scope sheet | P2 |

---

## Критерии готовности Sprint 3

| Критерий | ✓ |
|----------|---|
| Новый Home только при flag | ✅ |
| Старый Home при flag off | ✅ |
| Реальные данные overview | ✅ |
| Hero + next_action + Photo Rail | ✅ |
| Не HubTile / не dashboard | ✅ |
| Empty + Skeleton + Dark | ✅ |

---

*Следующий спринт: Onboarding WOW + trial UX (Sprint 4 roadmap).*
