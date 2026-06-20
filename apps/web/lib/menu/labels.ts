import type { MealType, MenuVariantType } from "./types";

export const VARIANT_LABELS: Record<
  MenuVariantType,
  { label: string; emoji: string; accent: string }
> = {
  quick: {
    label: "Быстрое",
    emoji: "⚡",
    accent: "from-warm to-orange-400",
  },
  economy: {
    label: "Экономное",
    emoji: "💰",
    accent: "from-sage-500 to-sage-700",
  },
  balanced: {
    label: "Сбалансированное",
    emoji: "🥗",
    accent: "from-olive-500 to-sage-600",
  },
};

export const MEAL_LABELS: Record<MealType, string> = {
  breakfast: "Завтрак",
  lunch: "Обед",
  dinner: "Ужин",
  snack: "Перекус",
};
