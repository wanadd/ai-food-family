const PERSONS_KEY = "planam-menu-persons";
const PLAN_MODE_KEY = "planam-menu-plan-mode";

export function loadPersonsOverride(): number | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem(PERSONS_KEY);
  if (!raw) return null;
  const n = parseInt(raw, 10);
  return Number.isNaN(n) ? null : n;
}

export function savePersonsOverride(count: number): void {
  localStorage.setItem(PERSONS_KEY, String(count));
}

export function clearPersonsOverride(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(PERSONS_KEY);
}

export function loadPlanMode(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(PLAN_MODE_KEY);
}

export function savePlanMode(mode: string): void {
  localStorage.setItem(PLAN_MODE_KEY, mode);
}
