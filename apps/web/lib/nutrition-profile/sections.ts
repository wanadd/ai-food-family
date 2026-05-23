import type { NutritionProfileData } from "@/lib/nutrition-profile/types";

export const NUTRITION_SECTION_IDS = [
  "basics",
  "goal_activity",
  "allergies_restrictions",
  "favorites",
  "dislikes",
  "cooking",
  "pro",
] as const;

export type NutritionSectionId = (typeof NUTRITION_SECTION_IDS)[number];

export const NUTRITION_SECTION_LABELS: Record<NutritionSectionId, string> = {
  basics: "Основные данные",
  goal_activity: "Цель и активность",
  allergies_restrictions: "Аллергии и ограничения",
  favorites: "Любимые продукты",
  dislikes: "Нелюбимые продукты",
  cooking: "Настройки готовки",
  pro: "PRO",
};

/** Eight checklist items for progress (product spec). */
export function getNutritionSectionChecks(data: NutritionProfileData) {
  const hasBasics = Boolean(data.age && data.gender);
  const hasGoal = Boolean(data.nutrition_goal);
  const hasActivity = Boolean(data.activity_level);
  const hasAllergies =
    data.allergies.length > 0 ||
    data.allergies.includes("none");
  const hasRestrictions =
    data.diets.some((d) => d && d !== "none") ||
    Boolean(data.medical_restrictions.trim()) ||
    Boolean(data.banned_foods.trim());
  const hasFavorites = Boolean(data.favorite_foods.trim());
  const hasDislikes = Boolean(data.disliked_foods.trim());
  const hasCooking = Boolean(data.budget && data.cooking_time);

  const items = [
    { key: "goal", label: "Цель", done: hasGoal },
    { key: "activity", label: "Активность", done: hasActivity },
    { key: "allergies", label: "Аллергии", done: hasAllergies },
    { key: "restrictions", label: "Ограничения", done: hasRestrictions },
    { key: "favorites", label: "Любит", done: hasFavorites },
    { key: "dislikes", label: "Не любит", done: hasDislikes },
    { key: "cooking", label: "Готовка", done: hasCooking },
    { key: "basics", label: "Основные данные", done: hasBasics },
  ] as const;

  const filled = items.filter((i) => i.done).length;
  const total = items.length;
  const percent = Math.round((filled / total) * 100);

  return { items, filled, total, percent };
}

export function isNutritionCardComplete(
  id: NutritionSectionId,
  data: NutritionProfileData,
): boolean {
  switch (id) {
    case "basics":
      return Boolean(data.age && data.gender);
    case "goal_activity":
      return Boolean(data.nutrition_goal && data.activity_level);
    case "allergies_restrictions":
      return (
        data.allergies.length > 0 ||
        data.diets.some((d) => d && d !== "none") ||
        Boolean(data.medical_restrictions.trim()) ||
        Boolean(data.banned_foods.trim())
      );
    case "favorites":
      return Boolean(data.favorite_foods.trim());
    case "dislikes":
      return Boolean(data.disliked_foods.trim());
    case "cooking":
      return Boolean(data.budget && data.cooking_time);
    case "pro":
      return (
        data.pro.workouts_enabled ||
        data.pro.track_macros ||
        Boolean(data.pro.body_measurements.trim())
      );
    default:
      return false;
  }
}
