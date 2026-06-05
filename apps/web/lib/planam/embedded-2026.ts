"use client";

import { usePathname } from "next/navigation";

import { isPlanamUi2026Enabled } from "@/lib/planam/feature-flags";

/** True when a legacy screen is rendered under a 2026 account (or nested) route. */
export function usePlanam2026Embedded(routePrefix: string): boolean {
  const pathname = usePathname();
  return isPlanamUi2026Enabled() && pathname.startsWith(routePrefix);
}

export function isPlanam2026EmbeddedPath(pathname: string, routePrefix: string): boolean {
  return isPlanamUi2026Enabled() && pathname.startsWith(routePrefix);
}
