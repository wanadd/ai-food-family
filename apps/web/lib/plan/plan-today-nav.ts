import { defaultDayIndex } from "@/lib/menu/menu-days";
import type { MenuVariant } from "@/lib/menu/types";
import { PLAN_PATHS } from "@/lib/plan/plan-paths";

export const PLAN_TODAY_DAY_PARAM = "day";
export const PLAN_TODAY_DAY_STORAGE_KEY = "planam:plan-today:day";

export function parsePlanTodayDay(
  value: string | null | undefined,
  fallback: number,
): number {
  if (!value) {
    return fallback;
  }
  const parsed = Number(value);
  if (!Number.isFinite(parsed) || parsed < 1) {
    return fallback;
  }
  return Math.trunc(parsed);
}

export function resolvePlanTodayDay(
  dayParam: string | null | undefined,
  menu: MenuVariant | null,
): number {
  const fallback = menu ? defaultDayIndex(menu) : 1;
  if (!dayParam) {
    return fallback;
  }
  return parsePlanTodayDay(dayParam, fallback);
}

export function planTodayPath(dayIndex?: number | null): string {
  if (dayIndex == null || dayIndex < 1) {
    return PLAN_PATHS.today;
  }
  return `${PLAN_PATHS.today}?${PLAN_TODAY_DAY_PARAM}=${dayIndex}`;
}

export function planTodayReturnPath(
  dayIndex: number,
  menu: MenuVariant | null,
): string {
  if (dayIndex < 1) {
    return PLAN_PATHS.today;
  }
  if (!menu) {
    return planTodayPath(dayIndex);
  }
  const fallback = defaultDayIndex(menu);
  if (dayIndex === fallback && dayIndex === 1) {
    return PLAN_PATHS.today;
  }
  return planTodayPath(dayIndex);
}

export function planTodayScrollQuery(dayIndex: number): string {
  return `${PLAN_TODAY_DAY_PARAM}=${dayIndex}`;
}

export function savePlanTodayDay(dayIndex: number): void {
  if (typeof window === "undefined") {
    return;
  }
  try {
    sessionStorage.setItem(PLAN_TODAY_DAY_STORAGE_KEY, String(dayIndex));
  } catch {
    /* ignore */
  }
}

export function readStoredPlanTodayDay(): number | null {
  if (typeof window === "undefined") {
    return null;
  }
  try {
    const raw = sessionStorage.getItem(PLAN_TODAY_DAY_STORAGE_KEY);
    if (!raw) {
      return null;
    }
    const parsed = Number(raw);
    return Number.isFinite(parsed) && parsed >= 1 ? Math.trunc(parsed) : null;
  } catch {
    return null;
  }
}

export function buildPlanTodaySearchParams(
  current: URLSearchParams,
  dayIndex: number,
): URLSearchParams {
  const next = new URLSearchParams(current.toString());
  next.set(PLAN_TODAY_DAY_PARAM, String(dayIndex));
  next.delete("meal");
  next.delete("recipeId");
  next.delete("menuItemId");
  next.delete("replace");
  next.delete("outcome");
  next.delete("saved");
  next.delete("action");
  return next;
}
