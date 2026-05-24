import type { NutritionProfileData } from "@/lib/nutrition-profile/types";
import type { ProgressOverview } from "@/lib/progress/types";

export type GoalProgressCard = {
  startWeight: string;
  currentWeight: string;
  targetWeight: string;
  remaining: string | null;
  percent: number | null;
  paceLine: string | null;
  forecastLine: string | null;
};

export function buildGoalProgressCard(
  profile: NutritionProfileData | null,
  progress: ProgressOverview | null,
): GoalProgressCard {
  const gd = profile?.goal_details;
  const current = progress?.current_weight_kg ?? gd?.current_weight_kg ?? profile?.weight_kg;
  const target = gd?.target_weight_kg;

  let remaining: string | null = null;
  if (current != null && target != null) {
    const diff = Number(current) - Number(target);
    remaining =
      progress?.goal_type === "lose"
        ? `${Math.max(0, diff).toFixed(1)} кг`
        : `${Math.abs(diff).toFixed(1)} кг`;
  }

  let paceLine: string | null = null;
  if (gd?.goal_pace) {
    const paceLabels: Record<string, string> = {
      soft: "мягкий",
      standard: "стандартный",
      intensive: "интенсивный",
    };
    paceLine = `Темп: ${paceLabels[gd.goal_pace] ?? gd.goal_pace}`;
  } else if (progress?.weight_change_week_kg != null) {
    paceLine = `За неделю: ${progress.weight_change_week_kg > 0 ? "+" : ""}${progress.weight_change_week_kg.toFixed(1)} кг`;
  }

  let forecastLine: string | null = null;
  if (gd?.target_date) {
    forecastLine = `Цель к ${gd.target_date}`;
  }

  return {
    startWeight:
      gd?.current_weight_kg != null
        ? `${gd.current_weight_kg} кг`
        : current != null
          ? `${current} кг`
          : "—",
    currentWeight: current != null ? `${current} кг` : "—",
    targetWeight: target != null ? `${target} кг` : "—",
    remaining,
    percent: progress?.goal_progress_percent ?? null,
    paceLine,
    forecastLine,
  };
}
