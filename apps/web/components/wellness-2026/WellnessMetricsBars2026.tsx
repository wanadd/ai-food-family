import type { WellnessTodayMetrics } from "@/lib/wellness/wellness-status";
import { cn } from "@/lib/planam/cn";

type WellnessMetricsBars2026Props = {
  metrics: WellnessTodayMetrics;
};

function parseProgress(label: string): { current: number; target: number } | null {
  const match = label.match(/([\d.,]+)\s*\/\s*([\d.,]+)/);
  if (!match) {
    return null;
  }
  const current = Number.parseFloat(match[1].replace(",", "."));
  const target = Number.parseFloat(match[2].replace(",", "."));
  if (!Number.isFinite(current) || !Number.isFinite(target) || target <= 0) {
    return null;
  }
  return { current, target };
}

function MetricBar({ label, value }: { label: string; value: string }) {
  const parsed = parseProgress(value);
  const pct = parsed
    ? Math.min(100, Math.round((parsed.current / parsed.target) * 100))
    : null;

  return (
    <div>
      <div className="flex items-baseline justify-between gap-2">
        <span className="pa26-micro font-medium text-pa-foreground">{label}</span>
        <span className="pa26-micro tabular-nums text-pa-muted">{value}</span>
      </div>
      <div className="mt-1.5 h-2 overflow-hidden rounded-pill bg-pa-border/60">
        <div
          className={cn(
            "h-full rounded-pill bg-sage-500 transition-all dark:bg-sage-400",
            pct == null && "w-0",
          )}
          style={pct != null ? { width: `${pct}%` } : undefined}
        />
      </div>
    </div>
  );
}

export function WellnessMetricsBars2026({ metrics }: WellnessMetricsBars2026Props) {
  const rows = [
    { label: "Калории", value: metrics.eatenLabel },
    { label: "Вода", value: metrics.waterLabel },
    { label: "Активность", value: metrics.activityLabel },
  ];

  return (
    <section className="rounded-card border border-pa-border bg-pa-surface p-4 shadow-soft dark:shadow-none">
      <h2 className="pa26-section-title">Сегодня</h2>
      <div className="mt-3 space-y-3">
        {rows.map((row) => (
          <MetricBar key={row.label} label={row.label} value={row.value} />
        ))}
      </div>
    </section>
  );
}
