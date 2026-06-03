import type { PlanSnapshotItem } from "@/lib/home/home-2026-data";
import { cn } from "@/lib/planam/cn";

type PlanSnapshot2026Props = {
  items: PlanSnapshotItem[];
  loading?: boolean;
};

export function PlanSnapshot2026({ items, loading = false }: PlanSnapshot2026Props) {
  if (loading) {
    return (
      <section className="px-4 pt-4" aria-busy="true">
        <div className="flex gap-2">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="h-10 min-w-[96px] flex-1 rounded-card border border-pa-border bg-pa-surface px-3 py-2"
            >
              <div className="h-3 w-16 animate-pulse rounded-pill bg-cream-deep dark:bg-graphite-700/40" />
            </div>
          ))}
        </div>
      </section>
    );
  }

  if (items.length === 0) {
    return null;
  }

  return (
    <section className="px-4 pt-4" aria-label="Сводка плана">
      <div className="flex flex-wrap gap-2">
        {items.map((item) => (
          <div
            key={item.id}
            className={cn(
              "min-w-[96px] flex-1 rounded-card border border-pa-border bg-pa-surface px-3 py-2.5 shadow-soft dark:shadow-none",
            )}
          >
            <span className="pa26-body whitespace-nowrap">
              <span className="mr-1" aria-hidden>
                {item.emoji}
              </span>
              {item.label}
            </span>
          </div>
        ))}
      </div>
    </section>
  );
}
