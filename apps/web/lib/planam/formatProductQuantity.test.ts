import { describe, expect, it } from "vitest";

import { formatProductQuantity } from "./formatProductQuantity";

describe("formatProductQuantity", () => {
  it("prefers amount when present", () => {
    expect(
      formatProductQuantity({ amount: "500 г", quantity: "1", unit: "л" }),
    ).toBe("500 г");
  });

  it("does not duplicate unit in quantity", () => {
    expect(formatProductQuantity({ quantity: "1 л", unit: "л" })).toBe("1 л");
    expect(formatProductQuantity({ quantity: "500 г", unit: "г" })).toBe("500 г");
  });

  it("joins quantity and unit when separate", () => {
    expect(formatProductQuantity({ quantity: "1", unit: "л" })).toBe("1 л");
    expect(formatProductQuantity({ quantity: "1", unit: "шт" })).toBe("1 шт");
  });

  it("hides invalid values", () => {
    expect(formatProductQuantity({ quantity: null, unit: "г" })).toBe("");
    expect(formatProductQuantity({ quantity: "undefined", unit: "г" })).toBe("");
    expect(formatProductQuantity({ quantity: "NaN", unit: "шт" })).toBe("");
  });
});
