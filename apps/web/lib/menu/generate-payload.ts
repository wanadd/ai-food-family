import type { AppMode } from "@/lib/app-mode/types";
import type { MenuGoalId, PlanModeId } from "@/lib/menu/planner-options";
import type { PantryList } from "@/lib/pantry/types";

import type { MenuGenerateOptions } from "./api";
import { normalizeMenuDurationDays } from "./duration-options";

export type BuildGeneratePayloadInput = {
  mode: AppMode;
  goal: MenuGoalId;
  personsCount: number;
  planDays: number;
  planMode: PlanModeId;
  wizardBudget: string;
  pantry: PantryList | null;
};

function resolvePlanMode(
  wizardBudget: string,
  planMode: PlanModeId,
): string {
  if (wizardBudget === "economy") return "economy";
  if (wizardBudget === "premium") return "healthy";
  return planMode;
}

/** Request body for POST /menus/generate (API schema fields only). */
export function buildMenuGeneratePayload(
  input: BuildGeneratePayloadInput,
): MenuGenerateOptions {
  const persons =
    input.mode === "family"
      ? Math.max(1, Math.min(20, input.personsCount))
      : 1;

  return {
    nutrition_goal: input.goal,
    plan_days: normalizeMenuDurationDays(input.planDays),
    persons_count: persons,
    plan_mode: resolvePlanMode(input.wizardBudget, input.planMode),
  };
}

export function menuGenerateDebugMeta(
  input: BuildGeneratePayloadInput,
  url: string,
): Record<string, unknown> {
  const payload = buildMenuGeneratePayload(input);
  const hasPantry = (input.pantry?.active_count ?? 0) > 0;
  const hasLeftovers =
    input.pantry?.items.some(
      (i) =>
        i.source === "manual" &&
        (i.note?.toLowerCase().includes("остат") ?? false),
    ) ?? false;

  return {
    url,
    goal: input.goal,
    plan_days: payload.plan_days,
    persons_count: payload.persons_count,
    plan_mode: payload.plan_mode,
    budget: input.wizardBudget,
    use_pantry: hasPantry,
    use_leftovers: hasLeftovers,
  };
}
