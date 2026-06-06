import { describe, expect, it } from "vitest";

import { FORBIDDEN_CATEGORY_SLUG } from "@/lib/shopping/categories-v1";
import {
  normalizeCategorySlug,
  suggestCategorySlug,
} from "@/lib/shopping/category-suggest";

describe("category-suggest V1", () => {
  it("classifies eggs correctly", () => {
    expect(suggestCategorySlug("Яйцо")).toBe("яйца");
    expect(suggestCategorySlug("Яйца куриные")).toBe("яйца");
  });

  it("classifies berries and grains", () => {
    expect(suggestCategorySlug("Малина")).toBe("фрукты_ягоды");
    expect(suggestCategorySlug("Пшено")).toBe("крупы_макароны");
    expect(suggestCategorySlug("Бульон куриный")).toBe("бакалея");
    expect(suggestCategorySlug("Орехи грецкие")).toBe("бакалея");
  });

  it("distinguishes pepper spice from vegetable", () => {
    expect(suggestCategorySlug("Перец болгарский")).toBe("овощи_зелень");
    expect(suggestCategorySlug("Перец чёрный молотый")).toBe("специи_соусы");
  });

  it("never returns forbidden продукты slug", () => {
    expect(suggestCategorySlug("")).toBe("другое");
    expect(suggestCategorySlug("Неизвестный товар")).toBe("другое");
    expect(suggestCategorySlug("Яйцо")).not.toBe(FORBIDDEN_CATEGORY_SLUG);
  });

  it("normalizes legacy продукты via item name", () => {
    expect(normalizeCategorySlug("продукты", "Яйцо")).toBe("яйца");
    expect(normalizeCategorySlug("продукты", "Малина")).toBe("фрукты_ягоды");
    expect(normalizeCategorySlug("овощи", "Огурцы")).toBe("овощи_зелень");
  });
});
