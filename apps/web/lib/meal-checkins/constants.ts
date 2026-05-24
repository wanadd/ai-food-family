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
