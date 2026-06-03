import { cn } from "@/lib/planam/cn";
import type { WeekStripDay } from "@/lib/wellness/week-strip";

type WellnessWeekStrip2026Props = {
  days: WeekStripDay[];
};

const levelClass: Record<WeekStripDay["level"], string> = {
  none: "bg-cream-deep dark:bg-graphite-700/50",
  low: "bg-sage-200 dark:bg-sage-700/50",
  good: "bg-sage-500 dark:bg-sage-400",
};

export function WellnessWeekStrip2026({ days }: WellnessWeekStrip2026Props) {
  return (
    <section className="rounded-card border border-pa-border bg-pa-surface p-4 shadow-soft dark:shadow-none">
      <h2 className="pa26-section-title">Неделя</h2>
      <p className="pa26-caption mt-1 text-pa-muted">
        Отметки веса и активность дня — без графиков
      </p>
      <div className="mt-4 flex items-end justify-between gap-1">
        {days.map((day) => (
          <div
            key={day.dateIso}
            className="flex min-w-0 flex-1 flex-col items-center gap-1"
          >
            <div
              className={cn(
                "h-10 w-full max-w-[28px] rounded-t-md transition-colors",
                levelClass[day.level],
              )}
              title={day.dateIso}
            />
            <span className="pa26-micro capitalize text-pa-muted">
              {day.label}
            </span>
          </div>
        ))}
      </div>
    </section>
  );
}
