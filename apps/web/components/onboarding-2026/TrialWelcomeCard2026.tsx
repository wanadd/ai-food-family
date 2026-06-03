import { Card2026 } from "@/components/planam-2026/ui/Card2026";
import {
  ONBOARDING_TRIAL_AMS,
  ONBOARDING_TRIAL_DAYS,
} from "@/lib/onboarding-2026/config";

type TrialWelcomeCard2026Props = {
  amaBalance?: number | null;
};

export function TrialWelcomeCard2026({ amaBalance }: TrialWelcomeCard2026Props) {
  const amsLine =
    amaBalance != null && amaBalance > 0
      ? `На балансе ${amaBalance} Амов — хватит на подбор блюд и замены.`
      : `В подарок ${ONBOARDING_TRIAL_AMS} Амов на подбор и замены блюд.`;

  return (
    <Card2026 className="border-sage-200 bg-sage-50/80 dark:border-sage-700/40 dark:bg-sage-700/15">
      <p className="pa26-micro font-semibold uppercase tracking-wide text-sage-700 dark:text-sage-300">
        Знакомство с ПланАм
      </p>
      <p className="pa26-card-title mt-2">
        {ONBOARDING_TRIAL_DAYS} дня полного доступа
      </p>
      <p className="pa26-body mt-1 text-pa-muted">{amsLine}</p>
      <p className="pa26-caption mt-2 text-pa-muted">
        Без оплаты сейчас — сначала попробуйте план в деле.
      </p>
    </Card2026>
  );
}
