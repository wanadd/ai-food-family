import { GOAL_OPTIONS } from "@/lib/onboarding/options";
import { TOTAL_STEPS } from "@/lib/onboarding/steps";
import type { OnboardingData } from "@/lib/onboarding/types";

export function getOnboardingProgressPercent(data: OnboardingData | null): number {
  if (!data) {
    return 0;
  }
  if (data.completed) {
    return 100;
  }
  const step = Math.min(Math.max(data.currentStep, 0), TOTAL_STEPS - 1);
  return Math.round(((step + 1) / TOTAL_STEPS) * 100);
}

export function getPrimaryGoalLabel(data: OnboardingData | null): string | null {
  if (!data?.goals?.length) {
    return null;
  }
  const first = data.goals[0];
  return GOAL_OPTIONS.find((o) => o.value === first)?.label ?? null;
}

export function getGoalsSummary(data: OnboardingData | null): string {
  if (!data?.goals?.length) {
    return "Не задана";
  }
  return data.goals
    .map((v) => GOAL_OPTIONS.find((o) => o.value === v)?.label ?? v)
    .join(", ");
}
