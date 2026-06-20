"use client";

/**
 * PLANAM V2 — segment «Покупки | Запасы» внутри домашнего раздела.
 * Bottom nav не меняем: это переключатель между /shopping и /home/pantry.
 * «Из того, что есть дома» — CTA внутри Запасов, не отдельная вкладка.
 */

import { useRouter } from "next/navigation";

import { PLANAM_ROUTES } from "@/lib/planam/routes";
import { cn } from "@/lib/planam/cn";

const TABS = [
  { id: "shopping" as const, label: "Покупки", href: PLANAM_ROUTES.shopping },
  { id: "pantry" as const, label: "Запасы", href: PLANAM_ROUTES.pantry },
];

export function HomeDomainSegmentV2({
  active,
  className,
}: {
  active: "shopping" | "pantry";
  className?: string;
}) {
  const router = useRouter();
  return (
    <div
      role="tablist"
      aria-label="Покупки и запасы"
      className={cn(
        "flex rounded-pill border border-pa-border bg-pa-surface p-1",
        className,
      )}
    >
      {TABS.map((tab) => (
        <button
          key={tab.id}
          type="button"
          role="tab"
          aria-selected={active === tab.id}
          onClick={() => {
            if (active !== tab.id) {
              router.push(tab.href);
            }
          }}
          className={cn(
            "flex-1 rounded-pill py-2 pa26-caption font-semibold transition",
            active === tab.id
              ? "bg-sage-500 text-white dark:bg-sage-400 dark:text-graphite-900"
              : "text-pa-muted hover:text-pa-foreground",
          )}
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
}
