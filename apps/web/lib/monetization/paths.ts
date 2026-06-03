/** Canonical monetization routes (PLANAM 2026). */
export const MONETIZATION_PATHS = {
  subscription: "/account/subscription",
  ams: "/account/ams",
  checkout: "/account/subscription/checkout",
} as const;

export function subscriptionCheckoutPath(planCode: string): string {
  return `${MONETIZATION_PATHS.checkout}?plan=${encodeURIComponent(planCode)}`;
}
