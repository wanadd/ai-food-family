import { describe, expect, it } from "vitest";

import {
  DEFAULT_MENU_DURATION_DAYS,
  MENU_DURATION_OPTIONS,
  formatMenuDuration,
  isMenuDurationDays,
  menuDurationChipLabel,
  normalizeMenuDurationDays,
} from "./duration-options";

describe("menu duration options", () => {
  it("allows only first-run menu durations", () => {
    expect(MENU_DURATION_OPTIONS).toEqual([1, 3, 5, 7]);
    expect(isMenuDurationDays(1)).toBe(true);
    expect(isMenuDurationDays(3)).toBe(true);
    expect(isMenuDurationDays(5)).toBe(true);
    expect(isMenuDurationDays(7)).toBe(true);
    expect(isMenuDurationDays(2)).toBe(false);
    expect(isMenuDurationDays(30)).toBe(false);
  });

  it("falls back to recommended seven days for invalid values", () => {
    expect(DEFAULT_MENU_DURATION_DAYS).toBe(7);
    expect(normalizeMenuDurationDays(undefined)).toBe(7);
    expect(normalizeMenuDurationDays(0)).toBe(7);
    expect(normalizeMenuDurationDays(9)).toBe(7);
  });

  it("formats selected duration for copy", () => {
    expect(formatMenuDuration(1)).toBe("1 день");
    expect(formatMenuDuration(3)).toBe("3 дня");
    expect(formatMenuDuration(5)).toBe("5 дней");
    expect(formatMenuDuration(7)).toBe("7 дней");
    expect(menuDurationChipLabel(7)).toContain("рекомендуем");
  });
});
