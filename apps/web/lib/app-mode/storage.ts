import type { AppMode } from "./types";

const STORAGE_KEY = "aifood_app_mode";

export function loadStoredMode(): AppMode | null {
  if (typeof window === "undefined") {
    return null;
  }
  const value = window.localStorage.getItem(STORAGE_KEY);
  if (value === "personal" || value === "family") {
    return value;
  }
  return null;
}

export function saveStoredMode(mode: AppMode): void {
  if (typeof window === "undefined") {
    return;
  }
  window.localStorage.setItem(STORAGE_KEY, mode);
}
