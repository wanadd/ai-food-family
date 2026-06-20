import { describe, expect, it } from "vitest";

import {
  detectProductCategory,
  formatProductQuantity,
  isSuspiciousUnit,
  normalizeProductName,
} from "./productTaxonomy";

describe("normalizeProductName", () => {
  it("trims and capitalizes", () => {
    expect(normalizeProductName("  капуста  белокочанная ")).toBe(
      "Капуста белокочанная",
    );
    expect(normalizeProductName(null)).toBe("");
  });
});

describe("detectProductCategory", () => {
  it("maps vegetables", () => {
    expect(detectProductCategory("капуста")).toBe("овощи_зелень");
    expect(detectProductCategory("лук репчатый")).toBe("овощи_зелень");
    expect(detectProductCategory("картофель")).toBe("овощи_зелень");
  });

  it("maps meat and fish", () => {
    expect(detectProductCategory("курица")).toBe("мясо_птица");
    expect(detectProductCategory("лосось филе")).toBe("рыба_морепродукты");
  });

  it("maps dairy and grocery", () => {
    expect(detectProductCategory("молоко")).toBe("молочные");
    expect(detectProductCategory("творог")).toBe("молочные");
    expect(detectProductCategory("рис")).toBe("крупы_макароны");
    expect(detectProductCategory("киноа")).toBe("крупы_макароны");
  });

  it("respects canonical backend category", () => {
    expect(detectProductCategory("капуста", "овощи_зелень")).toBe(
      "овощи_зелень",
    );
  });

  it("overrides forbidden/unknown category by name", () => {
    expect(detectProductCategory("капуста", "продукты")).toBe("овощи_зелень");
    expect(detectProductCategory("молоко", "что-то")).toBe("молочные");
  });

  it("falls back to другое", () => {
    expect(detectProductCategory("непонятный товар")).toBe("другое");
  });
});

describe("isSuspiciousUnit", () => {
  it("flags solid products with volume units", () => {
    expect(isSuspiciousUnit("капуста", "л")).toBe(true);
    expect(isSuspiciousUnit("лук", "мл")).toBe(true);
    expect(isSuspiciousUnit("курица", "л")).toBe(true);
    expect(isSuspiciousUnit("сыр", "мл")).toBe(true);
  });

  it("allows liquids with volume units", () => {
    expect(isSuspiciousUnit("молоко", "л")).toBe(false);
    expect(isSuspiciousUnit("сок яблочный", "мл")).toBe(false);
    expect(isSuspiciousUnit("масло оливковое", "л")).toBe(false);
  });

  it("ignores non-volume units", () => {
    expect(isSuspiciousUnit("капуста", "шт")).toBe(false);
    expect(isSuspiciousUnit("курица", "г")).toBe(false);
  });
});

describe("formatProductQuantity (taxonomy guard)", () => {
  it("капуста 1 л → пусто (показываем только имя)", () => {
    expect(
      formatProductQuantity({ name: "капуста", quantity: "1", unit: "л" }),
    ).toBe("");
  });

  it("курица 2 л → пусто", () => {
    expect(
      formatProductQuantity({ name: "курица", quantity: "2", unit: "л" }),
    ).toBe("");
  });

  it("молоко 1 л → 1 л", () => {
    expect(
      formatProductQuantity({ name: "молоко", quantity: "1", unit: "л" }),
    ).toBe("1 л");
  });

  it("рис 500 г → 500 г", () => {
    expect(
      formatProductQuantity({ name: "рис", quantity: "500", unit: "г" }),
    ).toBe("500 г");
  });

  it("1 л + л → 1 л (no duplicate)", () => {
    expect(
      formatProductQuantity({ name: "молоко", quantity: "1 л", unit: "л" }),
    ).toBe("1 л");
  });

  it("undefined г → пусто", () => {
    expect(
      formatProductQuantity({ name: "рис", quantity: "undefined", unit: "г" }),
    ).toBe("");
  });

  it("null шт → пусто", () => {
    expect(
      formatProductQuantity({ name: "яблоко", quantity: null, unit: "шт" }),
    ).toBe("");
  });
});
