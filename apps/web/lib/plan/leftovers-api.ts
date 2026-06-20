import { apiFetch, apiGet } from "@/lib/api-client";
import type { AppMode } from "@/lib/app-mode/types";

export type StockProduct = {
  id: number;
  title: string;
  quantity: string;
  unit: string;
  category: string;
  source: "inventory";
};

export type PreparedDish = {
  id: number;
  recipe_id: number | null;
  recipe_title: string | null;
  remaining_servings: number;
  total_servings: number;
  serving_unit: string;
  meal_type: string | null;
  planned_date: string | null;
  day_index: number | null;
  menu_selection_id: number | null;
  batch_status: string;
  yield_type?: string | null;
  total_amount_value?: number | null;
  total_amount_unit?: string | null;
  remaining_amount_value?: number | null;
  remaining_amount_unit?: string | null;
  serving_size_value?: number | null;
  serving_size_unit?: string | null;
  source: "cooking_batch";
  can_manage: boolean;
};

export type StocksSummary = {
  products_count: number;
  prepared_dishes_count: number;
  total_positions_count: number;
};

export type StocksOverview = {
  products: StockProduct[];
  prepared_dishes: PreparedDish[];
  summary: StocksSummary;
};

export type CookingBatch = {
  id: number;
  family_id: number | null;
  owner_user_id: number | null;
  recipe_id: number | null;
  recipe_title: string | null;
  menu_selection_id: number | null;
  day_index: number | null;
  planned_date: string | null;
  meal_type: string | null;
  batch_status: string;
  total_servings: number;
  remaining_servings: number;
  serving_unit: string;
  total_amount_value?: number | null;
  total_amount_unit?: string | null;
  remaining_amount_value?: number | null;
  remaining_amount_unit?: string | null;
  serving_size_value?: number | null;
  serving_size_unit?: string | null;
  estimated_total_servings?: number | null;
  estimated_remaining_servings?: number | null;
  yield_type?: string | null;
};

export type BatchLookupParams = {
  recipe_id?: number | null;
  menu_selection_id?: number | null;
  day_index?: number | null;
  meal_type?: string | null;
  planned_date?: string | null;
};

export type PreparedLeftoversSheetDefaults = {
  batch: CookingBatch | null;
  totalServings: number;
  servingUnit: string;
};

/** Map API batch into sheet field defaults (reopen). */
export function mapExistingBatchToSheetDefaults(
  batch: CookingBatch,
): PreparedLeftoversSheetDefaults {
  return {
    batch,
    totalServings: batch.total_servings,
    servingUnit: batch.serving_unit || "порция",
  };
}

/** Defaults when no active batch exists yet. */
export function mapNewDishToSheetDefaults(
  recipeServings?: number | null,
): PreparedLeftoversSheetDefaults {
  const total = recipeServings != null && recipeServings > 0 ? recipeServings : 1;
  return {
    batch: null,
    totalServings: total,
    servingUnit: "порция",
  };
}

/** Preview remaining after optional additional usage input. */
export function previewPreparedRemaining(
  batch: CookingBatch | null,
  totalServings: number,
  usedServings: number | null,
  customUsed: string,
): number {
  if (batch) {
    const additional =
      usedServings ??
      (customUsed ? Number(customUsed.replace(",", ".")) : 0);
    if (Number.isFinite(additional) && additional > 0) {
      return Math.max(0, batch.remaining_servings - additional);
    }
    return batch.remaining_servings;
  }
  const used =
    usedServings ?? (customUsed ? Number(customUsed.replace(",", ".")) : 0);
  return Math.max(0, totalServings - (Number.isFinite(used) ? used : 0));
}

export async function fetchActiveCookingBatch(
  initData: string,
  mode: AppMode,
  params: BatchLookupParams,
): Promise<CookingBatch | null> {
  const qs = new URLSearchParams();
  if (params.recipe_id != null) {
    qs.set("recipe_id", String(params.recipe_id));
  }
  if (params.menu_selection_id != null) {
    qs.set("menu_selection_id", String(params.menu_selection_id));
  }
  if (params.day_index != null) {
    qs.set("day_index", String(params.day_index));
  }
  if (params.meal_type) {
    qs.set("meal_type", params.meal_type);
  }
  if (params.planned_date) {
    qs.set("planned_date", params.planned_date);
  }
  const suffix = qs.toString() ? `?${qs.toString()}` : "";
  const data = await apiGet<CookingBatch[]>(
    initData,
    mode,
    `/leftovers/prepared${suffix}`,
  );
  return data?.[0] ?? null;
}

export async function fetchStocksOverview(
  initData: string,
  mode: AppMode,
  params?: { family_id?: number | null; include_prepared?: boolean },
): Promise<StocksOverview> {
  const qs = new URLSearchParams();
  if (params?.family_id != null) {
    qs.set("family_id", String(params.family_id));
  }
  if (params?.include_prepared === false) {
    qs.set("include_prepared", "false");
  }
  const suffix = qs.toString() ? `?${qs.toString()}` : "";
  const data = await apiGet<StocksOverview>(
    initData,
    mode,
    `/leftovers${suffix}`,
  );
  if (!data) {
    throw new Error("Не удалось загрузить запасы");
  }
  return data;
}

export async function fetchPreparedLeftovers(
  initData: string,
  mode: AppMode,
): Promise<CookingBatch[]> {
  const data = await apiGet<CookingBatch[]>(
    initData,
    mode,
    "/leftovers/prepared",
  );
  return data ?? [];
}

export async function createCookingBatch(
  initData: string,
  mode: AppMode,
  payload: {
    family_id?: number | null;
    recipe_id?: number | null;
    recipe_title: string;
    menu_selection_id?: number | null;
    day_index?: number | null;
    planned_date?: string | null;
    meal_type?: string | null;
    total_servings?: number;
    serving_unit?: string;
    total_amount_value?: number | null;
    total_amount_unit?: string | null;
    remaining_amount_value?: number | null;
    remaining_amount_unit?: string | null;
    serving_size_value?: number | null;
    serving_size_unit?: string | null;
    estimated_total_servings?: number | null;
    estimated_remaining_servings?: number | null;
    yield_type?: string | null;
  },
): Promise<CookingBatch> {
  return apiFetch(initData, mode, "/leftovers/batches", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function recordCookingBatchUsage(
  initData: string,
  mode: AppMode,
  batchId: number,
  payload: { servings_used: number; note?: string | null },
): Promise<CookingBatch> {
  return apiFetch(initData, mode, `/leftovers/batches/${batchId}/use`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function adjustCookingBatchRemaining(
  initData: string,
  mode: AppMode,
  batchId: number,
  payload: {
    remaining_servings: number;
    note?: string | null;
    remaining_amount_value?: number | null;
    remaining_amount_unit?: string | null;
    estimated_remaining_servings?: number | null;
  },
): Promise<CookingBatch> {
  return apiFetch(initData, mode, `/leftovers/batches/${batchId}/adjust`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function finishCookingBatch(
  initData: string,
  mode: AppMode,
  batchId: number,
): Promise<CookingBatch> {
  return apiFetch(initData, mode, `/leftovers/batches/${batchId}/finish`, {
    method: "POST",
    body: JSON.stringify({}),
  });
}

export async function discardCookingBatch(
  initData: string,
  mode: AppMode,
  batchId: number,
): Promise<CookingBatch> {
  return apiFetch(initData, mode, `/leftovers/batches/${batchId}/discard`, {
    method: "POST",
    body: JSON.stringify({}),
  });
}

import { formatPreparedAmount } from "@/lib/plan/yield-format";

/** «осталось 2 из 4 порций» / «2 л из 5 л» */
export function formatPreparedLeftoverAmount(
  remaining: number,
  total: number,
  unit: string,
  physical?: {
    remaining_amount_value?: number | null;
    remaining_amount_unit?: string | null;
    total_amount_value?: number | null;
    total_amount_unit?: string | null;
  },
): string {
  return formatPreparedAmount({
    remaining,
    total,
    unit,
    remainingAmount:
      physical?.remaining_amount_value != null && physical.remaining_amount_unit
        ? {
            value: physical.remaining_amount_value,
            unit: physical.remaining_amount_unit,
          }
        : null,
    totalAmount:
      physical?.total_amount_value != null && physical.total_amount_unit
        ? { value: physical.total_amount_value, unit: physical.total_amount_unit }
        : null,
  });
}

export function formatStocksSummaryLabel(summary: StocksSummary): string {
  const { products_count, prepared_dishes_count } = summary;
  if (products_count <= 0 && prepared_dishes_count <= 0) {
    return "Пока пусто";
  }
  const parts: string[] = [];
  if (products_count > 0) {
    parts.push(`${products_count} ${productsLabel(products_count)}`);
  }
  if (prepared_dishes_count > 0) {
    parts.push(`${prepared_dishes_count} ${dishesLabel(prepared_dishes_count)}`);
  }
  return parts.join(" · ");
}

function productsLabel(count: number): string {
  const mod10 = count % 10;
  const mod100 = count % 100;
  if (mod10 === 1 && mod100 !== 11) return "продукт";
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 10 || mod100 >= 20)) {
    return "продукта";
  }
  return "продуктов";
}

function dishesLabel(count: number): string {
  const mod10 = count % 10;
  const mod100 = count % 100;
  if (mod10 === 1 && mod100 !== 11) return "готовое блюдо";
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 10 || mod100 >= 20)) {
    return "готовых блюда";
  }
  return "готовых блюд";
}
