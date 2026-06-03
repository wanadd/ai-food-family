import type { WellnessTodayMetrics } from "@/lib/wellness/wellness-status";

type WellnessTodayCard2026Props = {
  metrics: WellnessTodayMetrics;
};

export function WellnessTodayCard2026({ metrics }: WellnessTodayCard2026Props) {
  const rows = [
    { label: "Съедено", value: metrics.eatenLabel },
    { label: "Осталось", value: metrics.remainingLabel },
    { label: "Вода", value: metrics.waterLabel },
    { label: "Активность", value: metrics.activityLabel },
  ];

  return (
    <section className="rounded-card border border-pa-border bg-pa-surface p-4 shadow-soft dark:shadow-none">
      <h2 className="pa26-section-title">Сегодня</h2>
      <dl className="mt-3 grid grid-cols-2 gap-3">
        {rows.map((row) => (
          <div key={row.label} className="min-w-0">
            <dt className="pa26-micro text-pa-muted">{row.label}</dt>
            <dd className="pa26-card-title mt-0.5 tabular-nums">{row.value}</dd>
          </div>
        ))}
      </dl>
    </section>
  );
}
