import { apiUrl } from "@/lib/api";
import { buildProtectedRequestHeaders } from "@/lib/audit/audit-mode";

import type {
  NotificationSettings,
  NotificationSettingsUpdate,
} from "./types";

async function notificationFetch<T>(
  path: string,
  initData: string,
  init?: RequestInit,
): Promise<T> {
  const response = await fetch(`${apiUrl}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...buildProtectedRequestHeaders(initData),
      ...init?.headers,
    },
  });

  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as
      | { detail?: string }
      | null;
    throw new Error(payload?.detail ?? `HTTP ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export async function fetchNotificationSettings(
  initData: string,
): Promise<NotificationSettings> {
  return notificationFetch<NotificationSettings>(
    "/notifications/settings",
    initData,
  );
}

export async function updateNotificationSettings(
  initData: string,
  patch: NotificationSettingsUpdate,
): Promise<NotificationSettings> {
  return notificationFetch<NotificationSettings>(
    "/notifications/settings",
    initData,
    {
      method: "PUT",
      body: JSON.stringify(patch),
    },
  );
}
