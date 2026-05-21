import type { MealType, MenuVariantType } from "./types";

export const VARIANT_LABELS: Record<
  MenuVariantType,
  { label: string; emoji: string; accent: string }
> = {
  quick: {
    label: "Быстрое",
    emoji: "⚡",
    accent: "from-amber-400 to-orange-500",
  },
  economy: {
    label: "Экономное",
    emoji: "💰",
    accent: "from-emerald-400 to-teal-500",
  },
  balanced: {
    label: "Сбалансированное",
    emoji: "🥗",
    accent: "from-violet-400 to-indigo-500",
  },
};

export const MEAL_LABELS: Record<MealType, string> = {
  breakfast: "Завтрак",
  lunch: "Обед",
  dinner: "Ужин",
  snack: "Перекус",
};
