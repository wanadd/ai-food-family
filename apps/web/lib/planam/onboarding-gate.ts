/**
 * PLANAM 2026 onboarding / WOW session flags (CR3).
 */

import { isDeferPhoneGateEnabled } from "./feature-flags";

const WOW_KEY = "planam_wow_complete";

export function isWowComplete(): boolean {
  if (typeof window === "undefined") return false;
  return sessionStorage.getItem(WOW_KEY) === "1";
}

export function markWowComplete(): void {
  if (typeof window === "undefined") return;
  sessionStorage.setItem(WOW_KEY, "1");
}

export function clearWowComplete(): void {
  if (typeof window === "undefined") return;
  sessionStorage.removeItem(WOW_KEY);
}

/**
 * Phone gate blocks only when defer is on and WOW not yet done.
 */
export function shouldBlockForPhone(
  hasPhone: boolean,
  phoneSkipped: boolean,
): boolean {
  if (hasPhone || phoneSkipped) return false;
  if (!isDeferPhoneGateEnabled()) return true;
  return isWowComplete();
}
