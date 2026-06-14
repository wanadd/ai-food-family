export const DAY_SUMMARY_SHEET_TITLE = "Итог дня";
export const DAY_SUMMARY_SHEET_SUBTITLE = "План на день и КБЖУ";

/** Legacy copy that must not appear in the day summary sheet. */
export const DAY_SUMMARY_LEGACY_TITLES = ["Результат дня", "Что приготовили?"] as const;

export function formatDaySummaryKcal(
  kcal: number,
  target: number | null,
  approximate = false,
): string {
  const prefix = approximate ? "≈" : "";
  if (target != null && target > 0) {
    return `${prefix}${Math.round(kcal)} / ${Math.round(target)} ккал`;
  }
  return `${prefix}${Math.round(kcal)} ккал`;
}
