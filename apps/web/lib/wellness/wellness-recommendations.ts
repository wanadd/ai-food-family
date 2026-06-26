import type { MenuOverview } from "@/lib/menu/overview-types";
import type { ProgressOverview } from "@/lib/progress/types";

export type WellnessRecommendationCategory =
  | "plan"
  | "protein"
  | "light_dinner"
  | "snack"
  | "lower_calories"
  | "from_pantry";

const CATEGORY_LABELS: Record<WellnessRecommendationCategory, string> = {
  plan: "По вашему плану",
  protein: "Добрать белок",
  light_dinner: "Лёгкий ужин",
  snack: "Быстрый перекус",
  lower_calories: "Меньше калорий",
  from_pantry: "Из запасов",
};

export type WellnessRecommendation = {
  id: string;
  title: string;
  category: WellnessRecommendationCategory;
  categoryLabel: string;
  recipeId: number | null;
};

function inferCategory(
  mealType: string,
  progress: ProgressOverview | null,
): WellnessRecommendationCategory {
  const targets = progress?.targets;
  const actual = progress?.daily_actual;
  const proteinTarget = targets?.protein_target_g ?? 0;
  const proteinEaten = actual?.protein_consumed_g ?? 0;
  const calTarget = targets?.calories_target ?? 0;
  const calEaten = actual?.calories_consumed ?? 0;

  if (mealType === "snack") {
    return "snack";
  }
  if (
    proteinTarget > 0 &&
    actual?.meals_logged &&
    proteinEaten / proteinTarget < 0.6 &&
    (mealType === "lunch" || mealType === "dinner")
  ) {
    return "protein";
  }
  if (
    calTarget > 0 &&
    actual?.meals_logged &&
    calEaten / calTarget > 0.85 &&
    mealType === "dinner"
  ) {
    return "light_dinner";
  }
  if (
    calTarget > 0 &&
    actual?.meals_logged &&
    calEaten / calTarget > 0.9
  ) {
    return "lower_calories";
  }
  return "plan";
}

export function buildWellnessRecommendations(input: {
  overview: MenuOverview | null;
  progress: ProgressOverview | null;
  maxItems?: number;
}): WellnessRecommendation[] {
  const { overview, progress, maxItems = 4 } = input;
  const meals = (overview?.today_meals ?? []).filter(
    (m) => m.name?.trim() && m.recipe_id != null,
  );

  return meals.slice(0, maxItems).map((meal) => {
    const category = inferCategory(meal.meal_type, progress);
    return {
      id: `${meal.meal_type}-${meal.recipe_id}`,
      title: meal.name!.trim(),
      category,
      categoryLabel: CATEGORY_LABELS[category],
      recipeId: meal.recipe_id ?? null,
    };
  });
}

export function wellnessRecommendationsEmptyMessage(
  hasMenu: boolean,
): string {
  if (!hasMenu) {
    return "Варианты появятся после генерации меню";
  }
  return "Варианты замены появятся после генерации альтернатив";
}
