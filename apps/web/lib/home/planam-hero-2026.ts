import type { MenuOverview } from "@/lib/menu/overview-types";

import type { Home2026TodayMeal } from "./home-2026-data";
import { formatMealMeta } from "./home-2026-data";

export type PlanAmHeroVariant = "no_menu" | "shopping" | "wellness" | "meal";

export type PlanAmHeroState = {
  variant: PlanAmHeroVariant;
  ctaLabel: string;
  ctaHref: string;
  title: string;
  subtitle: string;
  meal: Home2026TodayMeal | null;
  shoppingCount: number;
};

const MEAL_CYCLE = ["breakfast", "lunch", "dinner", "snack"] as const;

/** Time-of-day meal priority (Final Vision Sprint 1). */
export function mealTypesForHour(hour: number): string[] {
  if (hour >= 5 && hour < 12) {
    return ["breakfast", "lunch", "dinner", "snack"];
  }
  if (hour >= 12 && hour < 17) {
    return ["lunch", "dinner", "breakfast", "snack"];
  }
  if (hour >= 17 && hour < 24) {
    return ["dinner", "snack", "breakfast", "lunch"];
  }
  return [...MEAL_CYCLE];
}

export function pickNextMealByTime(
  meals: Home2026TodayMeal[],
  now: Date = new Date(),
): Home2026TodayMeal | null {
  if (!meals.length) {
    return null;
  }
  const order = mealTypesForHour(now.getHours());
  for (const type of order) {
    const found = meals.find((m) => m.meal_type === type);
    if (found) {
      return found;
    }
  }
  return meals[0] ?? null;
}

export function greetingForPlanAm(date: Date = new Date()): string {
  const h = date.getHours();
  if (h >= 5 && h < 12) {
    return "Доброе утро";
  }
  if (h >= 12 && h < 17) {
    return "Добрый день";
  }
  if (h >= 17 && h < 24) {
    return "Добрый вечер";
  }
  return "Здравствуйте";
}

export function formatPlanAmGreeting(
  displayName: string | null | undefined,
  date: Date = new Date(),
): string {
  const base = greetingForPlanAm(date);
  if (displayName?.trim()) {
    return `${base}, ${displayName.trim()} 👋`;
  }
  return `${base} 👋`;
}

export function isShoppingHeroPriority(
  uncheckedCount: number,
  now: Date = new Date(),
): boolean {
  const hour = now.getHours();
  if (uncheckedCount >= 8) {
    return true;
  }
  return hour >= 17 && hour < 19 && uncheckedCount >= 3;
}

export function isWellnessHeroPriority(
  overview: MenuOverview,
): boolean {
  const { level, body, freshness_status } = overview.nutritionist_advice;
  if (freshness_status === "no_menu") {
    return false;
  }
  if (level === "update_recommended") {
    return true;
  }
  if (level === "suggest_update" && body?.trim()) {
    return true;
  }
  return false;
}

export function resolvePlanAmHeroState(
  overview: MenuOverview | null,
  meals: Home2026TodayMeal[],
  hasMenu: boolean,
  now: Date = new Date(),
): PlanAmHeroState {
  const unchecked = overview?.shopping_unchecked_count ?? 0;

  // Priority 1: next meal (food first — never let wellness/shopping override)
  const meal = hasMenu ? pickNextMealByTime(meals, now) : null;
  if (meal) {
    return {
      variant: "meal",
      ctaLabel: "Приготовить",
      ctaHref: `/plan/today?meal=${meal.meal_type}`,
      title: meal.name,
      subtitle: formatMealMeta(meal),
      meal,
      shoppingCount: unchecked,
    };
  }

  // Priority 2: no menu
  if (!hasMenu) {
    return {
      variant: "no_menu",
      ctaLabel: "Создать меню",
      ctaHref: "/plan/generate",
      title: "Составим меню?",
      subtitle: "План на неделю за пару минут — с фото блюд и списком покупок",
      meal: null,
      shoppingCount: unchecked,
    };
  }

  // Priority 3: shopping
  if (isShoppingHeroPriority(unchecked, now)) {
    return {
      variant: "shopping",
      ctaLabel: "Открыть список",
      ctaHref: "/shopping",
      title: `Нужно купить ${unchecked} ${goodsLabel(unchecked)}`,
      subtitle: "Еда и быт — один список для семьи",
      meal: null,
      shoppingCount: unchecked,
    };
  }

  // Priority 4: wellness
  if (overview && isWellnessHeroPriority(overview)) {
    const advice = overview.nutritionist_advice;
    const title = advice.title?.trim() || "Есть рекомендации по здоровью";
    const subtitle =
      advice.body?.trim() || "Откройте раздел «Здоровье» для подробностей";
    return {
      variant: "wellness",
      ctaLabel: "Подробнее",
      ctaHref: "/wellness",
      title,
      subtitle,
      meal: null,
      shoppingCount: unchecked,
    };
  }

  return {
    variant: "no_menu",
    ctaLabel: "Создать меню",
    ctaHref: "/plan/generate",
    title: "Составим меню?",
    subtitle: "Добавьте блюда на сегодня",
    meal: null,
    shoppingCount: unchecked,
  };
}

function goodsLabel(count: number): string {
  const mod10 = count % 10;
  const mod100 = count % 100;
  if (mod10 === 1 && mod100 !== 11) {
    return "товар";
  }
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 10 || mod100 >= 20)) {
    return "товара";
  }
  return "товаров";
}

export function wellnessStatusLabel(overview: MenuOverview | null): string {
  if (!overview) {
    return "—";
  }
  if (isWellnessHeroPriority(overview)) {
    return "Есть рекомендации";
  }
  const level = overview.nutritionist_advice.level;
  if (level === "ok") {
    return "В норме";
  }
  if (level === "suggest_update") {
    return "Есть рекомендации";
  }
  return "В норме";
}

export function leftoversStatusLabel(overview: MenuOverview | null): string {
  const count = overview?.meal_leftovers_count ?? 0;
  if (count <= 0) {
    return "Пока пусто";
  }
  return `${count} ${productsLabel(count)}`;
}

/** Pantry stock label for the home "Остатки" block (real pantry_items_count). */
export function pantryStatusLabel(overview: MenuOverview | null): string {
  if (!overview || overview.pantry_items_count == null) {
    return "Пока пусто";
  }
  const count = overview.pantry_items_count;
  if (count <= 0) {
    return "Пока пусто";
  }
  return `${count} ${productsLabel(count)}`;
}

function productsLabel(count: number): string {
  const mod10 = count % 10;
  const mod100 = count % 100;
  if (mod10 === 1 && mod100 !== 11) {
    return "продукт";
  }
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 10 || mod100 >= 20)) {
    return "продукта";
  }
  return "продуктов";
}

export function shoppingStatusLabel(unchecked: number): string {
  if (unchecked <= 0) {
    return "Всё куплено";
  }
  return `${unchecked} ${goodsLabel(unchecked)}`;
}
