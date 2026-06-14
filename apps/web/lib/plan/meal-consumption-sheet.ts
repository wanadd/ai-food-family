export const MENU_TODAY_MARK_CONSUMPTION_BUTTON = "Отметить съеденное";

export const MEAL_CONSUMPTION_SHEET_TITLE = "Что вы съели?";
export const MEAL_CONSUMPTION_SHEET_SUBTITLE =
  "Отметьте блюда и порции для себя или членов семьи";

export const MEAL_CONSUMPTION_MEMBER_PROMPT = "Кого отмечаем?";

export const MEAL_CONSUMPTION_SAVE_DISABLED_HINT =
  "Сохранение будет доступно после настройки семейного учёта";

/** Must not appear in the consumption marking sheet. */
export const MEAL_CONSUMPTION_FORBIDDEN_PHRASES = [
  "Итог дня",
  "Результат дня",
  "Что приготовили?",
  "План на день и КБЖУ",
  "Показать итог дня",
] as const;

export const MEAL_CONSUMPTION_PORTION_OPTIONS = [0.5, 1, 1.5, 2] as const;

export type MealConsumptionStatus = "eaten" | "skipped" | "ate_out";

export const MEAL_CONSUMPTION_STATUS_OPTIONS: ReadonlyArray<{
  id: MealConsumptionStatus;
  label: string;
}> = [
  { id: "eaten", label: "Съел" },
  { id: "skipped", label: "Не ел" },
  { id: "ate_out", label: "Ел вне дома" },
];

export type ConsumptionTargetId = "self" | "family" | number;

export function formatConsumptionPortion(value: number): string {
  if (value === 0.5) {
    return "½";
  }
  return String(value);
}
