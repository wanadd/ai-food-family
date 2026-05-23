import { apiFetch, apiGet } from "@/lib/api-client";
import type { AppMode } from "@/lib/app-mode/types";

import type {
  AdminAiUsageRow,
  AdminBackupRow,
  AdminFamilyRow,
  AdminGrantResponse,
  AdminPlanOption,
  AdminSubscriptionRow,
  AdminSummary,
  AdminUserRow,
} from "./types";

const MODE: AppMode = "personal";

export async function fetchAdminSummary(
  initData: string,
): Promise<AdminSummary | null> {
  return apiGet<AdminSummary>(initData, MODE, "/admin/summary");
}

export async function fetchAdminUsers(initData: string): Promise<AdminUserRow[]> {
  const data = await apiGet<AdminUserRow[]>(initData, MODE, "/admin/users");
  return data ?? [];
}

export async function fetchAdminFamilies(
  initData: string,
): Promise<AdminFamilyRow[]> {
  const data = await apiGet<AdminFamilyRow[]>(initData, MODE, "/admin/families");
  return data ?? [];
}

export async function fetchAdminSubscriptions(
  initData: string,
): Promise<AdminSubscriptionRow[]> {
  const data = await apiGet<AdminSubscriptionRow[]>(
    initData,
    MODE,
    "/admin/subscriptions",
  );
  return data ?? [];
}

export async function fetchAdminPlans(initData: string): Promise<AdminPlanOption[]> {
  const data = await apiGet<AdminPlanOption[]>(initData, MODE, "/admin/plans");
  return data ?? [];
}

export async function fetchAdminAiUsage(
  initData: string,
): Promise<AdminAiUsageRow[]> {
  const data = await apiGet<AdminAiUsageRow[]>(initData, MODE, "/admin/ai-usage");
  return data ?? [];
}

export async function fetchAdminBackups(initData: string): Promise<AdminBackupRow[]> {
  const data = await apiGet<AdminBackupRow[]>(initData, MODE, "/admin/backups");
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
  return apiFetch(initData, MODE, "/admin/subscriptions/grant", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function grantAdminAms(
  initData: string,
  body: { user_id: number; amount: number; reason?: string },
): Promise<AdminGrantResponse> {
  return apiFetch(initData, MODE, "/admin/ams/grant", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function createAdminBackup(initData: string): Promise<{
  id: string;
  message: string;
}> {
  return apiFetch(initData, MODE, "/admin/backups/create", {
    method: "POST",
    body: JSON.stringify({}),
  });
}
