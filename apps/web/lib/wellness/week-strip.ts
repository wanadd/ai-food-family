import type { ProgressEntry } from "@/lib/progress/types";
import type { ProgressOverview } from "@/lib/progress/types";

export type WeekStripDay = {
  dateIso: string;
  label: string;
  level: "none" | "low" | "good";
};

function isoDate(d: Date): string {
  return d.toISOString().slice(0, 10);
}

function shortLabel(d: Date): string {
  return d.toLocaleDateString("ru-RU", { weekday: "short" }).replace(".", "");
}

export function buildWeekStrip(
  history: ProgressEntry[],
  progress: ProgressOverview | null,
  todayProgressPercent: number,
): WeekStripDay[] {
  const historyDates = new Set(
    history.map((e) => e.recorded_at.slice(0, 10)),
  );
  const todayIso = isoDate(new Date());
  const days: WeekStripDay[] = [];

  for (let i = 6; i >= 0; i--) {
    const d = new Date();
    d.setDate(d.getDate() - i);
    const dateIso = isoDate(d);
    let level: WeekStripDay["level"] = "none";

    if (dateIso === todayIso) {
      if (todayProgressPercent >= 60) {
        level = "good";
      } else if (todayProgressPercent > 0) {
        level = "low";
      } else if ((progress?.daily_actual?.meals_logged ?? 0) > 0) {
        level = "low";
      }
    } else if (historyDates.has(dateIso)) {
      level = "good";
    } else if (i <= 2) {
      level = "none";
    }

    days.push({
      dateIso,
      label: shortLabel(d),
      level,
    });
  }

  return days;
}
