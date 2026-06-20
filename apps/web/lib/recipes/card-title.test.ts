import { describe, expect, it } from "vitest";

import { recipeCardHeading, recipeDetailHeading } from "./card-title";

describe("recipe card titles", () => {
  it("uses display_title on cards", () => {
    expect(
      recipeCardHeading({
        title: "Салат с курицей, яблоком и свежими овощами",
        display_title: "Салат с курицей и яблоком",
      }),
    ).toBe("Салат с курицей и яблоком");
  });

  it("uses display_title on detail screen", () => {
    expect(
      recipeDetailHeading({
        title: "Салат с курицей, яблоком и свежими овощами",
        display_title: "Салат с курицей и яблоком",
      }),
    ).toBe("Салат с курицей и яблоком");
  });
});
