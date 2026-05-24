import type { AppMode } from "@/lib/app-mode/types";
import type { MainAdvice } from "@/lib/nutritionist/main-advice";
import {
  deferAdviceApi,
  dismissDeferredAdvice,
  fetchDeferredAdvice,
  type DeferredAdviceRow,
} from "@/lib/nutritionist/deferred-advice-api";

const STORAGE_KEY = "planam_deferred_advice";

export type DeferredAdvice = MainAdvice & {
  id: string;
  snoozedAt: string;
};

function rowToDeferred(row: DeferredAdviceRow): DeferredAdvice {
  return {
    id: String(row.id),
    title: row.title,
    body: row.body,
    snoozedAt: row.created_at,
  };
}

/** Migrate legacy localStorage entries to the API once. */
export async function migrateLocalDeferredAdvice(
  initData: string,
  mode: AppMode,
): Promise<void> {
  if (typeof window === "undefined") return;
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return;
    const parsed = JSON.parse(raw) as DeferredAdvice[];
    if (!Array.isArray(parsed)) return;
    for (const item of parsed) {
      await deferAdviceApi(initData, mode, {
        title: item.title,
        body: item.body,
      });
    }
    localStorage.removeItem(STORAGE_KEY);
  } catch {
    /* ignore */
  }
}

export async function listDeferredAdvice(
  initData: string,
  mode: AppMode,
): Promise<DeferredAdvice[]> {
  const rows = await fetchDeferredAdvice(initData, mode);
  return rows.map(rowToDeferred);
}

export async function deferAdvice(
  initData: string,
  mode: AppMode,
  advice: MainAdvice,
): Promise<void> {
  await deferAdviceApi(initData, mode, advice);
}

export async function removeDeferredAdvice(
  initData: string,
  mode: AppMode,
  id: string,
): Promise<void> {
  await dismissDeferredAdvice(initData, mode, parseInt(id, 10));
}

export function listDeferredAdviceLocal(): DeferredAdvice[] {
  return [];
}
