import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

import type { CookingBatch } from "./leftovers-api";
import {
  buildDefaultLeftoversDraft,
  hasTouchedLeftoversDrafts,
  mapBatchesByMealKey,
  previewLeftoversDisplayRemaining,
  resolveLeftoversRemainingTarget,
  shouldShowLeftoversSection,
} from "./meal-leftovers-unified";

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

describe("meal-leftovers-unified", () => {
  it("shows leftovers section for eaten meal with recipe", () => {
    expect(
      shouldShowLeftoversSection({
        recipeId: 260,
        included: true,
        status: "eaten",
        existingBatch: null,
      }),
    ).toBe(true);
  });

  it("hides leftovers section for skipped meal without batch", () => {
    expect(
      shouldShowLeftoversSection({
        recipeId: 260,
        included: true,
        status: "skipped",
        existingBatch: null,
      }),
    ).toBe(false);
  });

  it("shows leftovers section when active batch exists", () => {
    expect(
      shouldShowLeftoversSection({
        recipeId: 260,
        included: true,
        status: "skipped",
        existingBatch: sampleBatch,
      }),
    ).toBe(true);
  });

  it("maps existing batch into sheet defaults", () => {
    const draft = buildDefaultLeftoversDraft(sampleBatch, 4);
    expect(draft.totalServings).toBe(4);
    expect(draft.remainingTarget).toBe(2);
    expect(draft.touched).toBe(false);
  });

  it("restores 2 из 4 after reopen via preview", () => {
    const draft = buildDefaultLeftoversDraft(sampleBatch, 4);
    expect(previewLeftoversDisplayRemaining(draft, sampleBatch)).toBe(2);
  });

  it("detects touched leftovers drafts", () => {
    const draft = buildDefaultLeftoversDraft(sampleBatch, 4);
    expect(hasTouchedLeftoversDrafts({ lunch: draft })).toBe(false);
    expect(
      hasTouchedLeftoversDrafts({
        lunch: { ...draft, touched: true, remainingTarget: 1 },
      }),
    ).toBe(true);
  });

  it("maps batches by meal key", () => {
    const mapped = mapBatchesByMealKey(
      [sampleBatch],
      [{ key: "lunch-0", meal_type: "lunch", recipe_id: 260 }],
      123,
      1,
      "2026-06-14",
    );
    expect(mapped["lunch-0"]?.id).toBe(10);
  });

  it("resolves finish action to remaining 0", () => {
    const draft = {
      ...buildDefaultLeftoversDraft(sampleBatch, 4),
      touched: true,
      quickAction: "finish" as const,
    };
    expect(resolveLeftoversRemainingTarget(draft)).toBe(0);
    expect(previewLeftoversDisplayRemaining(draft, sampleBatch)).toBe(0);
  });

  it("MenuToday has no separate Остатки action", () => {
    const source = readFileSync(
      join(process.cwd(), "components/planam-v2/menu/MenuTodayV2.tsx"),
      "utf8",
    );
    expect(source).not.toContain('label="Остатки"');
    expect(source).not.toContain("PreparedLeftoversSheetV2");
  });
});
