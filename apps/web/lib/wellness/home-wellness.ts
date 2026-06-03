import type { MenuOverview } from "@/lib/menu/overview-types";
import type { ProgressOverview } from "@/lib/progress/types";
import type { WaterToday } from "@/lib/water-intake/api";

import { wellnessGoalLabel } from "@/lib/wellness/goal-labels";
import { buildWellnessDayProgress } from "@/lib/wellness/wellness-status";
import { buildWellnessInsight } from "@/lib/wellness/wellness-insight";

export type HomeWellnessChip = {
  waterPercent: number | null;
  dayPercent: number;
  insight: string | null;
  goalLabel: string;
  goalProgressPercent: number | null;
};

export function buildHomeWellnessChip(input: {
  overview: MenuOverview | null;
  progress: ProgressOverview | null;
  water: WaterToday | null;
  profileComplete: boolean;
  mealsCompleted: number;
}): HomeWellnessChip | null {
  const { overview, progress, water, profileComplete, mealsCompleted } = input;

  if (!overview && !progress && !water) {
    return null;
  }

  const day = buildWellnessDayProgress({
    progress,
    water,
    checkins: [],
    overview,
    mealsCompletedOverride: mealsCompleted,
  });

  const waterTarget = water?.target_ml ?? progress?.targets?.water_target_ml;
  const waterTotal =
    water?.total_ml ?? progress?.daily_actual?.water_consumed_ml ?? 0;
  const waterPercent =
    waterTarget && waterTarget > 0
      ? Math.min(100, Math.round((waterTotal / waterTarget) * 100))
      : null;

  const insight = buildWellnessInsight({
    overview,
    progress,
    water,
    profileComplete,
    mealsCompleted,
  });

  const goalType = progress?.goal_type ?? null;
  const goalLabel = wellnessGoalLabel(
    goalType,
    overview?.plan_summary.goal_label ?? progress?.goal_label,
  );

  return {
    waterPercent,
    dayPercent: day.percent,
    insight,
    goalLabel,
    goalProgressPercent: progress?.goal_progress_percent ?? null,
  };
}
