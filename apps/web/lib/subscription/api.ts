import { apiFetch, apiGet } from "@/lib/api-client";
import type { AppMode } from "@/lib/app-mode/types";

import type { SubscriptionOverview } from "./types";

export async function fetchSubscriptionOverview(
  initData: string,
  mode: AppMode = "personal",
): Promise<SubscriptionOverview | null> {
  return apiGet<SubscriptionOverview>(initData, mode, "/subscriptions/me");
}

export async function selectPlanStub(
  initData: string,
  mode: AppMode,
  planCode: string,
): Promise<SubscriptionOverview> {
  return apiFetch<SubscriptionOverview>(initData, mode, "/subscriptions/select-plan", {
    method: "POST",
    body: JSON.stringify({ plan_code: planCode }),
  });
}
