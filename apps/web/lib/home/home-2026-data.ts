import { stripAuditSuffix } from "@/lib/display/sanitize-label";
import type { MenuOverview, HomeNextAction } from "@/lib/menu/overview-types";
import type { MenuMeal } from "@/lib/menu/types";
import { defaultDayIndex, mealsForDayIndex } from "@/lib/menu/menu-days";

export type Home2026TodayMeal = {
  meal_type: string;
  label: string;
  name: string;
  recipe_id: number | null;
  image_url: string | null;
  prep_time_minutes: number | null;
  calories: number | null;
};

export type PlanSnapshotItem = {
  id: string;
  emoji: string;
  label: string;
};

const MEAL_ORDER = ["dinner", "lunch", "breakfast", "snack"];

function mealsFromSelectedMenu(
  overview: MenuOverview,
): Map<string, MenuMeal> {
  const map = new Map<string, MenuMeal>();
  const menu = overview.selected_menu?.menu;
  if (!menu) {
    return map;
  }
  const dayIndex = defaultDayIndex(menu);
  for (const meal of mealsForDayIndex(menu, dayIndex)) {
    map.set(meal.meal_type, meal);
  }
  return map;
}

export function enrichTodayMeals(overview: MenuOverview): Home2026TodayMeal[] {
  const byType = mealsFromSelectedMenu(overview);
  return overview.today_meals
    .filter((m): m is typeof m & { name: string } => Boolean(m.name?.trim()))
    .map((m) => {
      const detail = byType.get(m.meal_type);
      return {
        meal_type: m.meal_type,
        label: m.label,
        name: stripAuditSuffix(m.name!.trim()),
        recipe_id: m.recipe_id ?? null,
        image_url: m.image_url ?? null,
        prep_time_minutes: detail?.prep_time_minutes ?? null,
        calories: detail?.calories_estimate ?? null,
      };
    });
}

export function pickHeroMeal(meals: Home2026TodayMeal[]): Home2026TodayMeal | null {
  if (!meals.length) {
    return null;
  }
  for (const type of MEAL_ORDER) {
    const found = meals.find((m) => m.meal_type === type);
    if (found) {
      return found;
    }
  }
  return meals[0];
}

export function buildPlanSnapshot(overview: MenuOverview): PlanSnapshotItem[] {
  const items: PlanSnapshotItem[] = [];
  const unchecked = overview.shopping_unchecked_count ?? 0;

  if (unchecked > 0) {
    items.push({
      id: "shopping",
      emoji: "🛒",
      label: `Купить: ${unchecked}`,
    });
  }

  const pantry = overview.pantry_expiring_preview;
  if (pantry) {
    items.push({
      id: "pantry",
      emoji: "📦",
      label: `${pantry.name}: ${pantry.days_until_expiry} дн.`,
    });
  }

  const leftovers = overview.meal_leftovers_count ?? 0;
  if (leftovers > 0) {
    items.push({
      id: "leftovers",
      emoji: "🍲",
      label: `Остатки: ${leftovers}`,
    });
  }

  if (overview.is_pro && overview.pro_coverage) {
    const { protein_percent, fiber_percent, calories_percent, water_percent } =
      overview.pro_coverage;
    const avg = Math.round(
      (protein_percent + fiber_percent + calories_percent + water_percent) / 4,
    );
    if (avg > 0) {
      items.push({
        id: "plan",
        emoji: "❤️",
        label: `План: ${avg}%`,
      });
    }
  } else if (overview.plan_summary.has_selected_menu) {
    const count = overview.today_meals.filter((m) => m.name).length;
    if (count > 0) {
      items.push({
        id: "meals",
        emoji: "🍽",
        label: `Блюд сегодня: ${count}`,
      });
    }
  }

  return items.slice(0, 3);
}

export function buildAiInsight(overview: MenuOverview): string | null {
  if (overview.nutritionist_advice_error) {
    return null;
  }
  const { title, body, level } = overview.nutritionist_advice;
  if (level === "ok" && !body?.trim()) {
    return null;
  }
  const text = body?.trim() || title?.trim();
  if (!text) {
    return null;
  }
  return text;
}

export function shouldShowShoppingAction(action: HomeNextAction | null | undefined): boolean {
  if (!action || action.id !== "shopping") {
    return true;
  }
  const count = Number(action.metadata?.unchecked_count ?? 0);
  return count > 0;
}

export function formatMealMeta(meal: Home2026TodayMeal): string {
  const parts: string[] = [meal.label];
  if (meal.prep_time_minutes != null && meal.prep_time_minutes > 0) {
    parts.push(`${meal.prep_time_minutes} мин`);
  }
  if (meal.calories != null && meal.calories > 0) {
    parts.push(`${Math.round(meal.calories)} ккал`);
  }
  return parts.join(" · ");
}

export function greetingFor(date: Date): string {
  const h = date.getHours();
  if (h < 6) return "Доброй ночи";
  if (h < 12) return "Доброе утро";
  if (h < 18) return "Добрый день";
  return "Добрый вечер";
}

export function formatHomeDate(date: Date): string {
  return date.toLocaleDateString("ru-RU", {
    weekday: "long",
    day: "numeric",
    month: "long",
  });
}
