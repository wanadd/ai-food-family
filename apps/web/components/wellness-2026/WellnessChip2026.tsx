"use client";

import { useRouter } from "next/navigation";

import { Skeleton2026 } from "@/components/planam-2026/ui/Skeleton2026";
import type { HomeWellnessChip } from "@/lib/wellness/home-wellness";
import { cn } from "@/lib/planam/cn";

type WellnessChip2026Props = {
  data: HomeWellnessChip | null;
  loading?: boolean;
};

export function WellnessChip2026({ data, loading = false }: WellnessChip2026Props) {
  const router = useRouter();

  if (loading) {
    return (
      <section className="px-4 pt-4" aria-busy="true">
        <Skeleton2026 variant="rect" className="h-[72px] w-full" />
      </section>
    );
  }

  if (!data) {
    return null;
  }

  const waterPct = data.waterPercent ?? 0;

  return (
    <section className="px-4 pt-4" aria-label="Забота">
      <button
        type="button"
        onClick={() => router.push("/wellness")}
        className="flex w-full items-center gap-3 rounded-card border border-pa-border bg-pa-surface p-3 text-left shadow-soft transition active:scale-[0.98] dark:shadow-none"
      >
        <div
          className="relative flex h-12 w-12 shrink-0 items-center justify-center rounded-full"
          style={{
            background: `conic-gradient(#6b8f71 ${waterPct}%, #e8e4dc ${waterPct}%)`,
          }}
          aria-hidden
        >
          <span className="flex h-9 w-9 items-center justify-center rounded-full bg-pa-surface pa26-micro font-bold tabular-nums">
            {waterPct > 0 ? waterPct : data.dayPercent}
          </span>
        </div>
        <div className="min-w-0 flex-1">
          <p className="pa26-micro font-semibold text-sage-700 dark:text-sage-300">
            Забота · {data.goalLabel}
          </p>
          {data.insight ? (
            <p className="pa26-caption mt-0.5 line-clamp-2 text-graphite-800 dark:text-cream-100">
              {data.insight}
            </p>
          ) : (
            <p className="pa26-caption mt-0.5 text-pa-muted">
              Как у вас дела сегодня?
            </p>
          )}
        </div>
        {data.goalProgressPercent != null ? (
          <span
            className={cn(
              "shrink-0 rounded-pill bg-sage-100 px-2 py-0.5 pa26-micro font-semibold tabular-nums text-sage-800",
              "dark:bg-sage-700/40 dark:text-sage-200",
            )}
          >
            {data.goalProgressPercent}%
          </span>
        ) : null}
      </button>
    </section>
  );
}
