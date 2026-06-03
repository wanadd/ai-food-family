"use client";

import { useRouter } from "next/navigation";

import { BottomSheet2026 } from "@/components/planam-2026/ui/BottomSheet2026";
import { Button2026 } from "@/components/planam-2026/ui/Button2026";
import type { PaywallOpenOptions } from "@/lib/monetization/paywall";
import { paywallCopy } from "@/lib/monetization/paywall";
import {
  MONETIZATION_PATHS,
  subscriptionCheckoutPath,
} from "@/lib/monetization/paths";
import type { RetailPlanCode } from "@/lib/monetization/plan-catalog-2026";

type PaywallSheet2026Props = {
  open: boolean;
  options: PaywallOpenOptions | null;
  onClose: () => void;
};

function defaultPlanForReason(
  reason: PaywallOpenOptions["reason"],
  suggested?: RetailPlanCode,
): RetailPlanCode {
  if (suggested) {
    return suggested;
  }
  if (reason === "pro_feature") {
    return "pro";
  }
  return "personal";
}

export function PaywallSheet2026({
  open,
  options,
  onClose,
}: PaywallSheet2026Props) {
  const router = useRouter();

  if (!options) {
    return null;
  }

  const copy = paywallCopy(options.reason, options.featureLabel);
  const planCode = defaultPlanForReason(
    options.reason,
    options.suggestedPlanCode,
  );

  function goPlans() {
    onClose();
    const q = options?.returnTo
      ? `?returnTo=${encodeURIComponent(options.returnTo)}`
      : "";
    router.push(`${MONETIZATION_PATHS.subscription}${q}`);
  }

  function goCheckout() {
    onClose();
    router.push(subscriptionCheckoutPath(planCode));
  }

  function goAms() {
    onClose();
    router.push(MONETIZATION_PATHS.ams);
  }

  return (
    <BottomSheet2026 open={open} title={copy.title} onClose={onClose}>
      <p className="pa26-body text-pa-muted">{copy.description}</p>
      <div className="mt-5 flex flex-col gap-2">
        <Button2026 size="wide" onClick={goCheckout}>
          {copy.primaryCta}
        </Button2026>
        <Button2026 size="wide" variant="secondary" onClick={goPlans}>
          Сравнить тарифы
        </Button2026>
        {copy.amsLinkLabel ? (
          <button
            type="button"
            onClick={goAms}
            className="py-2 text-center pa26-micro font-semibold text-sage-700 dark:text-sage-300"
          >
            {copy.amsLinkLabel}
          </button>
        ) : null}
        <Button2026 size="wide" variant="ghost" onClick={onClose}>
          {copy.secondaryCta}
        </Button2026>
      </div>
    </BottomSheet2026>
  );
}
