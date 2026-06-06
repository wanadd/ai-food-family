import { cn } from "@/lib/planam/cn";
import type { WellnessDayProgress } from "@/lib/wellness/wellness-status";

type WellnessDayRing2026Props = {
  progress: WellnessDayProgress;
  caloriesLabel?: string;
};

export function WellnessDayRing2026({
  progress,
  caloriesLabel,
}: WellnessDayRing2026Props) {
  const { percent, label } = progress;
  const ringStyle = {
    background: `conic-gradient(var(--pa-brand-primary) ${percent}%, var(--pa-border) ${percent}%)`,
  };

  return (
    <section className="flex items-center gap-3 rounded-card border border-pa-border bg-pa-elevated p-3">
      <div
        className="relative flex h-[72px] w-[72px] shrink-0 items-center justify-center rounded-full p-1"
        style={ringStyle}
        aria-label={`Прогресс дня ${percent}%`}
      >
        <div className="flex h-full w-full flex-col items-center justify-center rounded-full bg-pa-surface">
          <span className="pa26-card-title tabular-nums">{percent}%</span>
          <span className="pa26-micro text-pa-muted">день</span>
        </div>
      </div>
      <div className="min-w-0">
        <p className="pa26-caption text-pa-muted">Статус</p>
        <p className={cn("pa26-card-title mt-0.5")}>{label}</p>
        {caloriesLabel ? (
          <p className="pa26-caption mt-0.5 text-pa-muted">Калории: {caloriesLabel}</p>
        ) : null}
      </div>
    </section>
  );
}
