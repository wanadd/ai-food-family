# Sprint 8 — Completion Report (Забота / Wellness 2026)

**Дата:** 2026-06-03  
**Ветка:** `sprint-0/planam-2026-foundation`  
**Спринт:** Wellness Home · Today Status · AI Insight · Goal · Progress · AI Coach · Home · Empty · Dark · Performance

**Эталоны:** [`PLANAM_UX_UI_2026_MASTER_SPEC.md`](PLANAM_UX_UI_2026_MASTER_SPEC.md) §5.9 · [`DOMAIN_ARCHITECTURE.md`](DOMAIN_ARCHITECTURE.md) §3.9 · [`SPRINT_7_COMPLETION_REPORT.md`](SPRINT_7_COMPLETION_REPORT.md)

**Условие:** `NEXT_PUBLIC_PLANAM_UI_2026=true`. Миграция URL: `NEXT_PUBLIC_PLANAM_ROUTE_REDIRECTS=true`.

---

## Executive summary

Раздел **Забота** (`/wellness`) — единый scroll без «медкабинета»: прогресс дня, карточка «Сегодня», вода, один совет (≤2 строки), цель из профиля, простая полоска недели, кнопка **«Спросить ПланАм»** → существующий `NutritionistChat` на `/wellness/chat`. Home 2026 получил **Wellness chip** (вода, insight, прогресс цели). Legacy `/health`, `/health/today`, `/health/chat`, `/progress` редиректят на 2026-маршруты при включённом флаге.

---

## Части спринта

| # | Требование | Статус | Реализация |
|---|------------|--------|------------|
| 1 | `/wellness` — главный экран, реальные данные | ✅ | `WellnessHome2026` |
| 2 | Карточка «Сегодня» (съедено / осталось / вода / активность) | ✅ | `WellnessTodayCard2026` + `buildWellnessTodayMetrics` |
| 3 | AI insight — одна рекомендация, ≤2 строк, не чат | ✅ | `WellnessInsight2026` + `buildWellnessInsight` |
| 4 | Goal card из профиля | ✅ | `WellnessGoalCard2026` + `wellnessGoalLabel` |
| 5 | Progress 7 дней — просто, без графиков | ✅ | `WellnessWeekStrip2026` + `buildWeekStrip` |
| 6 | AI Coach — кнопка → существующий чат | ✅ | `/wellness/chat` → `WellnessChat2026` |
| 7 | Home: wellness status, insight, goal progress | ✅ | `WellnessChip2026` + `buildHomeWellnessChip` |
| 8 | Empty states + CTA | ✅ | `EmptyState2026` на экране и в goal/water |
| 9 | Dark mode | ✅ | `pa-*`, `dark:` на всех блоках |
| 10 | Производительность — без chart libs | ✅ | CSS `conic-gradient` + div-bars |

---

## Маршруты

| Маршрут | Экран | Legacy (flag off) |
|---------|--------|-------------------|
| `/wellness` | `WellnessHome2026` | `/health`, `/health/today` → redirect при flag on |
| `/wellness/chat` | `WellnessChat2026` | `/health/chat`, `/nutritionist` |
| `/progress` | — | redirect → `/wellness` при flag on |

Подвкладки «Забота»: один пункт **«Сегодня»** (`/wellness`) — чат не в tab, только кнопка на экране (Master Spec §5.10).

---

## Новые артефакты

### Components (`components/wellness-2026/`)

| Компонент | Назначение |
|-----------|------------|
| `WellnessHome2026` | Orchestrator: загрузка данных, scroll |
| `WellnessDayRing2026` | Прогресс дня % |
| `WellnessTodayCard2026` | 4 метрики «Сегодня» |
| `WaterIntake2026` | Вода + стакан 250 мл |
| `WellnessInsight2026` | Один совет, `line-clamp-2` |
| `WellnessGoalCard2026` | Цель + % к цели |
| `WellnessWeekStrip2026` | 7 столбиков недели |
| `WellnessChip2026` | Home: вода + insight + goal % |
| `WellnessChat2026` | Обёртка `NutritionistChat` |

### Lib (`lib/wellness/`)

| Файл | Назначение |
|------|------------|
| `wellness-status.ts` | Метрики дня, ring %, подсчёт checkins |
| `wellness-insight.ts` | Короткий insight (overview / вода / белок) |
| `goal-labels.ts` | Человекочитаемые цели |
| `week-strip.ts` | 7 дней из history + сегодня |
| `home-wellness.ts` | DTO для Home chip |

### Расширения

| Файл | Изменение |
|------|-----------|
| `lib/progress/api.ts` | `fetchProgressHistory` |
| `lib/home/redirect-path-2026.ts` | `/health/*`, `/progress` → wellness |
| `Home2026.tsx` | Parallel load progress/water/checkins + `WellnessChip2026` |
| `health/*`, `progress/page.tsx` | Redirect при UI 2026 |

---

## API (существующие endpoint)

| Endpoint | Использование |
|----------|----------------|
| `GET /menus/overview` | Совет нутрициолога, план дня, goal_label |
| `GET /progress/me` | КБЖУ факт/план, цель %, тренировки недели |
| `GET /progress/history` | Полоска недели (дни с весом) |
| `GET /nutritionist/water/today` | Вода сегодня |
| `POST /nutritionist/water` | +250 мл |
| `GET /meal-checkins/today` | Выполненные приёмы пищи |
| `GET /nutrition-profile/me` | Полнота профиля, nutrition_goal |
| `POST /nutritionist/ask` | Чат (через `NutritionistChat`) |

Новых backend endpoint не добавлялось.

---

## AI integration

| Аспект | Реализация |
|--------|------------|
| Insight на `/wellness` | Приоритет: `overview.nutritionist_advice.body` → эвристики (вода, белок, приёмы) |
| Insight на Home | `WellnessChip` — `buildWellnessInsight`; отдельно `AIInsight2026` — совет из меню (`buildAiInsight`) |
| Чат | Тот же `NutritionistChat`, AMS, disclaimer в footer |
| Новый AI-сервис | **Не создавался** |

---

## Интеграция с Home 2026

| Элемент | Поведение |
|---------|-----------|
| `WellnessChip2026` | Клик → `/wellness`; кольцо воды %; insight `line-clamp-2`; badge goal % |
| Загрузка | `fetchMenuOverview` + `fetchProgressOverview` + `fetchWaterToday` + checkins + profile |
| `AIInsight2026` | Сохранён для совета по меню (не дублирует chip при разных текстах) |
| Redirects | `complete_nutrition` → `/profile/nutrition` |

---

## Empty states

| Состояние | CTA |
|-----------|-----|
| Ошибка загрузки | «Обновить» |
| Нет цели/меню/данных | «Настроить питание» + «Создать меню» |
| Цель не задана (card) | Link `/profile/nutrition` |
| Нет initData в чате | Текст про Telegram |

---

## QA

| Проверка | Результат |
|----------|-----------|
| `npx tsc --noEmit` | ✅ |
| `npm run lint` | ✅ (pre-existing `ProfileDashboard` img warning) |
| `npm run build` | ✅ |

### Ручной сценарий

1. `NEXT_PUBLIC_PLANAM_UI_2026=true`
2. `/wellness` — ring, сегодня, вода (+ стакан), совет, цель, неделя
3. «Спросить ПланАм» → чат, ответ, списание Амов
4. Home → chip Забота → `/wellness`
5. `/health` → redirect `/wellness`
6. Light/Dark

---

## Риски

| Риск | Митигация |
|------|-----------|
| Два insight на Home (chip + menu) | Разные источники; chip — wellness, AIInsight — план меню |
| Неделя: прошлые дни только по весу в history | Документировано; без checkin history API |
| PRO progress dashboard | `/progress` редирект на wellness; тяжёлый PRO UI — legacy при flag off |
| Insight из overview может совпадать с menu insight | Приоритет overview на wellness; дедуп на Home не форсирован |
| `conic-gradient` в dark | При необходимости — токены sage/cream в polish |

---

## Критерии готовности Sprint 8

| Критерий | ✓ |
|----------|---|
| Оценить свой день | ✅ ring + карточка «Сегодня» |
| Видеть прогресс | ✅ день % + неделя |
| Получать рекомендации | ✅ insight ≤2 строк |
| Перейти в AI | ✅ `/wellness/chat` |
| Забота без legacy UI при flag on | ✅ redirects `/health/*` |
| Не медкабинет / не MFP / не chart libs | ✅ |

---

## Gaps (следующие спринты)

| Gap | Примечание |
|-----|------------|
| `/wellness/progress` PRO teaser | Отдельный PRO экран не в Sprint 8; базовая неделя на home scroll |
| Checkin history по 7 дням | Нет API — полоска опирается на weight history |
| Deferred advice UI | Legacy в `HealthTodayView`; не перенесён в 2026 scroll |
| `home_next_action` «белок сегодня» для спортсмена | Rule engine без изменений |

---

*Следующий фокус: polish Account 2026, PRO wellness teaser, или объединение BFF `wellness-day` endpoint.*
