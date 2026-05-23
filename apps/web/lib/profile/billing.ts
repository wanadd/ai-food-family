/** Placeholder until subscription API (roadmap stage 10). */
export type ProfilePlanId = "personal" | "shared" | "family" | "pro";

export type ProfileBilling = {
  planId: ProfilePlanId;
  planLabel: string;
  amasBalance: number;
};

const PLAN_LABELS: Record<ProfilePlanId, string> = {
  personal: "Личный",
  shared: "Совместный",
  family: "Семейный",
  pro: "ПланАм PRO",
};

/** Default billing snapshot for profile UI. */
export function getProfileBilling(): ProfileBilling {
  return {
    planId: "personal",
    planLabel: PLAN_LABELS.personal,
    amasBalance: 50,
  };
}

export function formatAmasBalance(balance: number): string {
  const n = Math.abs(Math.floor(balance));
  const mod10 = n % 10;
  const mod100 = n % 100;
  if (mod10 === 1 && mod100 !== 11) {
    return `${n} Ам`;
  }
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 10 || mod100 >= 20)) {
    return `${n} Ама`;
  }
  return `${n} Амов`;
}
