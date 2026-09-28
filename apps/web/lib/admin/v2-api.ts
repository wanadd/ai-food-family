import { apiUrl } from "@/lib/api";

import { getAdminSessionToken, storeAdminSessionToken } from "./session";

export type AdminMetric = { value: number | null; state: string };
export type AdminOverview = {
  generated_at: string;
  api: AdminMetric;
  database: AdminMetric;
  users: AdminMetric;
  households: AdminMetric;
  active_subscriptions: AdminMetric;
  errors_last_24h: AdminMetric;
  analytics: AdminMetric;
};

async function adminV2Fetch<T>(path: string, init?: RequestInit): Promise<T> {
  const token = getAdminSessionToken();
  const response = await fetch(`${apiUrl}/api/v2/admin${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { "X-Admin-Session": token } : {}),
      ...init?.headers,
    },
  });
  if (!response.ok) throw new Error(response.status === 403 ? "Нет доступа" : "Админ API недоступен");
  return response.json() as Promise<T>;
}

export async function exchangeAdminSession(initData: string): Promise<void> {
  const response = await fetch(`${apiUrl}/api/v2/admin/session/exchange`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ init_data: initData }),
  });
  if (!response.ok) throw new Error("Нет доступа");
  const payload = (await response.json()) as { session_token: string };
  storeAdminSessionToken(payload.session_token);
}

export function fetchAdminOverview(): Promise<AdminOverview> {
  return adminV2Fetch<AdminOverview>("/overview");
}

export function fetchAdminAnalytics(): Promise<{
  state: string;
  message: string;
  events: Record<string, unknown>[];
}> {
  return adminV2Fetch("/analytics");
}
