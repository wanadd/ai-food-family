# Sprint 0 — Completion Report

**Дата:** 2026-06-03  
**Ветка:** `sprint-0/planam-2026-foundation`  
**Основа:** [`PLANAM_2026_IMPLEMENTATION_ROADMAP.md`](PLANAM_2026_IMPLEMENTATION_ROADMAP.md) Sprint 0

---

## Executive summary

Sprint 0 закрывает **блокеры CR1–CR5** перед Sprint 1 (Design System). Выполнены: decision record, расширение API overview для Home 2026, AppGate/phone defer, документация payment, исправление parallax в спеках, feature flags, частичный fix admin route, unit-тесты rule engine.

**Security Phase 0 (P0-3 webhook, P0-5 recipes)** — **не в scope CR1–CR5**; вынесены в Sprint 0 parallel track → **старт Sprint 1** (см. §7).

---

## CR1 — Trial decision

### Анализ as-is

| Файл | Значение |
|------|----------|
| [`subscription_catalog.py`](../apps/api/app/services/subscription_catalog.py) | `TRIAL_DAYS=14`, `monthly_ams=200` |
| [`subscription.py`](../apps/api/app/services/subscription.py) | welcome AMS из plan seed |
| Docs funnel | 3d / 50 AMS |

### Решение (DR-001)

| Параметр | 2026 |
|----------|------|
| Trial | **3 дня** |
| Welcome AMS | **50** |
| Menu gens in trial | **5** |

### Изменения

| Файл | Изменение |
|------|-----------|
| `apps/api/app/services/subscription_catalog.py` | `TRIAL_DAYS=3`, `TRIAL_WELCOME_AMS=50`, `TRIAL_MENU_GENERATIONS=5` |
| `apps/api/app/services/subscription.py` | fallback `TRIAL_WELCOME_AMS` |
| `docs/PLANAM_2026_DECISION_RECORD.md` | **новый** |

### Риски

| Риск | Митигация |
|------|-----------|
| Существующие trial 14d в БД | Не трогаем `trial_ends_at`; только новые пользователи |
| `seed_subscription_plans` обновит plan row на deploy | OK — monthly_ams trial станет 50 для catalog |
| Docs mockups «14 дней» | Исправить в Sprint 1 copy pass |

### Статус: **Закрыт** (код + decision record)

---

## CR2 — Home contract

### Анализ as-is

| Файл | Проблема |
|------|----------|
| [`schemas/menu_overview.py`](../apps/api/app/schemas/menu_overview.py) | `MenuTodayMeal` без `recipe_id`, `image_url` |
| [`meal_attendance.py`](../apps/api/app/services/meal_attendance.py) `extract_today_meals` | не читал `recipe_id` из JSON |
| [`menu_overview.py`](../apps/api/app/services/menu_overview.py) | нет `next_action` |
| Endpoint `GET /menus/overview` | **существует** |

### Решение

Расширить `MenuOverviewResponse`:

| Поле | Тип |
|------|-----|
| `today_meals[].recipe_id` | `int \| null` |
| `today_meals[].image_url` | `str \| null` |
| `next_action` | `HomeNextAction` |
| `shopping_unchecked_count` | `int` |
| `pantry_expiring_preview` | `PantryExpiringPreview \| null` |

Rule engine P0–P5: [`home_next_action.py`](../apps/api/app/services/home_next_action.py)

### Изменения

| Файл | Изменение |
|------|-----------|
| `apps/api/app/schemas/menu_overview.py` | новые модели |
| `apps/api/app/services/meal_attendance.py` | `recipe_id` + `enrich_today_meals_images()` |
| `apps/api/app/services/home_next_action.py` | **новый** |
| `apps/api/app/services/menu_overview.py` | wire compute + enrich |
| `apps/api/tests/test_home_next_action.py` | **новый**, 2 passed |

### Риски

| Риск | Митигация |
|------|-----------|
| `redirect_path` пока legacy (`/menu/generate`) | Sprint 2 redirects `/plan/*` |
| N+1 если клиент игнорирует `image_url` | overview уже отдаёт URL |
| `get_shopping_list` fail → count 0 | try/except в engine |

### Статус: **Закрыт** (API extension без миграции БД)

---

## CR3 — AppGate flow

### Анализ as-is

| Файл | Поведение |
|------|-----------|
| [`AppGate.tsx`](../apps/web/components/auth/AppGate.tsx) | legal → **phone блокирует** → children |
| [`PhoneRequiredScreen`](../apps/web/components/auth/PhoneRequiredScreen.tsx) | skip через API |
| WOW после phone в спеках | несовместимо |

### Решение (DR-003)

1. `NEXT_PUBLIC_PLANAM_DEFER_PHONE_GATE=true` (default)
2. Phone gate только если `planam_wow_complete=1` в sessionStorage **или** defer off
3. `/admin/*` **bypass** AppGate (AdminShell + initData)
4. Sync `captureAdminSessionFromUrl` в AppGate + `AdminSessionBootstrap`

### Изменения

| Файл | Изменение |
|------|-----------|
| `apps/web/lib/planam/feature-flags.ts` | **новый** |
| `apps/web/lib/planam/onboarding-gate.ts` | **новый** + `markWowComplete()` |
| `apps/web/components/auth/AppGate.tsx` | defer phone + admin bypass + sync capture |
| `apps/web/components/AppProviders.tsx` | `AdminSessionBootstrap` |
| `apps/web/.env.example` | env flags |

### Риски

| Риск | Митигация |
|------|-----------|
| Legal всё ещё до WOW | compliance OK |
| `markWowComplete()` не вызывается до Sprint 4 | вручную в dev; Sprint 4 hook on `menus/select` |
| Admin bypass без legal | admin users обычно прошли регистрацию |

### Статус: **Закрыт** (gate logic); WOW hook — **Sprint 4**

---

## CR4 — Parallax conflict

### Анализ

| Doc | Текст |
|-----|-------|
| Master Spec §5.5 | parallax |
| Design System §10 | запрет parallax |

### Решение

**No parallax.** Правка Master Spec (2 места).

### Изменения

| Файл | Изменение |
|------|-----------|
| `docs/PLANAM_UX_UI_2026_MASTER_SPEC.md` | static hero |

### Статус: **Закрыт** (docs)

---

## CR5 — Payment scope

### Анализ

- `POST /subscriptions/select-plan` без PSP
- Blueprint M1 checkout future

### Решение

Архитектурный документ: phases UI → checkout adapter → prod; production block on paid marketing.

### Изменения

| Файл | Изменение |
|------|-----------|
| `docs/PLANAM_PAYMENT_ARCHITECTURE_2026.md` | **новый** |

### Статус: **Закрыт** (architecture only, no payment code)

---

## Дополнительно Sprint 0

| Артефакт | Статус |
|----------|--------|
| `docs/PLANAM_2026_DECISION_RECORD.md` | ✅ |
| Feature flags env | ✅ |
| Unit tests | ✅ 2/2 |
| Security P0-1 admin (partial) | ✅ admin route bypass + session capture |
| Security P0-3, P0-5 | ⬜ Sprint 1 parallel |

---

## Файлы изменены (git)

### API

- `apps/api/app/services/subscription_catalog.py`
- `apps/api/app/services/subscription.py`
- `apps/api/app/schemas/menu_overview.py`
- `apps/api/app/services/home_next_action.py` (new)
- `apps/api/app/services/meal_attendance.py`
- `apps/api/app/services/menu_overview.py`
- `apps/api/tests/test_home_next_action.py` (new)

### Web

- `apps/web/components/auth/AppGate.tsx`
- `apps/web/components/AppProviders.tsx`
- `apps/web/lib/planam/feature-flags.ts` (new)
- `apps/web/lib/planam/onboarding-gate.ts` (new)
- `apps/web/.env.example`

### Docs

- `docs/PLANAM_2026_DECISION_RECORD.md` (new)
- `docs/PLANAM_PAYMENT_ARCHITECTURE_2026.md` (new)
- `docs/PLANAM_UX_UI_2026_MASTER_SPEC.md` (parallax)
- `docs/SPRINT_0_COMPLETION_REPORT.md` (this file)

---

## API contract reference (Home 2026)

```json
{
  "today_meals": [
    {
      "meal_type": "breakfast",
      "label": "Завтрак",
      "name": "Овсянка",
      "recipe_id": 42,
      "image_url": "https://cdn.example/recipes/42/hero.webp"
    }
  ],
  "next_action": {
    "id": "shopping",
    "cta_label": "Докупить 3 позиций",
    "redirect_path": "/shopping",
    "subtitle": "Список из вашего меню",
    "metadata": { "unchecked_count": 3 }
  },
  "shopping_unchecked_count": 3,
  "pantry_expiring_preview": { "name": "Молоко", "days_until_expiry": 1 }
}
```

---

## Готовность к Sprint 1

| Track | Sprint 1 задачи | Ready? |
|-------|-----------------|--------|
| **Design System** | CSS vars dark, Button/Card/Skeleton, ThemeProvider | ✅ |
| **Theme Engine** | `darkMode: 'class'`, semantic tokens from DS | ✅ |
| **New Navigation** | `nav-config-2026`, flag `PLANAM_UI_2026` | ✅ stubs in Sprint 2 |
| **Home Foundation** | consume `next_action` + `today_meals` in new Home component | ✅ API ready |

### Sprint 1 recommended tasks (week 1–2)

1. `apps/web/app/globals.css` — semantic CSS variables Light/Dark  
2. `apps/web/components/ui/ThemeProvider.tsx`  
3. `Button`, `Card`, `Skeleton`, `EmptyState` per DS  
4. `tailwind.config.ts` — `darkMode: 'class'`  
5. Figma parity check (optional)  
6. **Parallel:** Security P0-3, P0-5 (не блокирует DS)

### Sprint 2 preview (depends on S1)

- `nav-config-2026.ts`, 3-tab `BottomNavigation`  
- Route stubs `/plan`, `/home`, `/wellness`  
- `components/home-2026/HomePage.tsx` using `GET /menus/overview`

---

## Verification checklist

- [x] CR1 trial constants in code
- [x] CR2 overview fields + tests
- [x] CR3 AppGate defer + admin bypass
- [x] CR4 docs
- [x] CR5 payment architecture doc
- [x] Decision record
- [x] `.env.example` flags
- [ ] Manual: open TMA after legal without phone (defer on)
- [ ] Manual: `GET /menus/overview` returns new fields
- [ ] Manual: admin `/admin` without phone gate block

---

## GO for Sprint 1

**Да** — при условии merge ветки `sprint-0/planam-2026-foundation` и копирования env flags в local `.env`.

---

*Sprint 0 complete. Next: [`PLANAM_2026_IMPLEMENTATION_ROADMAP.md`](PLANAM_2026_IMPLEMENTATION_ROADMAP.md) Sprint 1.*
