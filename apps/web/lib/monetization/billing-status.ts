import type { SubscriptionOverview } from "@/lib/subscription/types";

import {
  PLANAM_LOW_AMA_THRESHOLD,
  PLANAM_TRIAL_AMS,
  PLANAM_TRIAL_DAYS,
} from "@/lib/monetization/trial-config";
import { planDisplayName } from "@/lib/monetization/plan-catalog-2026";
import { MONETIZATION_PATHS } from "@/lib/monetization/paths";

export type HomeMonetizationBanner = {
  id: "trial_ending" | "trial_ended" | "low_amas" | "period_ending";
  title: string;
  description: string;
  ctaLabel: string;
  href: string;
  tone: "soft" | "neutral";
};

export function isOnTrial(overview: SubscriptionOverview | null): boolean {
  return (
    overview?.status === "trial" ||
    overview?.plan_code === "trial" ||
    (overview?.trial_days_left != null && overview.trial_days_left > 0)
  );
}

export function isTrialEnded(overview: SubscriptionOverview | null): boolean {
  if (!overview) {
    return false;
  }
  if (overview.plan_code === "trial" && overview.trial_days_left === 0) {
    return true;
  }
  return (
    overview.trial_days_left === 0 &&
    overview.status !== "active" &&
    overview.price_rub === 0
  );
}

export function isLowAmaBalance(overview: SubscriptionOverview | null): boolean {
  if (!overview?.can_spend_ama && overview?.is_family_billing) {
    return false;
  }
  return (
    overview != null &&
    overview.ai_actions_enabled &&
    overview.ama_balance <= PLANAM_LOW_AMA_THRESHOLD
  );
}

function daysUntil(iso: string | null | undefined): number | null {
  if (!iso) {
    return null;
  }
  const end = new Date(iso).getTime();
  if (Number.isNaN(end)) {
    return null;
  }
  return Math.ceil((end - Date.now()) / 86400000);
}

export function isPeriodEndingSoon(
  overview: SubscriptionOverview | null,
): boolean {
  if (!overview || isOnTrial(overview)) {
    return false;
  }
  const left = daysUntil(overview.current_period_ends_at);
  return left != null && left >= 0 && left <= 3;
}

export function formatPeriodEnd(
  iso: string | null | undefined,
): string | null {
  if (!iso) {
    return null;
  }
  try {
    return new Date(iso).toLocaleDateString("ru-RU", {
      day: "numeric",
      month: "long",
    });
  } catch {
    return null;
  }
}

export function buildHomeMonetizationBanner(
  overview: SubscriptionOverview | null,
): HomeMonetizationBanner | null {
  if (!overview) {
    return null;
  }

  const trialDays = overview.trial_days_left;
  if (isOnTrial(overview) && trialDays != null && trialDays <= 1 && trialDays >= 0) {
    const daysText =
      trialDays === 0
        ? "сегодня последний день"
        : trialDays === 1
          ? "остался 1 день"
          : `осталось ${trialDays} дн.`;
    return {
      id: "trial_ending",
      title: "Пробный период заканчивается",
      description: `${daysText} · ${overview.ama_balance} Амов. Для продления обратитесь к администратору.`,
      ctaLabel: "Ваш тариф",
      href: MONETIZATION_PATHS.subscription,
      tone: "soft",
    };
  }

  if (isTrialEnded(overview)) {
    return {
      id: "trial_ended",
      title: "Пробный период завершён",
      description:
        "Доступ к расширенным функциям ограничен. Для продления обратитесь к администратору.",
      ctaLabel: "Ваш тариф",
      href: MONETIZATION_PATHS.subscription,
      tone: "soft",
    };
  }

  if (isLowAmaBalance(overview)) {
    return {
      id: "low_amas",
      title: "Амов почти не осталось",
      description: `На балансе ${overview.ama_balance} — хватит на 1–2 действия. Тариф управляется администратором.`,
      ctaLabel: "Баланс",
      href: MONETIZATION_PATHS.ams,
      tone: "neutral",
    };
  }

  if (isPeriodEndingSoon(overview)) {
    const endLabel = formatPeriodEnd(overview.current_period_ends_at);
    return {
      id: "period_ending",
      title: "Тариф скоро продлится",
      description: endLabel
        ? `«${planDisplayName(overview.plan_code, overview.plan_name)}» до ${endLabel}`
        : "Проверьте подписку в аккаунте",
      ctaLabel: "Подписка",
      href: MONETIZATION_PATHS.subscription,
      tone: "soft",
    };
  }

  return null;
}

export function trialStatusLine(overview: SubscriptionOverview | null): string | null {
  if (!isOnTrial(overview)) {
    return null;
  }
  const days = overview?.trial_days_left ?? PLANAM_TRIAL_DAYS;
  const ams = overview?.ama_balance ?? PLANAM_TRIAL_AMS;
  return `${days} дн. · ${ams} Амов`;
}
