import type {
  NutritionConfidence,
  NutritionSummary,
  RecipeSummary,
} from "./types";

/**
 * Soft KБЖУ presentation helpers. The PLANAM principle: show confident numbers
 * confidently, approximate numbers as "примерно" (≈), and never invent values
 * when data is missing.
 */

export type KcalBadge = {
  /** e.g. "320 ккал" or "≈320 ккал" */
  text: string;
  /** true => render an "примерно" hint */
  approximate: boolean;
};

function round(value: number | null | undefined): number | null {
  if (value == null || Number.isNaN(value)) {
    return null;
  }
  return Math.round(value);
}

/**
 * Per-serving kcal for a recipe card. Prefers the calculated nutrition_summary,
 * falling back to the legacy calories_per_serving field. Returns null when
 * nothing usable is available (unavailable / missing).
 */
export function cardKcalBadge(recipe: RecipeSummary): KcalBadge | null {
  const summary = recipe.nutrition_summary;
  if (summary && summary.confidence && summary.confidence !== "unavailable") {
    const kcal = round(summary.kcal_per_serving);
    if (kcal != null) {
      const approximate = summary.confidence === "low_confidence";
      return { text: `${approximate ? "≈" : ""}${kcal} ккал`, approximate };
    }
  }
  // Legacy fallback (older recipes without a calculated summary).
  const legacy = round(recipe.calories_per_serving);
  if (legacy != null) {
    return { text: `${legacy} ккал`, approximate: false };
  }
  return null;
}

export type MacroValue = { label: string; value: string };

export function perServingMacros(summary: NutritionSummary): MacroValue[] {
  const p = round(summary.protein_per_serving);
  const f = round(summary.fat_per_serving);
  const c = round(summary.carbs_per_serving);
  const kcal = round(summary.kcal_per_serving);
  return [
    { label: "Калории", value: kcal != null ? `${kcal}` : "—" },
    { label: "Белки", value: p != null ? `${p} г` : "—" },
    { label: "Жиры", value: f != null ? `${f} г` : "—" },
    { label: "Углеводы", value: c != null ? `${c} г` : "—" },
  ];
}

export function totalMacrosLine(summary: NutritionSummary): string | null {
  const kcal = round(summary.kcal_total);
  if (kcal == null) {
    return null;
  }
  const p = round(summary.protein_total);
  const f = round(summary.fat_total);
  const c = round(summary.carbs_total);
  const parts = [`${kcal} ккал`];
  if (p != null) parts.push(`Б ${p}`);
  if (f != null) parts.push(`Ж ${f}`);
  if (c != null) parts.push(`У ${c}`);
  return parts.join(" · ");
}

export function confidenceNote(
  confidence: NutritionConfidence | null | undefined,
): string | null {
  switch (confidence) {
    case "low_confidence":
      return "Расчёт примерный: часть ингредиентов указана «по вкусу» или требует уточнения.";
    case "unavailable":
      return "КБЖУ пока нельзя посчитать точно — нужно уточнить ингредиенты.";
    default:
      return null;
  }
}
