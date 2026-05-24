export type RecipeFitLevel = "good" | "partial" | "not_recommended";

export const FIT_BADGE_LABELS: Record<RecipeFitLevel, string> = {
  good: "Подходит",
  partial: "Подходит частично",
  not_recommended: "Не рекомендуется",
};

export const FIT_BADGE_STYLES: Record<RecipeFitLevel, string> = {
  good: "bg-emerald-100 text-emerald-900",
  partial: "bg-amber-100 text-amber-950",
  not_recommended: "bg-stone-200 text-stone-700",
};
