import { apiFetch, apiGet } from "@/lib/api-client";
import type { AppMode } from "@/lib/app-mode/types";

import type {
  CareNotification,
  CareNotificationType,
  CareSettings,
  CareSettingsUpdate,
  TestCareResponse,
} from "./types";

export async function fetchCareSettings(
  initData: string,
  mode: AppMode = "personal",
): Promise<CareSettings | null> {
  return apiGet<CareSettings>(initData, mode, "/care/settings");
}

export async function updateCareSettings(
  initData: string,
  mode: AppMode,
  payload: CareSettingsUpdate,
): Promise<CareSettings> {
  return apiFetch<CareSettings>(initData, mode, "/care/settings", {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export async function fetchCareNotifications(
  initData: string,
  mode: AppMode = "personal",
): Promise<CareNotification[]> {
  const data = await apiGet<CareNotification[]>(
    initData,
    mode,
    "/care/notifications",
  );
  return data ?? [];
}

export async function sendTestCareNotification(
  initData: string,
  mode: AppMode,
  notificationType: CareNotificationType = "water",
): Promise<TestCareResponse> {
  return apiFetch<TestCareResponse>(initData, mode, "/care/test-notification", {
    method: "POST",
    body: JSON.stringify({ notification_type: notificationType }),
  });
}
