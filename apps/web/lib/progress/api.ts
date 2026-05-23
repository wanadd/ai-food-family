import { apiFetch, apiGet } from "@/lib/api-client";
import type { AppMode } from "@/lib/app-mode/types";

import type {
  ProgressEntry,
  ProgressEntryCreate,
  ProgressOverview,
  TrainingEntry,
  TrainingEntryCreate,
} from "./types";

export async function fetchProgressOverview(
  initData: string,
  mode: AppMode,
): Promise<ProgressOverview | null> {
  return apiGet<ProgressOverview>(initData, mode, "/progress/me");
}

export async function createProgressEntry(
  initData: string,
  mode: AppMode,
  payload: ProgressEntryCreate,
): Promise<ProgressEntry> {
  return apiFetch<ProgressEntry>(initData, mode, "/progress/me", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function createTrainingEntry(
  initData: string,
  mode: AppMode,
  payload: TrainingEntryCreate,
): Promise<TrainingEntry> {
  return apiFetch<TrainingEntry>(initData, mode, "/progress/training", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function updateProgressPrivacy(
  initData: string,
  mode: AppMode,
  showProgressToFamily: boolean,
): Promise<{ show_progress_to_family: boolean }> {
  return apiFetch(initData, mode, "/progress/settings", {
    method: "PATCH",
    body: JSON.stringify({ show_progress_to_family: showProgressToFamily }),
  });
}
