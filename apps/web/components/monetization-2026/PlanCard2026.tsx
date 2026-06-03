"use client";

import { Button2026 } from "@/components/planam-2026/ui/Button2026";
import { cn } from "@/lib/planam/cn";
import type { PlanCatalogEntry } from "@/lib/monetization/plan-catalog-2026";
import type { SubscriptionPlanInfo } from "@/lib/subscription/types";

type PlanCard2026Props = {
  catalog: PlanCatalogEntry;
  apiPlan: SubscriptionPlanInfo;
  isCurrent: boolean;
  selecting?: boolean;
  onSelect: (code: string) => void;
};

function priceLabel(rub: number): string {
  if (rub <= 0) {
    return "Бесплатно";
  }
  return `${rub} ₽/мес`;
}

export function PlanCard2026({
  catalog,
  apiPlan,
  isCurrent,
  selecting = false,
  onSelect,
}: PlanCard2026Props) {
  return (
    <article
      className={cn(
        "rounded-card border p-4 shadow-soft dark:shadow-none",
        isCurrent
          ? "border-sage-400 bg-sage-50/50 dark:border-sage-500/50 dark:bg-sage-700/20"
          : "border-pa-border bg-pa-surface",
        catalog.isPro && !isCurrent && "ring-1 ring-sage-300/50 dark:ring-sage-500/30",
      )}
    >
      <div className="flex items-start justify-between gap-2">
        <div>
          <p className="pa26-card-title">{catalog.displayName}</p>
          <p className="pa26-caption text-pa-muted">{catalog.audience}</p>
        </div>
        {isCurrent ? (
          <span className="shrink-0 rounded-pill bg-sage-500 px-2 py-0.5 pa26-micro font-semibold text-white">
            Сейчас
          </span>
        ) : catalog.isPro ? (
          <span className="shrink-0 rounded-pill border border-sage-300 px-2 py-0.5 pa26-micro font-semibold text-sage-700 dark:border-sage-500 dark:text-sage-200">
            PRO
          </span>
        ) : null}
      </div>
      <p className="pa26-body mt-2 text-pa-muted">{catalog.tagline}</p>
      <p className="pa26-card-title mt-2 tabular-nums">
        {priceLabel(apiPlan.price_rub)}
      </p>
      <ul className="mt-3 space-y-1">
        {catalog.benefits.map((b) => (
          <li key={b} className="pa26-caption text-pa-muted">
            · {b}
          </li>
        ))}
      </ul>
      {!isCurrent ? (
        <Button2026
          size="wide"
          variant={catalog.isPro ? "primary" : "secondary"}
          className="mt-4"
          disabled={selecting}
          onClick={() => onSelect(apiPlan.code)}
        >
          {selecting ? "…" : "Перейти к оплате"}
        </Button2026>
      ) : null}
    </article>
  );
}
