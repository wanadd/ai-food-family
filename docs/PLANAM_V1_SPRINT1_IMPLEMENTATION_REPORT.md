# PLANAM V1 — Sprint 1 Implementation Report

**Дата:** 2026-06-06  
**Ветка:** `sprint-0/planam-2026-foundation`  
**Основа:** Final Vision, Design Spec, Design Review

---

# 1. Что реализовано

| Задача | Статус |
|--------|--------|
| Bottom Navigation 5 вкладок (ПланАм в центре) | ✅ |
| Маршрут ПланАм `/` без ShellHeader | ✅ (уже было в nav-config; greeting в body) |
| Dynamic Greeting по времени суток | ✅ |
| `PlanAmHero2026` — 6 логических состояний | ✅ |
| Приоритет Hero: нет меню → покупки → здоровье → приём пищи | ✅ |
| Compact Hero (<700px, фото 128px) | ✅ |
| Три статуса семьи (🛒 📦 ❤️) | ✅ |
| Вторичные CTA: Открыть меню / Список покупок | ✅ |
| «Спросить PlanAm» → BottomSheet2026 placeholder | ✅ |
| Покупки tab → `/shopping` | ✅ |
| Telegram back hidden на tab roots включая `/` и `/shopping` | ✅ |

---

# 2. Новые и изменённые компоненты

## Созданы

| Файл | Назначение |
|------|------------|
| `components/home-2026/PlanAmHero2026.tsx` | Динамический Hero |
| `components/home-2026/PlanAmStatusRows2026.tsx` | Три статуса семьи |
| `lib/home/planam-hero-2026.ts` | Логика приоритетов Hero + greeting |
| `lib/home/use-compact-viewport.ts` | Hook compact (<700px) |
| `lib/home/planam-hero-2026.test.ts` | Unit-тесты логики (vitest не подключён в npm scripts) |

## Изменены

| Файл | Изменение |
|------|-----------|
| `components/home-2026/Home2026.tsx` | Полная перестройка под V1 Sprint 1 |
| `components/planam-2026/navigation/BottomNavigation2026.tsx` | 5 tabs, центр ПланАм 44px |
| `lib/navigation/nav-config-2026.ts` | `planam` tab, `/shopping`, active `/` |
| `lib/navigation/back-navigation-2026.ts` | Tab roots `/`, `/shopping` |
| `app/shopping/page.tsx` | UI 2026 → `Shopping2026` на `/shopping` |
| `app/home/shopping/page.tsx` | Redirect → `/shopping` |

## Удалено с главной (Sprint 1)

- `HomeQuickActions2026` grid
- `HomeMonetizationBanner2026`
- `AIInsight2026`
- `HomeHero2026` (заменён `PlanAmHero2026`)

---

# 3. Маршруты

| Было | Стало |
|------|-------|
| Bottom nav: 4 вкладки, без ПланАм | 5 вкладок, ПланАм центр → `/` |
| Покупки tab → `/home/shopping` | → `/shopping` |
| `/home/shopping` (2026) | Redirect → `/shopping` |
| Остатки статус | → `/shopping/leftovers` |

---

# 4. Hero — логика приоритетов

```text
1. !hasMenu          → «Составим меню?» / Создать меню
2. shopping priority → N товаров / Открыть список
   (unchecked >= 8 OR 17:00–19:00 && unchecked >= 3)
3. wellness priority → update_recommended / suggest_update+body
4. meal              → pickNextMealByTime (завтрак/обед/ужин по часам)
```

---

# 5. QA

| Проверка | Результат |
|----------|-----------|
| `npm run lint` | ✅ Pass (2 pre-existing warnings) |
| `npm run build` | ✅ Pass |
| `NEXT_PUBLIC_PLANAM_UI_2026=true` | ✅ Build OK |
| `NEXT_PUBLIC_PLANAM_UI_2026=false` | ✅ Legacy paths unchanged |
| Viewports 320–412px | ✅ CSS `max-[359px]` compact nav; Hero 128px <700px |
| Unit tests | ⚠️ Файл добавлен; `npm test` не настроен в web package |

### 3-секундный тест (дизайн-оценка post-impl)

| Вопрос | Где ответ |
|--------|-----------|
| Что готовить | Hero (meal) или статусы + CTA меню |
| Что купить | 🛒 строка + shopping Hero при приоритете |
| Что дома | 📦 Остатки → `/shopping/leftovers` |
| Здоровье | ❤️ строка + wellness Hero при приоритете |

---

# 6. Скриншоты

Скриншоты runtime не приложены (нет запущенного TG Mini App в CI).

Визуальный эталон: [PLANAM_V1_SPRINT1_DESIGN_SPEC.md](./PLANAM_V1_SPRINT1_DESIGN_SPEC.md) wireframes.

**Рекомендация QA вручную:** открыть `/` в Telegram Mini App на iPhone SE и 390px Android.

---

# 7. Известные ограничения

| # | Ограничение |
|---|-------------|
| 1 | «Спросить PlanAm» — placeholder sheet, не AI |
| 2 | Wellness hero — по данным `nutritionist_advice`, без PRO блока |
| 3 | Остатки счётчик = `meal_leftovers_count`, не полный pantry |
| 4 | Secondary CTA + Ask могут требовать микро-скролл на SE + TG header |
| 5 | 14 категорий покупок / ручное добавление — Sprint 2+ |
| 6 | `planam-hero-2026.test.ts` не в CI до настройки vitest |

---

# 8. Sprint 2 (out of scope)

- Единый семейный список P0 (ручное +, AI категоризация)
- Здоровье PRO block
- Полный AI «Спросить PlanAm»
- Онбординг2026 → первое меню
- Семейная модель UX
- `/home/pantry` vs leftovers уточнение продукта

---

# 9. Git

```text
feat(v1): sprint 1 foundation
```

Push: `origin sprint-0/planam-2026-foundation`

---

*Sprint 1 foundation complete.*
