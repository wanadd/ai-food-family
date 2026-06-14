import { describe, expect, it } from "vitest";

import { pluralRu, pluralRuWithCount } from "./plural-ru";

describe("pluralRu", () => {
  const dish = (n: number) => pluralRu(n, "блюдо", "блюда", "блюд");

  it("handles 1, 21", () => {
    expect(dish(1)).toBe("блюдо");
    expect(dish(21)).toBe("блюдо");
  });

  it("handles 2–4, 22–24", () => {
    expect(dish(2)).toBe("блюда");
    expect(dish(3)).toBe("блюда");
    expect(dish(4)).toBe("блюда");
    expect(dish(22)).toBe("блюда");
    expect(dish(24)).toBe("блюда");
  });

  it("handles 0, 5–20, 25", () => {
    expect(dish(0)).toBe("блюд");
    expect(dish(5)).toBe("блюд");
    expect(dish(11)).toBe("блюд");
    expect(dish(12)).toBe("блюд");
    expect(dish(25)).toBe("блюд");
  });

  it("formats with count", () => {
    expect(pluralRuWithCount(2, "блюдо", "блюда", "блюд")).toBe("2 блюда");
  });
});
