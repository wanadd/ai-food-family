"use client";

import type { MenuOverview } from "@/lib/menu/overview-types";

type PlanAmTip2026Props = {
  overview: MenuOverview | null;
  loading?: boolean;
};

export function PlanAmTip2026({ overview, loading = false }: PlanAmTip2026Props) {
  if (loading) {
    return (
      <section className="px-4 pt-2" aria-busy="true">
        <div className="h-16 animate-pulse rounded-card border border-pa-border bg-pa-surface" />
      </section>
    );
  }

  const advice = overview?.nutritionist_advice;
  const body = advice?.body?.trim();
  const title = advice?.title?.trim() || "Совет PLANAM";

  if (!body) {
    return null;
  }

  return (
    <section className="px-4 pt-2" aria-label="Совет PLANAM">
      <div className="rounded-card border border-sage-200/80 bg-sage-50/60 px-3 py-3 dark:border-sage-700/40 dark:bg-sage-900/20">
        <p className="pa26-micro font-semibold text-sage-800 dark:text-sage-300">
          {title}
        </p>
        <p className="pa26-caption mt-1 line-clamp-3 text-pa-foreground">{body}</p>
      </div>
    </section>
  );
}
