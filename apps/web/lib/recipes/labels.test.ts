import { describe, expect, it } from "vitest";

import {
  categoryLabel,
  hasCategoryLabel,
  hasMealLabel,
  mealLabel,
} from "./labels";

describe("recipe labels", () => {
  it("maps category side to Гарнир", () => {
    expect(categoryLabel("side")).toBe("Гарнир");
    expect(categoryLabel("side")).not.toBe("side");
  });

  it("does not expose raw slug for unknown category", () => {
    expect(categoryLabel("unknown_slug")).toBe("");
    expect(hasCategoryLabel("unknown_slug")).toBe(false);
  });

  it("does not expose raw meal_type slug", () => {
    expect(mealLabel("dinner")).toBe("Ужин");
    expect(mealLabel("lunch")).toBe("Обед");
    expect(mealLabel("side")).toBe("");
    expect(mealLabel("main")).toBe("");
  });

  it("hides unknown meal labels", () => {
    expect(hasMealLabel("breakfast")).toBe(true);
    expect(hasMealLabel("foo_bar")).toBe(false);
  });
});
