import type { MenuOverview } from "@/lib/menu/overview-types";
import { PLANAM_ROUTES, recipeDetailPath } from "@/lib/planam/routes";

import type { Home2026TodayMeal } from "./home-2026-data";
import { formatMealMeta } from "./home-2026-data";

export type PlanAmHeroPriority = "P0" | "P1" | "P2" | "P3" | "P4" | "fallback";

export type PlanAmHeroVariant =
  | "nutrition_profile"
  | "meal"
  | "no_menu"
  | "pantry_expiry"
  | "meal_outcome"
  | "shopping"
  | "wellness"
  | "welcome";

export type PlanAmHeroState = {
  variant: PlanAmHeroVariant;
  priority: PlanAmHeroPriority;
  ctaLabel: string;
  ctaHref: string;
  secondaryCtaLabel?: string;
  secondaryCtaHref?: string;
  title: string;
  subtitle: string;
  meal: Home2026TodayMeal | null;
  shoppingCount: number;
};

const MEAL_CYCLE = ["breakfast", "lunch", "dinner", "snack"] as const;

/** Days until expiry to surface P3 pantry hero. */
const PANTRY_EXPIRY_HERO_DAYS = 3;

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

const QUOTE_PAIRS: Array<[string, string]> = [
  ["«", "»"],
  ['"', '"'],
  ["“", "”"],
  ["'", "'"],
  ["`", "`"],
];

/** Убирает обрамляющие кавычки из названия блюда: «Каша» → Каша. */
export function cleanMealTitle(name: string | null | undefined): string {
  let text = (name ?? "").trim();
  let changed = true;
  while (changed && text.length > 2) {
    changed = false;
    for (const [open, close] of QUOTE_PAIRS) {
      if (text.startsWith(open) && text.endsWith(close)) {
        text = text.slice(open.length, text.length - close.length).trim();
        changed = true;
      }
    }
  }
  return text;
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

export function isWellnessHeroPriority(overview: MenuOverview): boolean {
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

function isNutritionProfileIncomplete(overview: MenuOverview | null): boolean {
  return overview?.next_action?.id === "complete_nutrition";
}

function isPantryExpiryHero(overview: MenuOverview | null): boolean {
  const preview = overview?.pantry_expiring_preview;
  if (preview && preview.days_until_expiry <= PANTRY_EXPIRY_HERO_DAYS) {
    return true;
  }
  return overview?.next_action?.id === "use_pantry_item";
}

function isMealOutcomeHero(overview: MenuOverview | null): boolean {
  return overview?.next_action?.id === "meal_outcome";
}

function mealHeroHref(meal: Home2026TodayMeal): string {
  if (meal.recipe_id != null) {
    return recipeDetailPath(meal.recipe_id);
  }
  return `${PLANAM_ROUTES.planToday}?meal=${encodeURIComponent(meal.meal_type)}`;
}

function mealReplaceHref(meal: Home2026TodayMeal): string {
  return `${PLANAM_ROUTES.planToday}?meal=${encodeURIComponent(meal.meal_type)}&replace=1`;
}

/**
 * Hero priority: P0 profile → P1 meal → P2 no menu → P3 pantry → P4 outcome → fallback.
 * Uses only fields already present in MenuOverview / Home data.
 */
export function resolvePlanAmHeroState(
  overview: MenuOverview | null,
  meals: Home2026TodayMeal[],
  hasMenu: boolean,
  now: Date = new Date(),
): PlanAmHeroState {
  const unchecked = overview?.shopping_unchecked_count ?? 0;
  const base = { shoppingCount: unchecked, meal: null as Home2026TodayMeal | null };

  // P0 — incomplete nutrition profile
  if (isNutritionProfileIncomplete(overview)) {
    return {
      ...base,
      variant: "nutrition_profile",
      priority: "P0",
      ctaLabel: "Заполнить профиль",
      ctaHref: PLANAM_ROUTES.accountNutrition,
      title: "Давайте настроим питание под вас",
      subtitle:
        "Пара минут — и PLANAM будет учитывать цели, аллергии и предпочтения семьи.",
    };
  }

  // P1 — current meal
  const meal = hasMenu ? pickNextMealByTime(meals, now) : null;
  if (meal) {
    return {
      ...base,
      variant: "meal",
      priority: "P1",
      meal,
      ctaLabel: "Готовить",
      ctaHref: mealHeroHref(meal),
      secondaryCtaLabel: "Заменить",
      secondaryCtaHref: mealReplaceHref(meal),
      title: cleanMealTitle(meal.name),
      subtitle: formatMealMeta(meal),
    };
  }

  // P2 — no menu
  if (!hasMenu) {
    return {
      ...base,
      variant: "no_menu",
      priority: "P2",
      ctaLabel: "Собрать меню",
      ctaHref: PLANAM_ROUTES.planGenerate,
      title: "Соберём меню на неделю?",
      subtitle: "PLANAM предложит варианты и сразу подготовит список покупок.",
    };
  }

  // P3 — pantry expiry
  if (isPantryExpiryHero(overview)) {
    const preview = overview?.pantry_expiring_preview;
    const subtitle = preview
      ? `${preview.name} — осталось ${preview.days_until_expiry} дн. Подберём рецепт из запасов.`
      : "В остатках есть продукты, которые скоро испортятся. Подберём рецепт из них.";
    return {
      ...base,
      variant: "pantry_expiry",
      priority: "P3",
      ctaLabel: "Подобрать рецепт",
      ctaHref: PLANAM_ROUTES.homeLeftovers,
      title: "Лучше использовать сегодня",
      subtitle,
    };
  }

  // P4 — after cooking / meal outcome
  if (isMealOutcomeHero(overview)) {
    return {
      ...base,
      variant: "meal_outcome",
      priority: "P4",
      ctaLabel: "Открыть покупки",
      ctaHref: PLANAM_ROUTES.shopping,
      title: "Готово, меню обновлено",
      subtitle: "Можно отметить блюдо приготовленным или перейти к покупкам.",
    };
  }

  // Fallback — shopping / wellness / welcome (no new backend fields)
  if (isShoppingHeroPriority(unchecked, now)) {
    return {
      ...base,
      variant: "shopping",
      priority: "fallback",
      ctaLabel: "Открыть список",
      ctaHref: PLANAM_ROUTES.shopping,
      title: `Нужно купить ${unchecked} ${goodsLabel(unchecked)}`,
      subtitle: "Еда и быт — один список для семьи",
    };
  }

  if (overview && isWellnessHeroPriority(overview)) {
    const advice = overview.nutritionist_advice;
    const title = advice.title?.trim() || "Есть рекомендации по здоровью";
    const subtitle =
      advice.body?.trim() || "Откройте раздел «Здоровье» для подробностей";
    return {
      ...base,
      variant: "wellness",
      priority: "fallback",
      ctaLabel: "Подробнее",
      ctaHref: PLANAM_ROUTES.wellness,
      title,
      subtitle,
    };
  }

  return {
    ...base,
    variant: "welcome",
    priority: "fallback",
    ctaLabel: "Открыть меню",
    ctaHref: PLANAM_ROUTES.planToday,
    title: "Ваш день в PLANAM",
    subtitle: "Посмотрите план на сегодня или соберите новое меню.",
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

/** Home status chip for today's menu completeness. */
export function menuStatusLabel(overview: MenuOverview | null): string {
  if (!overview?.plan_summary.has_selected_menu) {
    return "Собрать";
  }
  const slots = overview.today_meals;
  if (!slots.length) {
    return "Собрать";
  }
  const filled = slots.filter((m) => m.name?.trim()).length;
  if (filled === 0) {
    return "Собрать";
  }
  const pct = Math.round((filled / slots.length) * 100);
  return `${pct}%`;
}

export function formatPlanAmDate(date: Date = new Date()): string {
  return date.toLocaleDateString("ru-RU", {
    weekday: "long",
    day: "numeric",
    month: "long",
  });
}
