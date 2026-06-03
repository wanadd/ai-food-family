import { cn } from "@/lib/planam/cn";
import type { WellnessDayProgress } from "@/lib/wellness/wellness-status";

type WellnessDayRing2026Props = {
  progress: WellnessDayProgress;
};

export function WellnessDayRing2026({ progress }: WellnessDayRing2026Props) {
  const { percent, label } = progress;
  const ringStyle = {
    background: `conic-gradient(var(--tw-gradient-from, #6b8f71) ${percent}%, var(--tw-gradient-to, #e8e4dc) ${percent}%)`,
  };

  return (
    <section className="flex items-center gap-4 rounded-card border border-pa-border bg-gradient-to-br from-sage-50/80 to-pa-surface p-4 dark:from-sage-900/20 dark:to-pa-surface">
      <div
        className="relative flex h-[88px] w-[88px] shrink-0 items-center justify-center rounded-full p-1"
        style={ringStyle}
        aria-label={`Прогресс дня ${percent}%`}
      >
        <div className="flex h-full w-full flex-col items-center justify-center rounded-full bg-pa-surface">
          <span className="pa26-card-title tabular-nums">{percent}%</span>
          <span className="pa26-micro text-pa-muted">день</span>
        </div>
      </div>
      <div className="min-w-0">
        <p className="pa26-caption text-pa-muted">Как у вас дела?</p>
        <p className={cn("pa26-card-title mt-0.5")}>{label}</p>
        <p className="pa26-caption mt-1 text-pa-muted">
          Питание, вода и отметки без лишней аналитики
        </p>
      </div>
    </section>
  );
}
