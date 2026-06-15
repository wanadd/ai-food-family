export type YieldType = "servings" | "volume" | "weight" | "count";

export type PhysicalAmount = {
  value: number;
  unit: string;
};

function fmtNum(n: number): string {
  return Number.isInteger(n) ? String(n) : n.toFixed(1).replace(".", ",");
}

/** «осталось 2 л из 5 л» / «4 из 12 шт» / «2 из 4 порций» */
export function formatPreparedAmount(params: {
  remaining: number;
  total: number;
  unit: string;
  remainingAmount?: PhysicalAmount | null;
  totalAmount?: PhysicalAmount | null;
}): string {
  if (
    params.remainingAmount?.unit &&
    params.totalAmount?.unit &&
    params.remainingAmount.unit === params.totalAmount.unit
  ) {
    return `осталось ${fmtNum(params.remainingAmount.value)} из ${fmtNum(params.totalAmount.value)} ${params.totalAmount.unit}`;
  }
  const unit = params.unit;
  if (unit === "порция" || unit === "порции" || unit === "порций") {
    return `осталось ${fmtNum(params.remaining)} из ${fmtNum(params.total)} порций`;
  }
  return `осталось ${fmtNum(params.remaining)} из ${fmtNum(params.total)} ${unit}`;
}

export function formatPlannedYieldLine(params: {
  planned_yield_amount?: number | null;
  planned_yield_unit?: string | null;
  planned_serving_size_amount?: number | null;
  planned_serving_size_unit?: string | null;
  expected_leftover_amount?: number | null;
  expected_leftover_unit?: string | null;
  servings?: number | null;
}): string | null {
  const amount = params.planned_yield_amount ?? params.servings;
  const unit = params.planned_yield_unit ?? (params.servings ? "порция" : null);
  if (amount == null || !unit) {
    return null;
  }
  const cook = `Готовить: ${fmtNum(amount)} ${unit}`;
  const portion =
    params.planned_serving_size_amount != null && params.planned_serving_size_unit
      ? ` · порция ${fmtNum(params.planned_serving_size_amount)} ${params.planned_serving_size_unit}`
      : "";
  const leftover =
    params.expected_leftover_amount != null && params.expected_leftover_unit
      ? ` · останется ~${fmtNum(params.expected_leftover_amount)} ${params.expected_leftover_unit}`
      : "";
  return `${cook}${portion}${leftover}`;
}
