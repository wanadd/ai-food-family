import type { SubscriptionOverview } from "@/lib/subscription/types";

export type ProfileBilling = {
  planCode: string;
  planLabel: string;
  amasBalance: number;
  menuRemaining: number | null;
};

export function billingFromSubscription(
  data: SubscriptionOverview | null,
): ProfileBilling {
  if (!data) {
    return {
      planCode: "trial",
      planLabel: "Пробный",
      amasBalance: 0,
      menuRemaining: null,
    };
  }
  return {
    planCode: data.plan_code,
    planLabel: data.plan_name,
    amasBalance: data.ama_balance,
    menuRemaining: data.menu_generations_remaining,
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
