import type { SelectOption } from "@/lib/onboarding/options";

export const GENDER_OPTIONS: SelectOption[] = [
  { value: "female", label: "Женский" },
  { value: "male", label: "Мужской" },
  { value: "other", label: "Другой" },
  { value: "prefer_not", label: "Не указывать" },
];

export const NUTRITION_GOAL_OPTIONS: SelectOption[] = [
  { value: "maintain", label: "Поддержание веса" },
  { value: "lose", label: "Похудение" },
  { value: "gain", label: "Набор массы" },
  { value: "healthy", label: "Здоровое питание" },
  { value: "sport", label: "Спортивный режим" },
];

export const ACTIVITY_OPTIONS: SelectOption[] = [
  { value: "low", label: "Низкая", hint: "Сидячий образ жизни" },
  { value: "medium", label: "Средняя", hint: "Прогулки, быт" },
  { value: "high", label: "Высокая", hint: "Много движения" },
  { value: "training", label: "Тренировки", hint: "Спорт 3+ раза в неделю" },
];

export const DISH_COMPLEXITY_OPTIONS: SelectOption[] = [
  { value: "simple", label: "Простые", hint: "До 5 ингредиентов" },
  { value: "medium", label: "Средние" },
  { value: "advanced", label: "Сложные", hint: "Готовлю с удовольствием" },
];

export const WORKOUT_FREQUENCY_OPTIONS: SelectOption[] = [
  { value: "1-2", label: "1–2 раза в неделю" },
  { value: "3-4", label: "3–4 раза" },
  { value: "5+", label: "5 и чаще" },
];

export {
  ALLERGY_OPTIONS,
  BUDGET_OPTIONS,
  COOKING_TIME_OPTIONS,
  DIET_OPTIONS,
  RESTRICTION_OPTIONS,
} from "@/lib/onboarding/options";

export const NUTRITION_GOAL_LABELS: Record<string, string> = Object.fromEntries(
  NUTRITION_GOAL_OPTIONS.map((o) => [o.value, o.label]),
);
