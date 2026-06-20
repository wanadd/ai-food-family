# Visual QA P0/P1 Hotfix Report

Дата: 2026-06-08  
Ветка: `fix/visual-qa-p0-p1-hotfix`  
Основа: `reports/full_visual_qa_ux_walkthrough_2026.md`

---

## 1. Закрытые проблемы из walkthrough audit

| Проблема аудита | Статус |
|-----------------|--------|
| `1 л л` / дубль unit в Pantry | ✅ Закрыто |
| Дубль unit в Shopping caption | ✅ Закрыто |
| Home «простыня» | ✅ Уплотнено |
| Дубль leftovers на Home | ✅ Убран |
| Путаница «Остатки» vs pantry/leftovers | ✅ Copy на Home |
| `pb-28` + shell offset на Plan Today | ✅ Закрыто |
| `pb-28` + shell offset на Recipe detail | ✅ Закрыто |
| Белая hero CTA `bg-white` | ✅ Закрыто |
| Hero gradient «съедает» фото | ✅ Смягчено |
| `/home/leftovers` generic title | ✅ Закрыто |

**Не в scope hotfix (осталось P1/P2):**

- Nutrition/Notifications legacy UI
- Shopping nested `max-h-[70vh]` scroll
- Upstream data: капуста с единицей «л»
- Plan week thumbnails
- Admin dark theme

---

## 2. Изменённые файлы

**Новые:**

- `apps/web/lib/planam/formatProductQuantity.ts`
- `apps/web/lib/planam/formatProductQuantity.test.ts`

**Изменённые:**

- `apps/web/components/dom-2026/Pantry2026.tsx`
- `apps/web/components/dom-2026/Shopping2026.tsx`
- `apps/web/components/home-2026/Home2026.tsx`
- `apps/web/components/home-2026/PlanAmHero2026.tsx`
- `apps/web/components/home-2026/TodayDishRail2026.tsx`
- `apps/web/components/home-2026/PlanAmStatusRows2026.tsx`
- `apps/web/components/plan-2026/PlanToday2026.tsx`
- `apps/web/components/recipes-2026/RecipeDetail2026.tsx`
- `apps/web/lib/navigation/nav-config-2026.ts`
- `apps/web/lib/planam/routes.ts` (comment only)

---

## 3. Unit display

Добавлен `formatProductQuantity()`:

- Prefer `amount` если уже formatted
- Не добавляет `unit`, если он уже в `quantity` (`1 л` + `л` → `1 л`)
- Скрывает `null`, `undefined`, `NaN`
- TODO в коде: upstream cleanup для твёрдых продуктов с объёмными единицами

Применено в `Pantry2026` и `Shopping2026`. `RecipeDetail` не менялся (`formatIngredientAmount`).

---

## 4. Home уплотнение

**Порядок блоков:**

1. Greeting  
2. Hero (compact 200px / 180px)  
3. TodayDishRail (compact)  
4. Status rows («Запасы»)  
5. Один row «Из того, что есть дома»  
6. Quick actions 3×1: Покупки / Запасы / Меню  
7. Компактный AI helper  

**Убрано:** дубль quick action «Готовить из остатков», 2×2 grid, длинный AI card copy.

**TodayDishRail:** image `h-20`, compact button, меньше padding.

---

## 5. Bottom inset

- `PlanToday2026`: `pb-28` → `pb-4`
- `RecipeDetail2026`: `pb-28` → `pb-4`

Shell `BOTTOM_NAV_OFFSET_2026` сохранён.

---

## 6. Hero CTA / overlay

- Primary CTA: `Button2026 variant="primary"` без `bg-white`
- Secondary на фото: полупрозрачный dark glass
- Gradient: `from-black/75` → `from-black/50`, readable zone `from-black/55` только внизу
- Hero height: 240/200 → 200/180

---

## 7. `/home/leftovers` title

`ROUTES_2026`:

```text
title: "Из того, что есть дома"
```

---

## 8. Build

```text
cd apps/web && npm run build → exit 0
```

Предупреждения `@next/next/no-img-element` — pre-existing.

---

## 9. Backend / API / БД

**Не менялись.**

---

## 10. Остаётся в P1/P2

- NutritionProfileForm + Notifications → 2026 tokens
- Shopping nested scroll
- Plan week real thumbnails
- Meal card `bg-white/90` status pill
- Data cleanup: volume units on solid produce
- Admin UI polish
