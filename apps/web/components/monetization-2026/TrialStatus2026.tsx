import { Card2026 } from "@/components/planam-2026/ui/Card2026";
import {
  PLANAM_TRIAL_AMS,
  PLANAM_TRIAL_DAYS,
} from "@/lib/monetization/trial-config";
import { trialStatusLine } from "@/lib/monetization/billing-status";
import type { SubscriptionOverview } from "@/lib/subscription/types";

type TrialStatus2026Props = {
  overview: SubscriptionOverview;
};

export function TrialStatus2026({ overview }: TrialStatus2026Props) {
  const line = trialStatusLine(overview);
  const days = overview.trial_days_left ?? PLANAM_TRIAL_DAYS;
  const ams = overview.ama_balance ?? PLANAM_TRIAL_AMS;

  return (
    <Card2026 className="border-sage-200 bg-sage-50/80 dark:border-sage-700/40 dark:bg-sage-700/15">
      <p className="pa26-micro font-semibold uppercase tracking-wide text-sage-700 dark:text-sage-300">
        Пробный период
      </p>
      <p className="pa26-card-title mt-1">
        {days} {days === 1 ? "день" : days < 5 ? "дня" : "дней"} · {ams} Амов
      </p>
      {line ? (
        <p className="pa26-caption mt-1 text-pa-muted">
          Без оплаты сейчас — попробуйте план в деле
        </p>
      ) : null}
    </Card2026>
  );
}
