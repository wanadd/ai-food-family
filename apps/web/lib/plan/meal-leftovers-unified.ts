import type { MealConsumptionStatus } from "@/lib/plan/meal-consumption-sheet";
import type { CookingBatch } from "@/lib/plan/leftovers-api";
import {
  adjustCookingBatchRemaining,
  createCookingBatch,
  discardCookingBatch,
  finishCookingBatch,
} from "@/lib/plan/leftovers-api";
import type { AppMode } from "@/lib/app-mode/types";

export type LeftoversDraft = {
  touched: boolean;
  totalServings: number;
  servingUnit: string;
  yieldType: string;
  totalAmountValue: number | null;
  totalAmountUnit: string | null;
  remainingAmountValue: number | null;
  remainingAmountUnit: string | null;
  servingSizeValue: number | null;
  servingSizeUnit: string | null;
  remainingTarget: number | null;
  quickAction: "finish" | "discard" | null;
  customRemaining: string;
};

export type MealLeftoversContext = {
  familyId: number | null;
  menuSelectionId: number | null;
  dayIndex: number;
  plannedDate: string | null;
  recipeId: number | null;
  recipeTitle: string;
  mealType: string;
  recipeServings?: number | null;
};

export function buildDefaultLeftoversDraft(
  batch: CookingBatch | null,
  recipeServings?: number | null,
): LeftoversDraft {
  if (batch) {
    return {
      touched: false,
      totalServings: batch.total_servings,
      servingUnit: batch.serving_unit || "порция",
      yieldType: batch.yield_type || "servings",
      totalAmountValue: batch.total_amount_value ?? null,
      totalAmountUnit: batch.total_amount_unit ?? null,
      remainingAmountValue: batch.remaining_amount_value ?? null,
      remainingAmountUnit: batch.remaining_amount_unit ?? null,
      servingSizeValue: batch.serving_size_value ?? null,
      servingSizeUnit: batch.serving_size_unit ?? null,
      remainingTarget: batch.remaining_servings,
      quickAction: null,
      customRemaining: "",
    };
  }
  const total =
    recipeServings != null && recipeServings > 0 ? recipeServings : 1;
  return {
    touched: false,
    totalServings: total,
    servingUnit: "порция",
    yieldType: "servings",
    totalAmountValue: null,
    totalAmountUnit: null,
    remainingAmountValue: null,
    remainingAmountUnit: null,
    servingSizeValue: null,
    servingSizeUnit: null,
    remainingTarget: null,
    quickAction: null,
    customRemaining: "",
  };
}

export function shouldShowLeftoversSection(params: {
  recipeId: number | null;
  included: boolean;
  status: MealConsumptionStatus;
  existingBatch: CookingBatch | null;
  leftoversExpanded?: boolean;
}): boolean {
  if (!params.recipeId || !params.included) {
    return false;
  }
  if (params.existingBatch || params.leftoversExpanded) {
    return true;
  }
  return params.status === "eaten";
}

export function hasTouchedLeftoversDrafts(
  drafts: Record<string, LeftoversDraft>,
): boolean {
  return Object.values(drafts).some((draft) => draft.touched);
}

export function mapBatchesByMealKey(
  batches: CookingBatch[],
  meals: Array<{
    key: string;
    meal_type: string;
    recipe_id: number | null;
  }>,
  menuSelectionId: number | null,
  dayIndex: number,
  plannedDate: string | null,
): Record<string, CookingBatch | null> {
  const result: Record<string, CookingBatch | null> = {};
  for (const meal of meals) {
    result[meal.key] =
      batches.find(
        (batch) =>
          batch.recipe_id === meal.recipe_id &&
          batch.meal_type === meal.meal_type &&
          (menuSelectionId == null ||
            batch.menu_selection_id === menuSelectionId) &&
          batch.day_index === dayIndex &&
          (!plannedDate || batch.planned_date === plannedDate),
      ) ?? null;
  }
  return result;
}

export function resolveLeftoversRemainingTarget(
  draft: LeftoversDraft,
): number | null {
  if (draft.quickAction === "finish" || draft.quickAction === "discard") {
    return 0;
  }
  if (draft.remainingTarget != null) {
    return draft.remainingTarget;
  }
  if (draft.customRemaining.trim()) {
    const parsed = Number(draft.customRemaining.replace(",", "."));
    return Number.isFinite(parsed) ? parsed : null;
  }
  return null;
}

export function previewLeftoversDisplayRemaining(
  draft: LeftoversDraft,
  batch: CookingBatch | null,
): number {
  if (draft.quickAction === "finish" || draft.quickAction === "discard") {
    return 0;
  }
  const target = resolveLeftoversRemainingTarget(draft);
  if (target != null) {
    return Math.max(0, target);
  }
  return batch?.remaining_servings ?? draft.totalServings;
}

export async function persistLeftoversDraft(
  initData: string,
  mode: AppMode,
  ctx: MealLeftoversContext,
  draft: LeftoversDraft,
  existingBatch: CookingBatch | null,
): Promise<CookingBatch | null> {
  if (!draft.touched || ctx.recipeId == null) {
    return existingBatch;
  }

  let batch = existingBatch;
  if (!batch) {
    batch = await createCookingBatch(initData, mode, {
      family_id: ctx.familyId,
      recipe_id: ctx.recipeId,
      recipe_title: ctx.recipeTitle,
      menu_selection_id: ctx.menuSelectionId,
      day_index: ctx.dayIndex,
      planned_date: ctx.plannedDate,
      meal_type: ctx.mealType,
      total_servings: draft.totalServings,
      serving_unit: draft.servingUnit,
      total_amount_value: draft.totalAmountValue,
      total_amount_unit: draft.totalAmountUnit,
      remaining_amount_value:
        draft.remainingAmountValue ?? draft.totalAmountValue,
      remaining_amount_unit:
        draft.remainingAmountUnit ?? draft.totalAmountUnit,
      serving_size_value: draft.servingSizeValue,
      serving_size_unit: draft.servingSizeUnit,
      estimated_total_servings: draft.totalServings,
      estimated_remaining_servings: draft.remainingTarget ?? draft.totalServings,
      yield_type: draft.yieldType,
    });
  }

  if (draft.quickAction === "finish") {
    return finishCookingBatch(initData, mode, batch.id);
  }
  if (draft.quickAction === "discard") {
    return discardCookingBatch(initData, mode, batch.id);
  }

  const remaining = resolveLeftoversRemainingTarget(draft);
  if (remaining == null) {
    return batch;
  }

  return adjustCookingBatchRemaining(initData, mode, batch.id, {
    remaining_servings: remaining,
    remaining_amount_value: draft.remainingAmountValue,
    remaining_amount_unit: draft.remainingAmountUnit,
    estimated_remaining_servings: remaining,
  });
}
