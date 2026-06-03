/**
 * Map legacy overview redirect_path → 2026 routes when UI flag is on.
 */

import type { HomeNextActionId } from "@/lib/menu/overview-types";

const LEGACY_TO_2026: Record<string, string> = {
  "/menu/generate": "/plan/generate",
  "/menu/current": "/plan/today",
  "/shopping": "/home/shopping",
  "/shopping/pantry": "/home/pantry",
  "/profile/nutrition": "/profile/nutrition",
  "/health": "/wellness",
  "/health/today": "/wellness",
  "/health/chat": "/wellness/chat",
  "/nutritionist": "/wellness/chat",
  "/progress": "/wellness",
  "/subscription": "/account/subscription",
};

export function resolveHomeRedirectPath(
  legacyPath: string,
  use2026Routes: boolean,
  actionId?: HomeNextActionId | null,
): string {
  if (!use2026Routes) {
    return legacyPath;
  }
  if (actionId === "meal_outcome") {
    return "/plan/today?outcome=1";
  }
  if (actionId === "open_today") {
    return "/plan/today";
  }
  if (actionId === "generate_menu") {
    return "/plan/generate";
  }
  if (actionId === "complete_nutrition") {
    return "/profile/nutrition";
  }
  return LEGACY_TO_2026[legacyPath] ?? legacyPath;
}
