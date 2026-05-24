import { apiUrl } from "@/lib/api";
import { parseApiErrorDetail } from "@/lib/api-errors";

import type { AppMode } from "@/lib/app-mode/types";

import { getAdminSessionToken } from "./session";
import type {
  AdminAiUsageRow,
  AdminAmaTransactionRow,
  AdminAmsActionBody,
  AdminAmsSummary,
  AdminBackupRow,
  AdminErrorRow,
  AdminFamilyCard,
  AdminFamilyRow,
  AdminGrantResponse,
  AdminOpenAiStats,
  AdminPlanOption,
  AdminSubscriptionActionBody,
  AdminSubscriptionRow,
  AdminSummary,
  AdminUserCard,
  AdminUserRow,
} from "./types";

const MODE: AppMode = "personal";

function adminHeaders(initData: string, extra?: HeadersInit): HeadersInit {
  const token = getAdminSessionToken();
  return {
    "Content-Type": "application/json",
    "X-Telegram-Init-Data": initData,
    "X-App-Mode": MODE,
    ...(token ? { "X-Admin-Session": token } : {}),
    ...extra,
  };
}

async function adminGet<T>(initData: string, path: string): Promise<T | null> {
  const response = await fetch(`${apiUrl}${path}`, {
    headers: adminHeaders(initData),
  });
  if (!response.ok) return null;
  const text = await response.text();
  if (!text || text === "null") return null;
  return JSON.parse(text) as T;
}

async function adminFetch<T>(
  initData: string,
  path: string,
  init?: RequestInit,
): Promise<T> {
  const response = await fetch(`${apiUrl}${path}`, {
    ...init,
    headers: adminHeaders(initData, init?.headers),
  });
  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as
      | { detail?: unknown }
      | null;
    const parsed = parseApiErrorDetail(payload?.detail);
    throw new Error(parsed?.message ?? "Нет доступа");
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export async function pingAdmin(initData: string): Promise<boolean> {
  const data = await adminGet<{ ok: boolean }>(initData, "/admin/ping");
  return Boolean(data?.ok);
}

export async function fetchAdminSummary(
  initData: string,
): Promise<AdminSummary | null> {
  return adminGet<AdminSummary>(initData, "/admin/summary");
}

export async function fetchAdminUsers(
  initData: string,
  params?: { q?: string; filter?: string },
): Promise<AdminUserRow[]> {
  const search = new URLSearchParams();
  if (params?.q) search.set("q", params.q);
  if (params?.filter && params.filter !== "all") search.set("filter", params.filter);
  const qs = search.toString();
  const data = await adminGet<AdminUserRow[]>(
    initData,
    `/admin/users${qs ? `?${qs}` : ""}`,
  );
  return data ?? [];
}

export async function fetchAdminFamilies(
  initData: string,
): Promise<AdminFamilyRow[]> {
  const data = await adminGet<AdminFamilyRow[]>(initData, "/admin/families");
  return data ?? [];
}

export async function fetchAdminSubscriptions(
  initData: string,
): Promise<AdminSubscriptionRow[]> {
  const data = await adminGet<AdminSubscriptionRow[]>(
    initData,
    "/admin/subscriptions",
  );
  return data ?? [];
}

export async function fetchAdminPlans(initData: string): Promise<AdminPlanOption[]> {
  const data = await adminGet<AdminPlanOption[]>(initData, "/admin/plans");
  return data ?? [];
}

export async function fetchAdminAiUsage(
  initData: string,
): Promise<AdminAiUsageRow[]> {
  const data = await adminGet<AdminAiUsageRow[]>(initData, "/admin/ai-usage");
  return data ?? [];
}

export async function fetchAdminOpenAi(
  initData: string,
  period: string,
): Promise<AdminOpenAiStats | null> {
  return adminGet<AdminOpenAiStats>(
    initData,
    `/admin/openai?period=${encodeURIComponent(period)}`,
  );
}

export async function fetchAdminAmsSummary(
  initData: string,
): Promise<AdminAmsSummary | null> {
  return adminGet<AdminAmsSummary>(initData, "/admin/ams/summary");
}

export async function fetchAdminAmaTransactions(
  initData: string,
): Promise<AdminAmaTransactionRow[]> {
  const data = await adminGet<AdminAmaTransactionRow[]>(
    initData,
    "/admin/ams/transactions",
  );
  return data ?? [];
}

export async function fetchAdminErrors(
  initData: string,
): Promise<AdminErrorRow[]> {
  const data = await adminGet<AdminErrorRow[]>(initData, "/admin/errors");
  return data ?? [];
}

export async function fetchAdminBackups(initData: string): Promise<AdminBackupRow[]> {
  const data = await adminGet<AdminBackupRow[]>(initData, "/admin/backups");
  return data ?? [];
}

export async function grantAdminSubscription(
  initData: string,
  body: {
    user_id: number;
    plan_code: string;
    extend_days?: number;
    promo_note?: string;
  },
): Promise<AdminGrantResponse> {
  return adminFetch(initData, "/admin/subscriptions/grant", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function grantAdminAms(
  initData: string,
  body: { user_id: number; amount: number; reason?: string },
): Promise<AdminGrantResponse> {
  return adminFetch(initData, "/admin/ams/grant", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function grantAdminFamilyAms(
  initData: string,
  body: { family_id: number; amount: number; reason?: string },
): Promise<AdminGrantResponse> {
  return adminFetch(initData, "/admin/ams/grant-family", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function deductAdminAms(
  initData: string,
  body: { user_id: number; amount: number; reason?: string },
): Promise<AdminGrantResponse> {
  return adminFetch(initData, "/admin/ams/deduct", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function fetchAdminUserCard(
  initData: string,
  userId: number,
): Promise<AdminUserCard | null> {
  return adminGet<AdminUserCard>(initData, `/admin/users/${userId}`);
}

export async function fetchAdminFamilyCard(
  initData: string,
  familyId: number,
): Promise<AdminFamilyCard | null> {
  return adminGet<AdminFamilyCard>(initData, `/admin/families/${familyId}`);
}

export async function adminUserAction(
  initData: string,
  userId: number,
  path: string,
  method: "POST" | "DELETE" = "POST",
  body?: unknown,
): Promise<AdminGrantResponse> {
  return adminFetch(initData, `/admin/users/${userId}${path}`, {
    method,
    body: body ? JSON.stringify(body) : undefined,
  });
}

export async function adminFamilyAction(
  initData: string,
  familyId: number,
  path: string,
  method: "POST" | "DELETE" | "PATCH" = "POST",
  body?: unknown,
): Promise<AdminGrantResponse> {
  return adminFetch(initData, `/admin/families/${familyId}${path}`, {
    method,
    body: body ? JSON.stringify(body) : undefined,
  });
}

export async function adminUserSubscription(
  initData: string,
  userId: number,
  action: "grant" | "extend" | "disable" | "change-plan",
  body?: AdminSubscriptionActionBody | { days?: number; reason?: string },
): Promise<AdminGrantResponse> {
  return adminUserAction(initData, userId, `/subscription/${action}`, "POST", body);
}

export async function adminUserAms(
  initData: string,
  userId: number,
  action: "add" | "remove" | "reset",
  body?: AdminAmsActionBody,
): Promise<AdminGrantResponse> {
  return adminUserAction(initData, userId, `/ams/${action}`, "POST", body);
}

export async function adminFamilySubscription(
  initData: string,
  familyId: number,
  action: "grant" | "extend" | "disable" | "change-plan",
  body?: AdminSubscriptionActionBody | { days?: number; reason?: string },
): Promise<AdminGrantResponse> {
  return adminFamilyAction(
    initData,
    familyId,
    `/subscription/${action}`,
    "POST",
    body,
  );
}

export async function adminFamilyAms(
  initData: string,
  familyId: number,
  action: "add" | "remove" | "reset",
  body?: AdminAmsActionBody,
): Promise<AdminGrantResponse> {
  return adminFamilyAction(initData, familyId, `/ams/${action}`, "POST", body);
}

export async function adminRemoveFamilyMember(
  initData: string,
  familyId: number,
  memberId: number,
): Promise<AdminGrantResponse> {
  return adminFetch(
    initData,
    `/admin/families/${familyId}/members/${memberId}`,
    { method: "DELETE" },
  );
}

export async function adminRenameFamily(
  initData: string,
  familyId: number,
  name: string,
): Promise<AdminGrantResponse> {
  return adminFetch(initData, `/admin/families/${familyId}`, {
    method: "PATCH",
    body: JSON.stringify({ name }),
  });
}

export async function createAdminBackup(initData: string): Promise<{
  id: string;
  message: string;
}> {
  return adminFetch(initData, "/admin/backups/create", {
    method: "POST",
    body: JSON.stringify({}),
  });
}
