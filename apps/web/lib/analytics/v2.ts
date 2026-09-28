const FORBIDDEN_KEYS = new Set([
  "allergy", "allergies", "restriction", "restrictions", "health", "child",
  "receipt", "invitation_token", "auth_token", "token", "secret", "prompt",
  "telegram_id", "phone", "email",
]);

export type AnalyticsEventName =
  | "plan_opened" | "recipe_opened" | "shopping_opened" | "wellness_opened"
  | "event_created" | "event_rsvp_recorded";

export function sanitizeAnalyticsPayload(payload: Record<string, unknown>): Record<string, unknown> {
  return Object.fromEntries(Object.entries(payload).filter(([key, value]) => {
    if (FORBIDDEN_KEYS.has(key.toLowerCase())) return false;
    return typeof value === "string" || typeof value === "number" || typeof value === "boolean" || value === null;
  }));
}

export function trackAnalyticsEvent(name: AnalyticsEventName, payload: Record<string, unknown> = {}): void {
  if (typeof window === "undefined") return;
  // Provider-neutral boundary. W9 intentionally has no speculative warehouse.
  window.dispatchEvent(new CustomEvent("planam:analytics", { detail: { name, payload: sanitizeAnalyticsPayload(payload) } }));
}
