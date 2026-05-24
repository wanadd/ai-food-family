import type { NutritionProfileData } from "@/lib/nutrition-profile/types";
import type { ProgressOverview } from "@/lib/progress/types";

export type GoalProgressCard = {
  startWeight: string;
  currentWeight: string;
  targetWeight: string;
  remaining: string | null;
  percent: number | null;
  startedAt: string | null;
  daysElapsed: number | null;
  paceLine: string | null;
  forecastLine: string | null;
};

function formatKg(value: number | null | undefined): string {
  if (value == null || Number.isNaN(Number(value))) return "—";
  return `${Number(value).toFixed(1)} кг`;
}

function formatDateRu(iso: string | null | undefined): string | null {
  if (!iso) return null;
  try {
    return new Date(iso).toLocaleDateString("ru-RU", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
    });
  } catch {
    return null;
  }
}

function computePercent(
  goalType: string | null | undefined,
  start: number,
  current: number,
  target: number,
): number | null {
  if (goalType === "lose") {
    const total = start - target;
    if (total <= 0) return current <= target ? 100 : 0;
    return Math.min(100, Math.max(0, Math.round(((start - current) / total) * 100)));
  }
  if (goalType === "gain") {
    const total = target - start;
    if (total <= 0) return current >= target ? 100 : 0;
    return Math.min(100, Math.max(0, Math.round(((current - start) / total) * 100)));
  }
  return null;
}

export function buildGoalProgressCard(
  profile: NutritionProfileData | null,
  progress: ProgressOverview | null,
): GoalProgressCard {
  const gd = profile?.goal_details;
  const goalType = progress?.goal_type ?? profile?.nutrition_goal ?? null;

  const startNum =
    progress?.start_weight_kg ??
    gd?.current_weight_kg ??
    progress?.current_weight_kg ??
    profile?.weight_kg ??
    null;
  const currentNum =
    progress?.current_weight_kg ?? gd?.current_weight_kg ?? profile?.weight_kg ?? null;
  const targetNum = progress?.target_weight_kg ?? gd?.target_weight_kg ?? null;

  let remaining: string | null = null;
  if (currentNum != null && targetNum != null) {
    const diff = Number(currentNum) - Number(targetNum);
    remaining =
      goalType === "lose"
        ? `${Math.max(0, diff).toFixed(1)} кг`
        : `${Math.abs(diff).toFixed(1)} кг`;
  }

  let percent = progress?.goal_progress_percent ?? null;
  if (
    percent == null &&
    startNum != null &&
    currentNum != null &&
    targetNum != null &&
    goalType
  ) {
    percent = computePercent(goalType, Number(startNum), Number(currentNum), Number(targetNum));
  }

  const startedIso = progress?.goal_started_at ?? gd?.target_date ?? null;
  const startedAt = formatDateRu(startedIso);
  let daysElapsed: number | null = null;
  if (startedIso) {
    const startMs = new Date(startedIso).getTime();
    if (!Number.isNaN(startMs)) {
      daysElapsed = Math.max(0, Math.floor((Date.now() - startMs) / 86400000));
    }
  }

  let paceLine: string | null = null;
  if (progress?.weight_change_week_kg != null) {
    const w = progress.weight_change_week_kg;
    paceLine = `Средний темп: ${Math.abs(w).toFixed(1)} кг в неделю`;
  } else if (gd?.goal_pace) {
    const paceLabels: Record<string, string> = {
      soft: "мягкий",
      standard: "стандартный",
      intensive: "интенсивный",
    };
    paceLine = `Темп: ${paceLabels[gd.goal_pace] ?? gd.goal_pace}`;
  }

  let forecastLine: string | null = null;
  if (progress?.goal_forecast_date) {
    const fd = formatDateRu(progress.goal_forecast_date);
    if (fd) forecastLine = `Прогноз: ${fd}`;
  } else if (gd?.target_date) {
    forecastLine = `Цель к ${gd.target_date}`;
  }

  return {
    startWeight: formatKg(startNum),
    currentWeight: formatKg(currentNum),
    targetWeight: formatKg(targetNum),
    remaining,
    percent,
    startedAt,
    daysElapsed,
    paceLine,
    forecastLine,
  };
}
