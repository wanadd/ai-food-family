import { cn } from "@/lib/planam/cn";

export type MetricCard2026Props = {
  label: string;
  value: string;
  progress?: number;
  locked?: boolean;
  className?: string;
};

export function MetricCard2026({
  label,
  value,
  progress,
  locked = false,
  className,
}: MetricCard2026Props) {
  const pct = progress !== undefined ? Math.min(100, Math.max(0, progress)) : undefined;

  return (
    <div
      className={cn(
        "relative min-w-[96px] rounded-card border border-pa-border bg-pa-surface p-3 shadow-soft dark:shadow-none",
        className,
      )}
    >
      <p className="pa26-caption">{label}</p>
      <p className="pa26-card-title mt-1 tabular-nums">{value}</p>
      {pct !== undefined ? (
        <div className="mt-2 h-1.5 overflow-hidden rounded-pill bg-cream-deep dark:bg-graphite-700/40">
          <div
            className="h-full rounded-pill bg-sage-500 dark:bg-sage-400"
            style={{ width: `${pct}%` }}
          />
        </div>
      ) : null}
      {locked ? (
        <div className="absolute inset-0 flex items-center justify-center rounded-card bg-pa-surface/80 backdrop-blur-[2px]">
          <span className="pa26-micro font-semibold text-pa-muted">В PRO</span>
        </div>
      ) : null}
    </div>
  );
}
