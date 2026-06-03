# Sprint 4 — Completion Report (Onboarding WOW 2026)

**Дата:** 2026-06-03  
**Ветка:** `sprint-0/planam-2026-foundation`  
**Спринт:** Onboarding PLANAM 2026 → первый WOW-момент

---

## Executive summary

Реализован **короткий onboarding 2026** (6 шагов) только при `NEXT_PUBLIC_PLANAM_UI_2026=true`. Цель — довести до **первого плана с фото**, не собирать длинную анкету. После WOW вызывается **`markWowComplete()`**, затем переход на **Home 2026**. Телефон **не блокирует** до WOW (Sprint 0 / CR3). Trial **3 дня / 50 Амов** — информационная карточка, не paywall.

---

## Маршруты

| Маршрут | Flag off | Flag on |
|---------|----------|---------|
| `/onboarding` | `redirect` → `/profile/nutrition` (legacy) | `Onboarding2026Flow` |

Новых URL кроме переиспользования `/onboarding` нет.

---

## Сценарий (6 шагов)

| Шаг | UI | API / действие |
|-----|-----|----------------|
| 1 | Кто: solo / couple / family / sport | client state |
| 2 | Цель: время / лучше / похудеть / масса / семья | → `nutrition_goal`, `plan_mode` |
| 3 | Ограничения: нет / аллергии / диета / заболевания | chips → `PUT /nutrition-profile/me` (шаг 4) |
| 4 | Генерация | реальные фазы: save profile → `POST /menus/generate` → `POST /menus/select` |
| 5 | WOW Reveal | `GET /menus/overview` → `today_meals` + фото |
| 6 | «Начать день» | **`markWowComplete()`** → `router.replace('/')` |

**Запрещено в flow:** тарифы, длинные формы, настройки, paywall.

---

## Новые компоненты

| Компонент | Назначение |
|-----------|------------|
| `Onboarding2026Flow` | State machine, шаги 1–5 |
| `Onboarding2026Redirect` | `isNewUser` → `/onboarding` до WOW |
| `OnboardingChipGrid2026` / `OnboardingMultiChip2026` | Выбор chips (DS 2026) |
| `OnboardingProgress2026` | Индикатор шагов |
| `OnboardingGenerateStep2026` | Реальные фазы генерации + retry |
| `OnboardingWowReveal2026` | Hero rail + trial card |
| `TrialWelcomeCard2026` | 3 дня · 50 Амов (не paywall) |

### Lib

| Файл | Назначение |
|------|------------|
| `lib/onboarding-2026/config.ts` | Опции шагов, маппинг в profile / generate |

---

## WOW state

| Ключ | Хранение | Установка |
|------|----------|-----------|
| `planam_wow_complete` | `sessionStorage` = `"1"` | `markWowComplete()` в `lib/planam/onboarding-gate.ts` |

**Вызов:** кнопка «Начать день» на шаге 5 (`OnboardingWowReveal2026` → `handleStartDay`).

**Чтение:** `isWowComplete()` — AppGate phone defer, `Onboarding2026Redirect`.

**Сброс (dev):** `clearWowComplete()` в том же модуле.

### App Gate (CR3)

```ts
shouldBlockForPhone() // defer on → блок телефона только если isWowComplete()
```

Порядок: Legal → (onboarding для `isNewUser`) → … → Phone **после** WOW.

---

## API

| Endpoint | Когда |
|----------|-------|
| `PUT /nutrition-profile/me` | Перед генерацией (минимальный patch, `completed: true`) |
| `POST /menus/generate` | 5 дней, goal/plan_mode из wizard |
| `POST /menus/select` | Вариант `balanced` или первый доступный |
| `GET /menus/overview` | WOW: фото `today_meals[].image_url` |
| `GET /subscriptions/me` | Опционально: баланс Амов на trial card |

**Без фейковой загрузки:** UI показывает фазу (`saving_profile` → `generating` → …) по факту await.

---

## Trial UX

| Параметр | Значение |
|----------|----------|
| Константы | `ONBOARDING_TRIAL_DAYS = 3`, `ONBOARDING_TRIAL_AMS = 50` |
| UI | `TrialWelcomeCard2026` — «Знакомство с ПланАм», без CTA оплаты |
| Баланс | Если `subscription.ama_balance` есть — показываем фактический остаток |

Согласовано с Sprint 0 (`TRIAL_DAYS=3`, welcome 50 AMS).

---

## Изменённые файлы

```
apps/web/app/onboarding/page.tsx
apps/web/components/AppProviders.tsx
apps/web/components/auth/AppGate.tsx
apps/web/components/layout/AppShellBridge.tsx
apps/web/lib/onboarding-2026/config.ts
apps/web/components/onboarding-2026/*
docs/SPRINT_4_COMPLETION_REPORT.md
```

---

## UI / DS

- Только **PLANAM 2026**: `Button2026`, `Card2026`, `HeroCard2026`, `EmptyState2026`, `Skeleton2026`
- Full-screen onboarding без bottom nav (`AppShellBridge` bypass для `/onboarding`)
- Light/Dark через `ThemeProvider`

---

## QA

| Проверка | Результат |
|----------|-----------|
| `npx tsc --noEmit` | ✅ |
| `npm run lint` | ✅ |
| `npm run build` | ✅ (`/onboarding` 6.18 kB) |

### Ручной сценарий

1. `NEXT_PUBLIC_PLANAM_UI_2026=true`
2. Новый пользователь (или dev auth `is_new`)
3. Legal → `/onboarding` → шаги 1–3 < 30 с
4. Шаг 4 — реальная генерация
5. Шаг 5 — фото в rail
6. «Начать день» → `/` Home 2026
7. Phone gate может появиться **после** WOW

---

## Риски

| Риск | Митигация |
|------|-----------|
| Генерация > 90 с | 5 дней, не 7; retry на ошибке |
| `isNewUser` только один раз | Returning users без меню не форсятся — можно открыть `/onboarding` вручную |
| Нет фото в overview | WOW rail + fallback plate |
| Лимит AMS / generate error | `ApiRequestError` message + retry |
| Session WOW теряется при закрытии TMA | sessionStorage — ожидаемо для CR3 |

---

## Готовность к Sprint 5 (Recipes / Plan)

| Готово | Задача Sprint 5 |
|--------|-----------------|
| ✅ Profile minimal в onboarding | Расширение не в WOW path |
| ✅ Menu selected после WOW | Home + `/plan/today` контент |
| ✅ `/plan/recipes` stub | Каталог-витрина с фото 1:1 |
| ⏳ `/plan/generate` wizard overlay | Вынести generate из `/menu/generate` |
| ⏳ G1 welcome story swipe | Опционально перед chips |

---

## Критерии готовности Sprint 4

| Критерий | ✓ |
|----------|---|
| Короткий onboarding (не анкета) | ✅ 3 tap + generate + reveal |
| Реальная генерация | ✅ |
| WOW с фото / fallback | ✅ |
| `markWowComplete()` | ✅ на «Начать день» |
| Home 2026 после WOW | ✅ `/` |
| Телефон после WOW | ✅ CR3 |
| Trial 3d/50 без paywall | ✅ |
| Только при UI_2026 flag | ✅ |
| Legacy onboarding при flag off | ✅ redirect nutrition |

---

*Следующий спринт: Recipes 2026 + наполнение `/plan/*`.*
