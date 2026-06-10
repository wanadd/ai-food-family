export type MealCheckinStatus =
  | "ate_home"
  | "ate_work"
  | "ate_cafe"
  | "ate_restaurant"
  | "ate_delivery"
  | "ate_other";

export const MEAL_CHECKIN_OPTIONS: {
  value: MealCheckinStatus;
  label: string;
}[] = [
  { value: "ate_home", label: "Поел дома" },
  { value: "ate_work", label: "На работе" },
  { value: "ate_cafe", label: "В кафе" },
  { value: "ate_restaurant", label: "В ресторане" },
  { value: "ate_delivery", label: "Доставка" },
  { value: "ate_other", label: "Другое" },
];

export const MEAL_TYPE_LABELS: Record<string, string> = {
  breakfast: "Завтрак",
  lunch: "Обед",
  dinner: "Ужин",
  snack: "Перекус",
};

/**
 * Статусы вне MEAL_CHECKIN_OPTIONS: «приготовил» ≠ «съел».
 * cooked / skipped не входят в EATEN_STATUSES на backend — КБЖУ не считаются.
 */
export const MEAL_STATUS_LABELS: Record<string, string> = {
  planned: "В плане",
  cooked: "Приготовлено · съем позже",
  skipped: "Пропущено",
  saved_as_leftover: "Съедено · есть остатки",
  completed: "Съедено",
};

export function mealCheckinStatusLabel(status: string | null): string {
  if (!status) {
    return "В плане";
  }
  return (
    MEAL_STATUS_LABELS[status] ??
    MEAL_CHECKIN_OPTIONS.find((o) => o.value === status)?.label ??
    status
  );
}
