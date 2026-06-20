import { describe, expect, it } from "vitest";

import {
  DAY_SUMMARY_LEGACY_TITLES,
  DAY_SUMMARY_SHEET_SUBTITLE,
  DAY_SUMMARY_SHEET_TITLE,
  formatDaySummaryKcal,
} from "./day-summary-sheet";

describe("day summary sheet copy", () => {
  it("uses Итог дня title", () => {
    expect(DAY_SUMMARY_SHEET_TITLE).toBe("Итог дня");
    expect(DAY_SUMMARY_SHEET_TITLE).not.toBe("Результат дня");
  });

  it("uses nutrition subtitle, not cooking question", () => {
    expect(DAY_SUMMARY_SHEET_SUBTITLE).toBe("План на день и КБЖУ");
    expect(DAY_SUMMARY_SHEET_SUBTITLE).not.toContain("Что приготовили");
  });

  it("does not include legacy confusing strings", () => {
    expect(DAY_SUMMARY_SHEET_TITLE).not.toBe(DAY_SUMMARY_LEGACY_TITLES[0]);
    expect(DAY_SUMMARY_SHEET_SUBTITLE).not.toBe(DAY_SUMMARY_LEGACY_TITLES[1]);
  });

  it("formats kcal with target", () => {
    expect(formatDaySummaryKcal(560, 1680)).toBe("560 / 1680 ккал");
  });
});
