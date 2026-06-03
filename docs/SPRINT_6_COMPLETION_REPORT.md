# Sprint 6 — Completion Report (Дом 2026)

**Дата:** 2026-06-03  
**Ветка:** `sprint-0/planam-2026-foundation`  
**Спринт:** Shopping + Pantry + Leftovers + Meal Outcome + Home integration

---

## Executive summary

Реализован единый цикл **Дом** при `NEXT_PUBLIC_PLANAM_UI_2026=true`: покупки (`/home/shopping`), запасы (`/home/pantry`), остатки и результат готовки через **BottomSheet2026** на Home, приоритет **next_action** из `GET /menus/overview` (shopping → pantry → meal_outcome). Legacy `/shopping` и `/shopping/pantry` не изменялись.

---

## Маршруты

| Маршрут | Flag on | Legacy (flag off / migration) |
|---------|---------|-------------------------------|
| `/home/shopping` | `Shopping2026` | `/shopping` |
| `/home/pantry` | `Pantry2026` | `/shopping/pantry`, `/pantry` |
| `/` (Home) | sheets: остатки, meal outcome | — |

**Миграция (opt-in):** `route-migration-2026.ts` — `/shopping` → `/home/shopping`, `/shopping/pantry` → `/home/pantry`.

---

## Части спринта

| # | Требование | Статус |
|---|------------|--------|
| 1 | Shopping 2026: группы, toggle, прогресс, sync | ✅ `Shopping2026` |
| 2 | Pantry 2026: запасы, скоро кончится, избыток | ✅ `splitPantryBuckets` + `Pantry2026` |
| 3 | Leftovers — BottomSheet, не отдельный экран | ✅ `LeftoversSheet2026` |
| 4 | Meal Outcome после готовки | ✅ `MealOutcomeSheet2026` + `createMealCheckin` |
| 5 | Home: next_action shopping/pantry/leftovers | ✅ `resolveHomeRedirectPath`, snapshot chips |
| 6 | Empty states + CTA | ✅ `EmptyState2026` |
| 7 | Skeletons, без спиннеров | ✅ `Skeleton2026` |
| 8 | Dark mode | ✅ `pa-*` / `dark:` |
| 9 | Производительность | ✅ группы + `max-h` scroll, без virtual list (типичный размер списка) |

---

## Новые компоненты

| Компонент | Назначение |
|-----------|------------|
| `Shopping2026` | Сгруппированный список, прогресс, sync из меню, отметка купленного |
| `Pantry2026` | Секции: скоро кончится / избыток / в запасах |
| `LeftoversSheet2026` | Остатки, срок, идеи из `from-pantry` |
| `MealOutcomeSheet2026` | Блюдо → порции осталось → checkin + leftover |

### Lib

| Файл | Назначение |
|------|------------|
| `lib/dom/shopping-groups.ts` | Группировка по категориям, прогресс |
| `lib/dom/pantry-sections.ts` | Бакеты запасов, эвристика «избыток» |

Barrel: `components/dom-2026/index.ts`.

---

## API (существующие, без новых endpoint)

| Endpoint | Использование |
|----------|----------------|
| `GET /shopping-lists/me` | Список покупок |
| `POST /shopping-lists/sync` | Обновить из меню |
| `PATCH /shopping-lists/items/{id}` | Отметка купленного (+ pantry) |
| `GET /shopping-categories` | Метки категорий |
| `GET /pantry/me` | Запасы |
| `DELETE /pantry/items/{id}` | Удаление из запасов |
| `GET /meal-leftovers` | Остатки в sheet |
| `PATCH|DELETE /meal-leftovers/{id}` | Съели / убрать |
| `GET /recipes/from-pantry` | «Что приготовить» в sheet |
| `GET /menus/selected` | Блюда на сегодня для meal outcome |
| `POST /meal-checkins` | `ate_home` или `saved_as_leftover` + `leftover_servings_delta` |
| `GET /menus/overview` | Home: `next_action`, `shopping_unchecked_count`, `meal_leftovers_count` |

---

## Meal Outcome flow

1. Home **next_action** `meal_outcome` → `/?meal_outcome=1` → открывается `MealOutcomeSheet2026`.
2. Выбор блюда из меню на сегодня (`fetchSelectedMenu` + `mealsForDayIndex`).
3. Число порций осталось (0–6).
4. `POST /meal-checkins`:
   - `0` → `actual_status: ate_home`
   - `>0` → `saved_as_leftover` + `leftover_servings_delta` (backend создаёт `meal_leftover`).
5. Invalidate `menu-overview`, `pantry`.

---

## Интеграция с Home 2026

| Элемент | Поведение |
|---------|-----------|
| `NextActionCard2026` / `HomeHero2026` | `resolveHomeRedirectPath(path, use2026, action.id)` |
| `shopping` | → `/home/shopping` |
| `use_pantry_item` | → `/home/pantry` |
| `meal_outcome` | → `/?meal_outcome=1` (sheet) |
| `PlanSnapshot2026` | Клик: shopping / pantry / leftovers sheet |
| `buildPlanSnapshot` | Чип «Остатки: N» при `meal_leftovers_count > 0` |
| Backend priority | `compute_home_next_action` (без изменений в спринте) |

---

## Leftovers sheet

- **Скоро испортится:** `valid_until` ≤ 2 дней.
- **Что осталось:** active/frozen leftovers.
- **Что приготовить:** до 5 рецептов из `GET /recipes/from-pantry` → `/plan/recipes/[id]`.

---

## Pantry «избыток»

Клиентская эвристика (`isExcessPantryItem`): кг ≥ 1, л ≥ 2, шт ≥ 5. Отдельного API нет.

---

## Производительность

- Списки по категориям с collapse (не рендерим тысячи строк flat).
- Scroll контейнер `max-h-[70vh]` на shopping.
- Session cache: `shopping-list`, `pantry`, `menu-overview`.
- Virtualization не подключена — при росте каталога можно добавить в Sprint 7+.

---

## QA

| Проверка | Результат |
|----------|-----------|
| `npx tsc --noEmit` | ✅ |
| `npm run lint` | ✅ (pre-existing `ProfileDashboard` img warning) |
| `npm run build` | ✅ |

### Ручной сценарий

1. `NEXT_PUBLIC_PLANAM_UI_2026=true`
2. Home → next_action «Докупить N» → `/home/shopping`, отметить позиции
3. `/home/pantry` — секции запасов
4. Home → «Остатки дома» или chip 🍲 → sheet
5. next_action «Отметить: поели?» → meal outcome sheet → порции
6. Light/Dark на всех экранах

---

## Риски

| Риск | Митигация |
|------|-----------|
| «Избыток» — эвристика, не доменная модель | Документировано; при появлении API — заменить |
| Нет add/edit item в Shopping 2026 | Toggle + sync покрывают основной цикл; CRUD — legacy или Sprint 7 |
| `meal_outcome` redirect через query | `router.replace` убирает query после открытия sheet |
| `/plan/today` всё ещё stub | Meal outcome на Home, не на plan/today |
| Покупки → pantry только через backend при check | Как в legacy `toggleShoppingItem` |

---

## Критерии готовности Sprint 6

| Критерий | ✓ |
|----------|---|
| Управлять покупками | ✅ |
| Видеть запасы | ✅ |
| Управлять остатками (sheet) | ✅ |
| Обновлять результат приготовления | ✅ |
| Полный цикл внутри PLANAM | ✅ shopping → pantry → outcome |
| Только при UI_2026 | ✅ `requirePlanamUi2026OrRedirect` |
| Legacy без поломки | ✅ |

---

## Готовность к Sprint 7+

| Готово | Далее |
|--------|-------|
| ✅ Дом hub routes | `/plan/today` immersive, wellness |
| ✅ Meal outcome на Home | Расширить на `/plan/today` |
| ⏳ Shopping add item 2026 sheet | Опционально |
| ⏳ Virtualized list | При >100 позиций |

---

*Следующий фокус: План «Сегодня» 2026, Wellness, или polish Дом.*
