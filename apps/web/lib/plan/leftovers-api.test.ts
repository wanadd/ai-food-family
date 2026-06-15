import { describe, expect, it } from "vitest";

import {
  formatPreparedLeftoverAmount,
  formatStocksSummaryLabel,
  mapExistingBatchToSheetDefaults,
  mapNewDishToSheetDefaults,
  previewPreparedRemaining,
  type CookingBatch,
  type StocksOverview,
} from "./leftovers-api";

const sampleBatch: CookingBatch = {
  id: 10,
  family_id: null,
  owner_user_id: 5,
  recipe_id: 260,
  recipe_title: "Суп",
  menu_selection_id: 123,
  day_index: 1,
  planned_date: "2026-06-14",
  meal_type: "lunch",
  batch_status: "active",
  total_servings: 4,
  remaining_servings: 2,
  serving_unit: "порция",
};

describe("leftovers-api helpers", () => {
  it("formats 2 из 4 порций", () => {
    expect(formatPreparedLeftoverAmount(2, 4, "порция")).toBe(
      "осталось 2 из 4 порций",
    );
  });

  it("formats 1,5 из 4 порций", () => {
    expect(formatPreparedLeftoverAmount(1.5, 4, "порция")).toBe(
      "осталось 1,5 из 4 порций",
    );
  });

  it("personal create payload shape", () => {
    const payload = {
      family_id: null,
      recipe_id: 260,
      recipe_title: "Суп",
      menu_selection_id: 123,
      day_index: 1,
      planned_date: "2026-06-14",
      meal_type: "lunch",
      total_servings: 4,
      serving_unit: "порция",
    };
    expect(payload.family_id).toBeNull();
    expect(payload.recipe_id).toBe(260);
  });

  it("use servings payload", () => {
    const payload = { servings_used: 2, note: "После ужина" };
    expect(payload.servings_used).toBe(2);
  });

  it("adjust remaining payload", () => {
    const payload = { remaining_servings: 1.5 };
    expect(payload.remaining_servings).toBe(1.5);
  });

  it("separates products and prepared_dishes", () => {
    const overview: StocksOverview = {
      products: [
        {
          id: 1,
          title: "Рис",
          quantity: "800",
          unit: "г",
          category: "Бакалея",
          source: "inventory",
        },
      ],
      prepared_dishes: [
        {
          id: 10,
          recipe_id: 260,
          recipe_title: "Суп",
          remaining_servings: 2,
          total_servings: 5,
          serving_unit: "порция",
          meal_type: "lunch",
          planned_date: "2026-06-14",
          day_index: 1,
          menu_selection_id: 123,
          batch_status: "active",
          source: "cooking_batch",
          can_manage: true,
        },
      ],
      summary: {
        products_count: 1,
        prepared_dishes_count: 1,
        total_positions_count: 2,
      },
    };
    expect(overview.products).toHaveLength(1);
    expect(overview.prepared_dishes).toHaveLength(1);
    expect(overview.products[0]?.source).toBe("inventory");
    expect(overview.prepared_dishes[0]?.source).toBe("cooking_batch");
  });

  it("summary 47 продуктов · 2 готовых блюда", () => {
    expect(
      formatStocksSummaryLabel({
        products_count: 47,
        prepared_dishes_count: 2,
        total_positions_count: 49,
      }),
    ).toBe("47 продуктов · 2 готовых блюда");
  });

  it("does not reference meal_consumption_logs", () => {
    const overview: StocksOverview = {
      products: [],
      prepared_dishes: [],
      summary: {
        products_count: 0,
        prepared_dishes_count: 0,
        total_positions_count: 0,
      },
    };
    expect(JSON.stringify(overview)).not.toContain("meal_consumption");
  });

  it("read-only prepared dish has can_manage false", () => {
    const dish = {
      id: 1,
      recipe_id: 1,
      recipe_title: "Суп",
      remaining_servings: 2,
      total_servings: 4,
      serving_unit: "порция",
      meal_type: "lunch",
      planned_date: null,
      day_index: null,
      menu_selection_id: null,
      batch_status: "active",
      source: "cooking_batch" as const,
      can_manage: false,
    };
    expect(dish.can_manage).toBe(false);
  });

  it("existing prepared batch maps into sheet defaults", () => {
    const mapped = mapExistingBatchToSheetDefaults(sampleBatch);
    expect(mapped.batch?.id).toBe(10);
    expect(mapped.totalServings).toBe(4);
    expect(mapped.servingUnit).toBe("порция");
  });

  it("2 из 4 порций restores after reopen via batch remaining", () => {
    const mapped = mapExistingBatchToSheetDefaults(sampleBatch);
    expect(
      formatPreparedLeftoverAmount(
        sampleBatch.remaining_servings,
        mapped.totalServings,
        mapped.servingUnit,
      ),
    ).toBe("осталось 2 из 4 порций");
  });

  it("preview remaining subtracts additional usage from existing batch", () => {
    expect(previewPreparedRemaining(sampleBatch, 4, 1, "")).toBe(1);
    expect(previewPreparedRemaining(sampleBatch, 4, null, "")).toBe(2);
  });

  it("save with existing batch should use batch id not create duplicate", () => {
    const mapped = mapExistingBatchToSheetDefaults(sampleBatch);
    expect(mapped.batch?.id).toBe(10);
    const again = mapExistingBatchToSheetDefaults(sampleBatch);
    expect(again.batch?.id).toBe(10);
  });

  it("empty state uses recipe servings or 1", () => {
    expect(mapNewDishToSheetDefaults(4).totalServings).toBe(4);
    expect(mapNewDishToSheetDefaults(null).totalServings).toBe(1);
    expect(mapNewDishToSheetDefaults(undefined).totalServings).toBe(1);
  });

  it("family read-only batch still maps for display", () => {
    const familyBatch: CookingBatch = {
      ...sampleBatch,
      id: 20,
      family_id: 1,
      owner_user_id: null,
    };
    const mapped = mapExistingBatchToSheetDefaults(familyBatch);
    expect(mapped.totalServings).toBe(4);
    expect(mapped.batch?.remaining_servings).toBe(2);
  });
});
