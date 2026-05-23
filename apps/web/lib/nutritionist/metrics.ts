import type { NutritionProfileData } from "@/lib/nutrition-profile/types";
import type { MenuVariant } from "@/lib/menu/types";
import type { ShoppingList } from "@/lib/shopping/types";

import { getNutritionProfileProgress } from "@/lib/profile/nutrition-summary";

export type StatCard = {
  id: string;
  label: string;
  value: string;
  hint: string;
  ready: boolean;
};

function estimateDailyCalories(
  profile: NutritionProfileData | null,
  menu: MenuVariant | null,
): string | null {
  if (menu?.meals?.length) {
    const fromMeals = menu.meals.reduce(
      (sum, meal) => sum + (meal.calories_estimate ?? 0),
      0,
    );
    if (fromMeals > 0) {
      return `~${fromMeals}`;
    }
  }
  if (!profile?.weight_kg || !profile.age) {
    return null;
  }
  const weight = profile.weight_kg;
  let base = weight * 24;
  if (profile.nutrition_goal === "lose") base *= 0.88;
  if (profile.nutrition_goal === "gain") base *= 1.12;
  if (profile.nutrition_goal === "sport") base *= 1.15;
  if (profile.activity_level === "high" || profile.activity_level === "training") {
    base *= 1.1;
  }
  return `~${Math.round(base)}`;
}

function estimateProtein(profile: NutritionProfileData | null): string | null {
  if (!profile?.weight_kg) {
    return null;
  }
  let gramsPerKg = 1.0;
  if (profile.nutrition_goal === "sport") gramsPerKg = 1.6;
  if (profile.nutrition_goal === "gain") gramsPerKg = 1.4;
  if (profile.nutrition_goal === "lose") gramsPerKg = 1.2;
  return `~${Math.round(profile.weight_kg * gramsPerKg)} г`;
}

function formatWater(profile: NutritionProfileData | null): string | null {
  const liters = profile?.pro?.water_liters;
  if (liters && liters > 0) {
    return `${liters} л`;
  }
  if (profile?.weight_kg) {
    return `~${(profile.weight_kg * 0.033).toFixed(1)} л`;
  }
  return null;
}

function planDoneLabel(shopping: ShoppingList | null): {
  value: string;
  hint: string;
  ready: boolean;
} {
  if (!shopping?.items?.length) {
    return {
      value: "—",
      hint: "Составьте меню и покупки",
      ready: false,
    };
  }
  const total = shopping.total_count || shopping.items.length;
  const checked = shopping.checked_count;
  if (total === 0) {
    return { value: "—", hint: "Список пуст", ready: false };
  }
  const pct = Math.round((checked / total) * 100);
  return {
    value: `${pct}%`,
    hint: checked === total ? "Всё куплено" : `Осталось ${total - checked}`,
    ready: true,
  };
}

export function buildStatCards(
  profile: NutritionProfileData | null,
  menu: MenuVariant | null,
  shopping: ShoppingList | null,
): StatCard[] {
  const calories = estimateDailyCalories(profile, menu);
  const protein = estimateProtein(profile);
  const water = formatWater(profile);
  const plan = planDoneLabel(shopping);

  return [
    {
      id: "calories",
      label: "Калории",
      value: calories ?? "—",
      hint: calories ? "ориентир на день" : "заполните вес в профиле",
      ready: Boolean(calories),
    },
    {
      id: "protein",
      label: "Белки",
      value: protein ?? "—",
      hint: protein ? "в день" : "укажите вес в профиле",
      ready: Boolean(protein),
    },
    {
      id: "water",
      label: "Вода",
      value: water ?? "—",
      hint: water ? "в день" : "можно задать в PRO",
      ready: Boolean(water),
    },
    {
      id: "plan",
      label: "План выполнен",
      value: plan.value,
      hint: plan.hint,
      ready: plan.ready,
    },
  ];
}

export function getOverallProgress(
  profile: NutritionProfileData | null,
  hasMenu: boolean,
  shopping: ShoppingList | null,
): number | null {
  if (!profile?.nutrition_goal) {
    return null;
  }
  let score = getNutritionProfileProgress(profile) * 0.45;
  if (hasMenu) {
    score += 35;
  }
  if (shopping?.items?.length) {
    const total = shopping.total_count || shopping.items.length;
    const checked = shopping.checked_count;
    if (total > 0) {
      score += (checked / total) * 20;
    }
  }
  return Math.min(100, Math.round(score));
}
