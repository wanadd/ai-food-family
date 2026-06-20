/**
 * PLANAM 2026 feature flags (Sprint 0).
 * @see docs/PLANAM_2026_DECISION_RECORD.md DR-006
 */

export function isPlanamUi2026Enabled(): boolean {
  return process.env.NEXT_PUBLIC_PLANAM_UI_2026 === "true";
}

/** Defer phone gate until WOW completes (CR3). */
export function isDeferPhoneGateEnabled(): boolean {
  return process.env.NEXT_PUBLIC_PLANAM_DEFER_PHONE_GATE !== "false";
}

/** Grace redirects legacy → 2026 routes (off by default, Sprint 2). */
export function isPlanamRouteRedirectsEnabled(): boolean {
  return (
    isPlanamUi2026Enabled() &&
    process.env.NEXT_PUBLIC_PLANAM_ROUTE_REDIRECTS === "true"
  );
}
