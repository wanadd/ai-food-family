# PLANAM V1 — Sprint 1.5 Report

**Branch:** `sprint-0/planam-2026-foundation`  
**Scope:** Polish and stabilization (no new features)

---

## P0 Fixes

### P0-1 Hero priority

**Problem:** Wellness hero (`❤️ Здоровье`) showed when meals existed on today.

**Fix:** `resolvePlanAmHeroState()` priority order:

1. Next meal (breakfast / lunch / dinner / snack)
2. No menu
3. Shopping
4. Wellness

**File:** `apps/web/lib/home/planam-hero-2026.ts`

### P0-2 Hero visual

**Problem:** Large emoji placeholders, empty card layout.

**Fix:** Meal state — photo-dominant card with gradient overlay, title, meta, CTA on image. Non-meal states — compact horizontal card (small icon + text), no oversized heart.

**File:** `apps/web/components/home-2026/PlanAmHero2026.tsx`

### P0-3 Color system V1

**Problem:** Mixed legacy cream/sage palette, low contrast.

**Fix:** Fresh V1 tokens — white canvas, saturated green `#2F9E44`, higher contrast text.

**Files:**

- `apps/web/app/globals.css`
- `apps/web/tailwind.config.ts`
- `docs/PLANAM_COLOR_SYSTEM_V1.md`

### P0-4 Shopping categories

**Problems:**

- `Яйцо → Другое`
- Forbidden category `Продукты`
- Mixed items in one bucket

**Fix:**

- Canonical module `apps/web/lib/shopping/categories-v1.ts` (15 categories)
- Classifier audit in `category-suggest.ts` (eggs, berries, broth, nuts, grains, pepper)
- Normalization in `shopping-groups.ts` — legacy `продукты` remapped via name
- Removed `продукты` defaults from shopping drafts

### P0-5 JSON error

**Problem:** `Unexpected end of JSON input` on empty API responses.

**Fix:** `apiFetch()` reads text first, handles empty/`null` body before `JSON.parse`.

**File:** `apps/web/lib/api-client.ts`

---

## P1 Fixes

### P1-1 Plan Today screen

- Page title styling (`pa26-page-title`)
- Day chips use `pa-brand`
- Meal cards match Hero photo-overlay layout

**Files:** `PlanToday2026.tsx`, `PlanMealCard2026.tsx`

### P1-2 Meal actions

Primary: **Приготовить · Рецепт · Заменить**  
Secondary: **Удалить** as text confirm link.

Removed: **В покупки** from card actions.

### P1-3 Profile compact

Smaller avatar, tighter padding, reduced row height.

**File:** `AccountHub2026.tsx`

### P1-4 Wellness first screen

First viewport: status ring + calories, water (compact), insight. Goals/week in collapsible section.

**Files:** `WellnessHome2026.tsx`, `WellnessDayRing2026.tsx`

---

## Changed components (summary)

| Area | Components / modules |
|------|---------------------|
| Home | `PlanAmHero2026`, `planam-hero-2026` |
| Plan | `PlanToday2026`, `PlanMealCard2026` |
| Shopping | `categories-v1`, `category-suggest`, `labels`, `shopping-groups` |
| Wellness | `WellnessHome2026`, `WellnessDayRing2026` |
| Account | `AccountHub2026` |
| Core | `api-client`, `globals.css`, `tailwind.config` |

---

## New colors (light)

| Role | Value |
|------|-------|
| Canvas | `#FFFFFF` |
| Brand | `#2F9E44` |
| Text | `#1A1F1C` |
| Muted | `#5C665C` |
| Border | `#E2E8E0` |
| Elevated | `#F6FAF6` |

See `docs/PLANAM_COLOR_SYSTEM_V1.md`.

---

## Category fixes (examples)

| Item | Before | After |
|------|--------|-------|
| Яйцо | Другое / Продукты | Яйца |
| Малина | mixed | Фрукты и ягоды |
| Бульон | mixed | Бакалея |
| Пшено | mixed | Крупы и макароны |
| Перец болгарский | Специи | Овощи и зелень |

---

## QA

| Check | Result |
|-------|--------|
| `npm run lint` (web) | ✅ |
| `npm run build` (web) | ✅ |
| Hero priority tests | ✅ `planam-hero-2026.test.ts` |
| Category classifier tests | ✅ `category-suggest.test.ts` |
| Viewports 320–412px | Manual: compact hero `min-h-[200px]`, bottom nav safe area |
| Light / dark theme | Tokens updated for both |
| Telegram WebView | No new `response.json()` on empty body |

### Screens audited

- `/` — V1 hero + status rows
- `/plan/today` — V1 meal cards
- `/shopping` — V1 categories grouping
- `/wellness` — compact first screen
- `/account` — compact hub

---

## Before / after (descriptions)

**Hero before:** Large ❤️ icon, wellness title over existing lunch menu.  
**Hero after:** Full-width dish photo, «Обед · Суп · 20 мин · 400 ккал», green CTA «Приготовить».

**Shopping before:** «Продукты» bucket with eggs, berries, broth mixed.  
**Shopping after:** 15 canonical categories, sorted, eggs in «Яйца».

**Palette before:** Cream `#FBF7EF`, muted sage `#5E8B57`.  
**Palette after:** White canvas, brand green `#2F9E44`, darker text `#1A1F1C`.

---

## Git

```
feat(v1): sprint 1.5 polish and stabilization
```
