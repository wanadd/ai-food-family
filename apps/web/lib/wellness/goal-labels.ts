import { NUTRITION_GOAL_LABELS } from "@/lib/nutrition-profile/options";

/** User-facing goal labels for Wellness 2026 (ПланАм tone). */
const WELLNESS_GOAL_LABELS: Record<string, string> = {
  lose: "Похудение",
  gain: "Набор массы",
  maintain: "Поддержание веса",
  healthy: "ЗОЖ",
  sport: "Спорт и нагрузка",
  kids: "Здоровье семьи",
  child: "Здоровье семьи",
};

export function wellnessGoalLabel(
  goalType: string | null | undefined,
  fallbackLabel?: string | null,
): string {
  if (!goalType) {
    return fallbackLabel?.trim() || "Цель не задана";
  }
  return (
    WELLNESS_GOAL_LABELS[goalType] ??
    NUTRITION_GOAL_LABELS[goalType] ??
    fallbackLabel?.trim() ??
    "Цель не задана"
  );
}
