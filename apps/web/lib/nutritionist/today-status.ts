import type { ProgressOverview } from "@/lib/progress/types";

export type TodayStatus = {
  goalLabel: string;
  goalToTarget: string | null;
  progressPercent: number | null;
  statusLine: string;
  familyLine: string | null;
};

export function buildTodayStatus(input: {
  goalLabel: string | null;
  progress: ProgressOverview | null;
  familyName: string | null;
  memberCount: number;
  mode: string;
}): TodayStatus {
  const { goalLabel, progress, familyName, memberCount, mode } = input;

  let goalToTarget: string | null = null;
  if (
    progress?.weight_change_week_kg != null &&
    progress.goal_type === "lose"
  ) {
    const remaining = Math.max(0, 7 + progress.weight_change_week_kg);
    goalToTarget = `−${remaining.toFixed(1)} кг`;
  } else if (progress?.weight_change_week_kg != null) {
    const delta = progress.weight_change_week_kg;
    goalToTarget =
      delta === 0
        ? "на цели"
        : `${delta > 0 ? "+" : ""}${delta.toFixed(1)} кг за неделю`;
  }

  const progressPercent = progress?.goal_progress_percent ?? null;

  let statusLine = "Сегодня вы движетесь по плану.";
  if (progress?.weight_change_week_kg != null && progress.weight_change_week_kg > 0.3) {
    statusLine = "Небольшой набор за неделю — проверьте порции.";
  } else if (
    progress?.weight_change_week_kg != null &&
    progress.weight_change_week_kg < -0.2
  ) {
    statusLine = "Хороший темп — продолжайте в том же ритме.";
  }

  let familyLine: string | null = null;
  if (mode === "family" && familyName) {
    familyLine = `Семья: ${familyName}`;
  } else if (mode === "family" && memberCount > 0) {
    familyLine = `Семья: ${memberCount} участника`;
  }

  return {
    goalLabel: goalLabel ?? "Цель не задана",
    goalToTarget,
    progressPercent,
    statusLine,
    familyLine,
  };
}
