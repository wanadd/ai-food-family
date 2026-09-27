import { apiFetch } from "@/lib/api-client";
import type { AppMode } from "@/lib/app-mode/types";

export type NotificationPreferenceInput = {
  subject_kind: "PERSON" | "HOUSEHOLD";
  subject_id: string;
  channel: string;
  enabled: boolean;
  timezone?: string | null;
  quiet_hours_start?: string | null;
  quiet_hours_end?: string | null;
};

export type NotificationPreference = NotificationPreferenceInput & { preference_id: string };

export function updateNotificationPreferences(
  initData: string,
  mode: AppMode,
  input: NotificationPreferenceInput,
  idempotencyKey: string,
) {
  return apiFetch<NotificationPreference>(initData, mode, "/api/v2/notification-preferences", {
    method: "POST",
    headers: { "Idempotency-Key": idempotencyKey },
    body: JSON.stringify(input),
  });
}
