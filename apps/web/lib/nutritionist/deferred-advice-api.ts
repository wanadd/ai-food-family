import { apiFetch, apiGet } from "@/lib/api-client";
import type { AppMode } from "@/lib/app-mode/types";

import type { MainAdvice } from "@/lib/nutritionist/main-advice";

export type DeferredAdviceRow = {
  id: number;
  advice_key: string;
  title: string;
  body: string;
  status: string;
  created_at: string;
  updated_at: string;
};

export async function fetchDeferredAdvice(
  initData: string,
  mode: AppMode,
): Promise<DeferredAdviceRow[]> {
  const data = await apiGet<DeferredAdviceRow[]>(
    initData,
    mode,
    "/nutritionist/deferred-advice",
  );
  return data ?? [];
}

export async function fetchSuppressedAdviceTitles(
  initData: string,
  mode: AppMode,
): Promise<string[]> {
  const data = await apiGet<string[]>(
    initData,
    mode,
    "/nutritionist/deferred-advice/suppressed-titles",
  );
  return data ?? [];
}

export async function deferAdviceApi(
  initData: string,
  mode: AppMode,
  advice: MainAdvice,
): Promise<DeferredAdviceRow> {
  return apiFetch(initData, mode, "/nutritionist/deferred-advice", {
    method: "POST",
    body: JSON.stringify({ title: advice.title, body: advice.body }),
  });
}

/** Remove deferral so the advice can appear in active recommendations again. */
export async function restoreDeferredAdvice(
  initData: string,
  mode: AppMode,
  id: number,
): Promise<void> {
  await apiFetch(initData, mode, `/nutritionist/deferred-advice/${id}`, {
    method: "DELETE",
  });
}

export async function updateDeferredAdviceStatus(
  initData: string,
  mode: AppMode,
  id: number,
  status: "completed" | "dismissed",
): Promise<DeferredAdviceRow> {
  return apiFetch(initData, mode, `/nutritionist/deferred-advice/${id}`, {
    method: "PATCH",
    body: JSON.stringify({ status }),
  });
}
