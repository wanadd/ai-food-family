import { redirect } from "next/navigation";

import { isPlanamUi2026Enabled } from "@/lib/planam/feature-flags";
import { LEGACY_FALLBACK_BY_2026_PATH } from "@/lib/navigation/nav-config-2026";

/** Redirect to legacy route when UI 2026 flag is off. Call at top of 2026-only pages. */
export function requirePlanamUi2026OrRedirect(path2026: string): void {
  if (!isPlanamUi2026Enabled()) {
    const fallback = LEGACY_FALLBACK_BY_2026_PATH[path2026] ?? "/";
    redirect(fallback);
  }
}

/** Redirect legacy routes to their 2026 counterparts when the flag is on. */
export function redirectLegacyToPlanam2026(path2026: string): void {
  if (isPlanamUi2026Enabled()) {
    redirect(path2026);
  }
}
