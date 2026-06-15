import { describe, expect, it } from "vitest";

import { formatPlannedYieldLine, formatPreparedAmount } from "./yield-format";

describe("yield-format", () => {
  it("formats soup 2 л из 5 л", () => {
    expect(
      formatPreparedAmount({
        remaining: 6,
        total: 14,
        unit: "порция",
        remainingAmount: { value: 2, unit: "л" },
        totalAmount: { value: 5, unit: "л" },
      }),
    ).toBe("осталось 2 из 5 л");
  });

  it("formats count 4 из 12 шт", () => {
    expect(
      formatPreparedAmount({
        remaining: 2,
        total: 6,
        unit: "порция",
        remainingAmount: { value: 4, unit: "шт" },
        totalAmount: { value: 12, unit: "шт" },
      }),
    ).toBe("осталось 4 из 12 шт");
  });

  it("formats planned yield line", () => {
    expect(
      formatPlannedYieldLine({
        planned_yield_amount: 5,
        planned_yield_unit: "л",
        planned_serving_size_amount: 350,
        planned_serving_size_unit: "мл",
        expected_leftover_amount: 2,
        expected_leftover_unit: "л",
      }),
    ).toContain("Готовить: 5 л");
    expect(
      formatPlannedYieldLine({
        planned_yield_amount: 5,
        planned_yield_unit: "л",
        planned_serving_size_amount: 350,
        planned_serving_size_unit: "мл",
        expected_leftover_amount: 2,
        expected_leftover_unit: "л",
      }),
    ).toContain("останется ~2 л");
  });
});
