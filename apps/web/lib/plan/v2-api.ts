import { apiFetch } from "@/lib/api-client";
import type { AppMode } from "@/lib/app-mode/types";

import type { PlanningOwnerScope, PlanningReadModel, PlanningSlotInput } from "./v2-types";

export async function createPlanningPlan(
  initData: string,
  mode: AppMode,
  payload: { owner_scope: PlanningOwnerScope; person_id?: string; household_id?: string; date_from?: string; date_to?: string; mode?: string },
  idempotencyKey: string,
): Promise<PlanningReadModel> {
  return apiFetch<PlanningReadModel>(initData, mode, "/v2/plans", {
    method: "POST",
    headers: { "Idempotency-Key": idempotencyKey },
    body: JSON.stringify(payload),
  });
}

export async function generatePlanningRevision(
  initData: string,
  mode: AppMode,
  planId: string,
  slots: PlanningSlotInput[],
  idempotencyKey: string,
  expectedRevisionId?: string,
): Promise<PlanningReadModel> {
  return apiFetch<PlanningReadModel>(initData, mode, `/v2/plans/${encodeURIComponent(planId)}/generate`, {
    method: "POST",
    headers: { "Idempotency-Key": idempotencyKey },
    body: JSON.stringify({ slots, expected_revision_id: expectedRevisionId ?? null }),
  });
}

export async function replacePlanningSlot(
  initData: string,
  mode: AppMode,
  planId: string,
  revisionId: string,
  slotKey: string,
  recipeVersionId: string,
  idempotencyKey: string,
): Promise<PlanningReadModel> {
  return apiFetch<PlanningReadModel>(initData, mode, `/v2/plans/${encodeURIComponent(planId)}/revisions/${encodeURIComponent(revisionId)}/replace`, {
    method: "POST",
    headers: { "Idempotency-Key": idempotencyKey },
    body: JSON.stringify({ slot_key: slotKey, recipe_version_id: recipeVersionId, expected_revision_id: revisionId }),
  });
}

export async function emptyPlanningSlot(
  initData: string,
  mode: AppMode,
  planId: string,
  slotId: string,
  revisionId: string,
  idempotencyKey: string,
): Promise<PlanningReadModel> {
  return apiFetch<PlanningReadModel>(initData, mode, `/v2/plans/${encodeURIComponent(planId)}/slots/${encodeURIComponent(slotId)}/empty`, {
    method: "POST",
    headers: { "Idempotency-Key": idempotencyKey },
    body: JSON.stringify({ expected_revision_id: revisionId }),
  });
}
