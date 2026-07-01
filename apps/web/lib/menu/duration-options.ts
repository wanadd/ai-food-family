export const MENU_DURATION_OPTIONS = [1, 3, 5, 7] as const;
export type MenuDurationDays = (typeof MENU_DURATION_OPTIONS)[number];

export const DEFAULT_MENU_DURATION_DAYS: MenuDurationDays = 7;

export function isMenuDurationDays(value: number): value is MenuDurationDays {
  return MENU_DURATION_OPTIONS.includes(value as MenuDurationDays);
}

export function normalizeMenuDurationDays(value: number | null | undefined): MenuDurationDays {
  return typeof value === "number" && isMenuDurationDays(value)
    ? value
    : DEFAULT_MENU_DURATION_DAYS;
}

export function formatMenuDuration(days: number): string {
  const safe = normalizeMenuDurationDays(days);
  if (safe === 1) return "1 день";
  if (safe === 5 || safe === 7) return `${safe} дней`;
  return `${safe} дня`;
}

export function menuDurationChipLabel(days: MenuDurationDays): string {
  return days === DEFAULT_MENU_DURATION_DAYS
    ? `${formatMenuDuration(days)} · рекомендуем`
    : formatMenuDuration(days);
}
