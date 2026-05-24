import { NUTRITION_GOAL_LABELS } from "@/lib/nutrition-profile/options";

export type PlanModeId =
  | "quick_simple"
  | "economy"
  | "healthy"
  | "sport"
  | "family"
  | "use_pantry";

export type MenuGoalId =
  | "maintain"
  | "lose"
  | "gain"
  | "healthy"
  | "sport"
  | "kids";

export const MENU_GOAL_OPTIONS: { value: MenuGoalId; label: string }[] = [
  { value: "lose", label: "Похудение" },
  { value: "maintain", label: NUTRITION_GOAL_LABELS.maintain ?? "Поддержание веса" },
  { value: "gain", label: "Набор массы" },
  { value: "sport", label: "Спорт" },
  { value: "kids", label: "Семейное питание" },
  { value: "healthy", label: "Пост / лечебное питание" },
];

export const MENU_DAY_OPTIONS = [1, 3, 5, 7, 14, 30] as const;

export type MenuDayCount = (typeof MENU_DAY_OPTIONS)[number];

export const MENU_BUDGET_OPTIONS = [
  { value: "economy", label: "Экономно" },
  { value: "standard", label: "Стандарт" },
  { value: "premium", label: "Без ограничений" },
] as const;

export const PLAN_MODE_OPTIONS: {
  value: PlanModeId;
  label: string;
  hint: string;
}[] = [
  {
    value: "quick_simple",
    label: "Быстро и просто",
    hint: "Минимум времени у плиты",
  },
  {
    value: "economy",
    label: "Экономно",
    hint: "Недорогие продукты",
  },
  {
    value: "healthy",
    label: "Полезно",
    hint: "Сбалансированный рацион",
  },
  {
    value: "sport",
    label: "Спорт",
    hint: "Больше белка и энергии",
  },
  {
    value: "family",
    label: "Семейное",
    hint: "Удобно для всех дома",
  },
  {
    value: "use_pantry",
    label: "Использовать запасы",
    hint: "Сначала то, что есть дома",
  },
];

export const PLAN_MODE_HINTS: Record<PlanModeId, string> = {
  quick_simple:
    "Сделай акцент на быстром и простом меню (вариант quick): короткая готовка, простые блюда.",
  economy:
    "Сделай акцент на экономном меню (вариант economy): бюджетные продукты, без лишних трат.",
  healthy:
    "Сделай акцент на полезном сбалансированном меню (вариант balanced).",
  sport:
    "Учти спортивный режим: достаточно белка, энергии, сбалансированные БЖУ.",
  family:
    "Учти семейный формат: блюда, которые удобно готовить на нескольких человек.",
  use_pantry:
    "Максимально используй остатки и запасы из холодильника, минимизируй покупки.",
};

export const CHECKLIST_ITEMS = [
  { id: "profile", label: "Профиль питания" },
  { id: "persons", label: "Количество персон" },
  { id: "pantry", label: "Запасы" },
  { id: "leftovers", label: "Остатки блюд" },
  { id: "allergies", label: "Аллергии" },
  { id: "budget", label: "Бюджет" },
  { id: "cooking_time", label: "Время на готовку" },
] as const;
